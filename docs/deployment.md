# Google Cloud deployment

This project can be evaluated locally without cloud credentials. A hosted demo
requires a Google Cloud project with billing configured; do not run these steps
unless the account holder has approved the exact spend.

## Prerequisites

1. Python 3.11 or newer.
2. Google Cloud CLI authenticated to the intended project.
3. The Google ADK CLI installed from `proofline/requirements.txt`.
4. Vertex AI, Cloud Run, Firestore, and Pub/Sub APIs enabled in that project.

## Local ADK session

From the repository root:

```bash
python -m venv .venv
python -m pip install -r proofline/requirements.txt
adk web
```

Set `GEMINI_MODEL` only when a different eligible Gemini model is required. The
default is `gemini-3.6-flash`.

## Cloud Run

After replacing the placeholders with the holder-approved project and region:

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
