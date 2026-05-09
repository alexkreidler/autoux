"""Deploy backends — make a committed patch "live" in an isolated dev namespace.

Production namespaces are NEVER touched. Patched images go to dev-<app>
namespaces with full metadata (version, SHA, agent). Promotion to production
is a separate, explicit step.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel

from coder.base import CodingPatch


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

class DeployResult(BaseModel):
    success: bool
    image_tag: str | None = None
    service_url: str | None = None
    duration_ms: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class DeployBackend(Protocol):
    async def deploy(self, repo_dir: Path, patch: CodingPatch, iteration: int) -> DeployResult:
        """Deploy the patched image to an isolated dev environment."""
        ...

    async def teardown(self) -> None:
        """Clean up dev resources. No-op for local."""
        ...


# ---------------------------------------------------------------------------
# Config models (parsed from the `deploy` key in YAML)
# ---------------------------------------------------------------------------

class LocalDeployConfig(BaseModel):
    mode: Literal["local"] = "local"
    restart_command: str | None = None


class K8sDeployConfig(BaseModel):
    mode: Literal["k8s"] = "k8s"
    app_name: str
    dockerfile: str = "Dockerfile"
    depot_project: str = "cdgf48zlw0"
    registry: str = ""  # empty = use Depot's built-in registry
    # Production reference (read-only — we copy from here, never modify)
    prod_namespace: str = ""  # defaults to app_name
    prod_deployment: str = ""  # defaults to app_name
    container: str = ""  # defaults to app_name
    service_port: int = 80
    rollout_timeout_s: int = 180
    build_args: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

class LocalBackend:
    def __init__(self, config: LocalDeployConfig | None = None) -> None:
        self._restart_cmd = config.restart_command if config else None

    async def deploy(self, repo_dir: Path, patch: CodingPatch, iteration: int) -> DeployResult:
        if not self._restart_cmd:
            return DeployResult(success=True)
        started = time.monotonic()
        proc = await asyncio.create_subprocess_shell(
            self._restart_cmd, cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        ms = int((time.monotonic() - started) * 1000)
        return DeployResult(
            success=proc.returncode == 0, duration_ms=ms,
            error=out.decode(errors="replace") if proc.returncode != 0 else None,
        )

    async def teardown(self) -> None:
        pass


class K8sBackend:
    """Deploys patched images to isolated dev-<app> namespaces.

    Never modifies production. Each deploy:
    1. Builds image with Depot → saves to Depot registry
    2. Creates/updates a dev namespace with full deployment + service
    3. Tags everything with version, SHA, and agent metadata
    """

    def __init__(self, config: K8sDeployConfig) -> None:
        self._c = config
        self._app = config.app_name
        self._container = config.container or config.app_name
        self._prod_ns = config.prod_namespace or config.app_name
        self._prod_deploy = config.prod_deployment or config.app_name
        self._dev_ns = f"dev-{config.app_name}"

    async def deploy(self, repo_dir: Path, patch: CodingPatch, iteration: int) -> DeployResult:
        started = time.monotonic()

        # --- Resolve version + SHA ---
        version = f"v{iteration}"
        sha = patch.commit_sha
        if not sha:
            sha = (await _run_cmd(
                ["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir,
            )).strip()
        agent = "claude-cli"
        local_tag = f"{self._app}-dev:{version}"

        # --- 1. Depot build + push in one step ---
        registry = self._c.registry or "ghcr.io/alexkreidler"
        image = f"{registry}/{self._app}-dev:{version}"
        build_cmd = [
            "depot", "build",
            "--project", self._c.depot_project,
            "--platform", "linux/amd64",
            "-f", self._c.dockerfile,
            "-t", image,
            "--push",
            ".",
        ]
        for k, v in self._c.build_args.items():
            build_cmd.extend(["--build-arg", f"{k}={v}"])

        print(f"  [deploy] depot build --push -t {image}")
        ok, err = await _run_check(build_cmd, cwd=repo_dir)
        if not ok:
            return DeployResult(
                success=False,
                error=f"depot build+push failed: {err}",
                duration_ms=_elapsed(started),
            )

        # --- 3. Create dev namespace + depot-pull secret ---
        await _run_check([
            "kubectl", "create", "namespace", self._dev_ns,
            "--dry-run=client", "-o", "yaml",
        ])
        await _run_check_stdin(
            ["kubectl", "apply", "-f", "-"],
            stdin=f"apiVersion: v1\nkind: Namespace\nmetadata:\n  name: {self._dev_ns}\n  labels:\n    usersim.dev/managed-by: usersim-loop\n",
        )
        await _ensure_ghcr_pull_secret(self._dev_ns)

        # --- 4. Apply dev deployment + service ---
        metadata_labels = {
            "app": self._app,
            "usersim.dev/version": version,
            "usersim.dev/commit-sha": sha,
            "usersim.dev/agent": agent,
            "usersim.dev/managed-by": "usersim-loop",
        }
        metadata_annotations = {
            "usersim.dev/iteration": str(iteration),
            "usersim.dev/files-changed": json.dumps(patch.files_changed[:10]),
            "usersim.dev/source-repo": str(repo_dir),
        }

        manifest = _render_dev_manifest(
            namespace=self._dev_ns,
            app_name=self._app,
            container_name=self._container,
            image=image,
            port=self._c.service_port,
            labels=metadata_labels,
            annotations=metadata_annotations,
        )

        print(f"  [deploy] applying to namespace {self._dev_ns} (production {self._prod_ns} untouched)")
        ok, err = await _run_check_stdin(
            ["kubectl", "apply", "-f", "-"],
            stdin=manifest,
        )
        if not ok:
            return DeployResult(
                success=False, image_tag=image,
                error=f"kubectl apply failed: {err}",
                duration_ms=_elapsed(started),
            )

        # --- 5. Wait for rollout ---
        print(f"  [deploy] waiting for rollout (timeout={self._c.rollout_timeout_s}s)")
        ok, err = await _run_check([
            "kubectl", "rollout", "status",
            f"deployment/{self._app}",
            "-n", self._dev_ns,
            f"--timeout={self._c.rollout_timeout_s}s",
        ])
        if not ok:
            return DeployResult(
                success=False, image_tag=image,
                error=f"rollout failed: {err}",
                duration_ms=_elapsed(started),
            )

        service_url = f"http://{self._app}.{self._dev_ns}.svc.cluster.local:{self._c.service_port}"
        print(f"  [deploy] live at {service_url}")
        return DeployResult(
            success=True,
            image_tag=image,
            service_url=service_url,
            duration_ms=_elapsed(started),
        )

    async def teardown(self) -> None:
        await _run_check([
            "kubectl", "delete", "namespace", self._dev_ns,
            "--ignore-not-found",
        ])


# ---------------------------------------------------------------------------
# Manifest renderer
# ---------------------------------------------------------------------------

def _render_dev_manifest(
    *,
    namespace: str,
    app_name: str,
    container_name: str,
    image: str,
    port: int,
    labels: dict[str, str],
    annotations: dict[str, str],
) -> str:
    """Render a minimal Namespace + Deployment + Service YAML for the dev env."""
    import yaml as _yaml

    def _labels(d: dict[str, str]) -> dict[str, str]:
        # K8s label values must be ≤63 chars, alphanumeric/dash/dot/underscore
        return {k: v for k, v in d.items() if len(v) <= 63}

    ns = {
        "apiVersion": "v1", "kind": "Namespace",
        "metadata": {"name": namespace, "labels": {"usersim.dev/managed-by": "usersim-loop"}},
    }
    deploy = {
        "apiVersion": "apps/v1", "kind": "Deployment",
        "metadata": {
            "name": app_name, "namespace": namespace,
            "labels": _labels(labels), "annotations": annotations,
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": app_name}},
            "template": {
                "metadata": {"labels": _labels(labels)},
                "spec": {
                    "imagePullSecrets": [{"name": "ghcr-pull"}],
                    "containers": [{
                        "name": container_name,
                        "image": image,
                        "ports": [{"containerPort": port}],
                        "resources": {
                            "requests": {"memory": "128Mi", "cpu": "100m"},
                            "limits": {"memory": "512Mi"},
                        },
                    }],
                },
            },
        },
    }
    svc = {
        "apiVersion": "v1", "kind": "Service",
        "metadata": {"name": app_name, "namespace": namespace, "labels": _labels(labels)},
        "spec": {
            "selector": {"app": app_name},
            "ports": [{"port": port, "targetPort": port}],
        },
    }
    return "---\n".join(_yaml.dump(doc, default_flow_style=False) for doc in [ns, deploy, svc])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _ensure_ghcr_pull_secret(namespace: str) -> None:
    """Create a GHCR imagePullSecret in a namespace if it doesn't exist.

    Uses `gh auth token` for credentials. For public GHCR packages this
    secret isn't strictly required, but we create it defensively.
    """
    ok, _ = await _run_check([
        "kubectl", "get", "secret", "ghcr-pull", "-n", namespace,
    ])
    if ok:
        return

    token = (await _run_cmd(["gh", "auth", "token"])).strip()
    if not token:
        print(f"  [deploy] WARNING: could not get gh auth token; skipping pull secret")
        return

    await _run_check([
        "kubectl", "create", "secret", "docker-registry", "ghcr-pull",
        "--docker-server=ghcr.io",
        "--docker-username=alexkreidler",
        f"--docker-password={token}",
        "-n", namespace,
    ])
    print(f"  [deploy] created ghcr-pull secret in {namespace}")


def _elapsed(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


async def _run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    return out.decode(errors="replace")


async def _run_check(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode == 0, out.decode(errors="replace")


async def _run_check_stdin(cmd: list[str], stdin: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate(input=stdin.encode())
    return proc.returncode == 0, out.decode(errors="replace")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_backend(spec: dict | None) -> DeployBackend:
    """Build a DeployBackend from a config dict (the 'deploy' key in YAML)."""
    if spec is None:
        return LocalBackend()
    mode = spec.get("mode", "local")
    if mode == "local":
        return LocalBackend(LocalDeployConfig(**spec))
    if mode == "k8s":
        return K8sBackend(K8sDeployConfig(**spec))
    raise ValueError(f"unknown deploy mode: {mode!r}")
