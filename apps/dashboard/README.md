# autoux dashboard

Next.js 16 (app router) live rollout dashboard for UserSim.

## prerequisites

- Node.js 18+
- The FastAPI backend running on port 8766:
  ```
  cd /path/to/cua-hackathon
  uvicorn usersim.web.server:app --port 8766 --reload
  ```

## run

```bash
cp .env.local.example .env.local   # only needed if API runs elsewhere
npm install
npm run dev
```

Open http://localhost:3000.

## env

| var | default | description |
|-----|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | `http://127.0.0.1:8766` | Base URL of the FastAPI backend |

## build

```bash
npm run build
npm start
```

## stubbed / not-yet-implemented endpoints

The dashboard gracefully falls back when these backend endpoints don't exist:

- `GET /api/configs` — falls back to hardcoded `configs/taxcaster.yaml` options
- `GET /api/agents` — falls back to `["northstar"]`
- `POST /api/run` — wired up; will error visibly in the modal if backend returns non-2xx
