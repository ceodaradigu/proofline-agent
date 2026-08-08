"""Public Cloud Run entry point for the Proofline ADK application."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app

ROOT = Path(__file__).resolve().parent
DEFAULT_AGENTS_DIR = (
    ROOT / "agents" if (ROOT / "agents").is_dir() else ROOT / "proofline"
)
AGENTS_DIR = os.getenv("PROOFLINE_AGENTS_DIR", str(DEFAULT_AGENTS_DIR))

app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    session_service_uri="memory://",
    artifact_service_uri="memory://",
    memory_service_uri="memory://",
    use_local_storage=False,
    web=False,
)


LANDING_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Proofline — Evidence before action</title>
  <meta name="description" content="A verification-first Google ADK agent that turns task claims into tamper-evident proof packets.">
  <style>
    :root { color-scheme: dark; --ink:#f7f8fb; --muted:#aab4c8; --line:#26334c; --blue:#6ee7ff; --gold:#ffd780; --bg:#07101f; --panel:#0d1930; }
    * { box-sizing: border-box; }
    body { margin:0; color:var(--ink); background:radial-gradient(circle at 75% 0%,#183769 0,transparent 34rem),var(--bg); font:16px/1.6 Inter,ui-sans-serif,system-ui,sans-serif; }
    main { width:min(1080px,calc(100% - 32px)); margin:auto; padding:72px 0 48px; }
    .eyebrow,.disclosure { display:inline-flex; border:1px solid #38527c; border-radius:999px; padding:7px 12px; color:var(--blue); background:#0b1a32cc; font-size:13px; letter-spacing:.04em; }
    h1 { max-width:820px; margin:22px 0 16px; font-size:clamp(42px,8vw,86px); line-height:.95; letter-spacing:-.055em; }
    h1 span { color:var(--blue); }
    .lead { max-width:760px; color:#d1d8e6; font-size:clamp(18px,2.5vw,24px); }
    .actions { display:flex; flex-wrap:wrap; gap:12px; margin:30px 0 52px; }
    a.button { color:#07101f; background:var(--blue); border-radius:10px; padding:12px 17px; font-weight:750; text-decoration:none; }
    a.button.secondary { color:var(--ink); background:transparent; border:1px solid #526483; }
    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
    .card { min-height:180px; padding:22px; border:1px solid var(--line); border-radius:16px; background:linear-gradient(145deg,#13233eaa,#0a1427ee); }
    .card b { display:block; margin-bottom:10px; color:var(--gold); font-size:14px; letter-spacing:.04em; }
    .card p { color:var(--muted); margin:0; }
    section { margin:54px 0; }
    section h2 { margin:0 0 16px; font-size:clamp(27px,4vw,42px); letter-spacing:-.035em; }
    .proof { display:grid; grid-template-columns:1.3fr .7fr; gap:20px; padding:28px; border:1px solid var(--line); border-radius:18px; background:var(--panel); }
    code { color:var(--blue); overflow-wrap:anywhere; }
    .proof p,.claim { color:var(--muted); }
    .links { display:flex; flex-wrap:wrap; gap:18px; }
    .links a { color:var(--blue); }
    footer { display:flex; flex-wrap:wrap; justify-content:space-between; gap:16px; padding-top:28px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; }
    @media (max-width:800px) { .grid { grid-template-columns:1fr 1fr; } .proof { grid-template-columns:1fr; } }
    @media (max-width:520px) { main { padding-top:38px; } .grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <main>
    <span class="eyebrow">Google ADK · Gemini 3.6 Flash · Cloud Run</span>
    <h1>Evidence before <span>action.</span></h1>
    <p class="lead">Proofline converts a work contract into explicit requirements, tests fresh authoritative evidence, detects contradictions, and produces a deterministic proof packet before any external action can proceed.</p>
    <div class="actions">
      <a class="button" href="/apps/proofline/app-info">Inspect the live ADK agent</a>
      <a class="button secondary" href="https://youtu.be/khPpdq7GcTk">Watch the 2:53 demo</a>
    </div>

    <div class="grid" aria-label="Proofline decision states">
      <article class="card"><b>01 · NEEDS_EVIDENCE</b><p>A requirement is missing a fresh, authoritative source.</p></article>
      <article class="card"><b>02 · CONFLICT</b><p>Evidence disagrees, so the agent refuses to hide uncertainty.</p></article>
      <article class="card"><b>03 · APPROVAL_REQUIRED</b><p>The packet passes, but an external action still needs human approval.</p></article>
      <article class="card"><b>04 · READY</b><p>Every requirement is supported and the deterministic gate agrees.</p></article>
    </div>

    <section>
      <h2>A live model call. A deterministic final boundary.</h2>
      <div class="proof">
        <div>
          <p>Google ADK lets Gemini decompose and interpret the task. Proofline's tool then applies the same auditable gate to every run, so model fluency cannot silently turn missing evidence into completion.</p>
          <p class="claim">Verified Cloud Run execution: <strong>READY</strong><br>Packet hash: <code>973750f90ceffd925eba6716399f9064fcc789522ae8455efe764ef6c841eb5d</code></p>
        </div>
        <div>
          <p><strong>Public verification</strong></p>
          <div class="links">
            <a href="/list-apps">App discovery</a>
            <a href="/docs">OpenAPI</a>
            <a href="https://github.com/ceodaradigu/proofline-agent">Source and tests</a>
            <a href="https://devpost.com/software/proofline-65a8t4">Devpost submission</a>
          </div>
        </div>
      </div>
    </section>

    <footer>
      <span class="disclosure">AI-assisted project and presentation</span>
      <span>Synthetic demo fixtures · No customer data · External actions remain human-gated</span>
    </footer>
  </main>
</body>
</html>"""


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def landing_page() -> HTMLResponse:
    """Render the public judge-facing overview without invoking Gemini."""

    return HTMLResponse(
        LANDING_PAGE,
        headers={
            "Cache-Control": "public, max-age=300",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline'; "
                "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )
