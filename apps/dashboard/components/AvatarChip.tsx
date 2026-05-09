"use client";

import { useState } from "react";
import { apiUrl } from "@/lib/api";
import { initials, colorIndex } from "@/lib/utils";

const FALLBACK_COLORS = [
  "bg-olive",
  "bg-sage",
  "bg-clay",
  "bg-rust",
  "bg-amber",
] as const;

interface Props {
  personaId: string;
  size?: number; // px
}

export default function AvatarChip({ personaId, size = 36 }: Props) {
  const [failed, setFailed] = useState(false);
  const ci = colorIndex(personaId);
  const bg = FALLBACK_COLORS[ci];

  return (
    <span
      className={`inline-flex items-center justify-center flex-shrink-0 overflow-hidden ${bg}`}
      style={{ width: size, height: size }}
    >
      {!failed ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={apiUrl(`/api/avatar/${encodeURIComponent(personaId)}.png`)}
          alt=""
          className="w-full h-full object-cover block"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="text-white font-semibold" style={{ fontSize: size * 0.33 }}>
          {initials(personaId)}
        </span>
      )}
    </span>
  );
}
