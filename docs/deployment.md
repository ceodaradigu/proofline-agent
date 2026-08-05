# Google Cloud deployment

This project can be evaluated locally without cloud credentials. A hosted demo
requires a Google Cloud project with billing configured; do not run these steps
unless the account holder has approved the exact spend.

## Prerequisites

1. Python 3.11 or newer.
2. Google Cloud CLI authenticated to the intended project.
3. The Google ADK CLI installed from `proofline/requirements.txt`.
4. Vertex AI, Cloud Run, Firestore, and Pub/Sub APIs enabled in that project.

The repository includes `agents-cli-manifest.yaml`, which identifies
`proofline/` as the agent directory and Cloud Run as the intended deployment
target. The exported `app` name matches that directory, as required by the
current ADK application layout.

## Local ADK session

From the repository root:

```bash
python -m venv .venv
python -m pip install -r proofline/requirements.txt
adk web
```

Set `GEMINI_MODEL` only when a different eligible Gemini model is required. The
default is `gemini-3.6-flash`.

## Credential-free API preflight

The application can be loaded and its API contract inspected without invoking
Gemini or creating cloud resources:

```bash
adk api_server \
  --host 127.0.0.1 \
  --port 8765 \
  --session_service_uri memory:// \
  --artifact_service_uri memory:// \
  --memory_service_uri memory:// \
  proofline
```

Then request `/health`, `/list-apps`, `/apps/proofline/app-info`, and
`/openapi.json`. The measured 2026-08-05 result is recorded in
[`local-api-evidence.md`](local-api-evidence.md). This check validates ADK
discovery and the HTTP surface, not model credentials or cloud deployment.

## Cloud Run

The repository root contains a production-shaped `Dockerfile`. It launches the
ADK API server on Cloud Run's runtime-provided `PORT`, copies only the agent
package into the image, and excludes local credentials, test artifacts, and
video assets from the build context.

After replacing the placeholders with the holder-approved project and region,
the container can be built and deployed directly from source:

```bash
gcloud run deploy proofline \
  --source=. \
  --project=YOUR_PROJECT_ID \
  --region=YOUR_REGION \
  --allow-unauthenticated \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=global
```

Alternatively, ADK's deployment command remains available:

```bash
adk deploy cloud_run \
  --project=YOUR_PROJECT_ID \
  --region=YOUR_REGION \
  proofline
```

The deployment folder includes `agent.py`, `root_agent`, `__init__.py`, and
`requirements.txt`, matching ADK discovery requirements. Firestore and Pub/Sub
are architectural integration points for the hosted version; the current local
demo does not create billable resources or claim they are already provisioned.

After deployment, verify the public surface before recording demo evidence:

```bash
curl -fsS "https://YOUR_SERVICE_URL/health"
curl -fsS "https://YOUR_SERVICE_URL/list-apps"
curl -fsS "https://YOUR_SERVICE_URL/apps/proofline/app-info"
```

The final demo must show the real `.run.app` URL and a corresponding Cloud Run
log entry. The checks succeeded on 2026-08-05; the final demo script now uses
only the recorded public-safe results and does not claim the planned Firestore
or Pub/Sub extensions are active.
