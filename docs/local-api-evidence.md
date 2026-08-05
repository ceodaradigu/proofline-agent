# Local Google ADK API evidence

Checked on 2026-08-05 with Google ADK CLI 2.6.2, Python 3.11, and no cloud
credentials. This proves the repository is discoverable as a real ADK
application; it does **not** claim a Google Cloud deployment or a live Gemini
generation.

## Start the server

From the repository root:

```bash
adk api_server \
  --host 127.0.0.1 \
  --port 8765 \
  --session_service_uri memory:// \
  --artifact_service_uri memory:// \
  --memory_service_uri memory:// \
  proofline
```

The three explicit in-memory services keep this verification credential-free
and prevent local session or artifact persistence.

## Reproduce the checks

```bash
curl -i http://127.0.0.1:8765/health
curl -i http://127.0.0.1:8765/list-apps
curl -i http://127.0.0.1:8765/apps/proofline/app-info
curl -s http://127.0.0.1:8765/openapi.json
```

## Measured result

| Endpoint | HTTP | Evidence |
| --- | ---: | --- |
| `/health` | 200 | `{"status":"ok"}` |
| `/list-apps` | 200 | `["proofline"]` |
| `/apps/proofline/app-info` | 200 | App and root agent are both named `proofline`; language is Python; the `evaluate_packet` function declaration is present. |
| `/openapi.json` | 200 | FastAPI 0.1.0 document with 16 routes, including session, artifact, `/run`, and `/run_sse` surfaces. |

The server was stopped after the checks. Calling `/run` was intentionally out
of scope for this credential-free preflight because it would invoke the Gemini
model. A hosted-demo claim must include a real Cloud Run URL and its associated
Google Cloud evidence.
