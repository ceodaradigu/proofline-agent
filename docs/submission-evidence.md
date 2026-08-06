# Submission evidence

Checked on 2026-08-06 against the public submission and deployment. This page
separates externally verified facts from planned extensions and prize claims.

## Contest timing and eligibility

- The official submission period runs from 2026-08-03 09:00 PT through
  2026-08-31 17:00 PT.
- Proofline's first public commit is `1a55d8f`, dated 2026-08-05 08:00 +02:00,
  after the submission period began.
- The entry is submitted as an individual project in the Taskmaster category.
- Spain is not included in the official list of excluded jurisdictions.

## Required stack

| Requirement | Evidence | Status |
| --- | --- | --- |
| Gemini 3.5 or newer | `proofline/agent.py` configures Gemini 3.6 Flash; the live execution evidence records a successful model/tool round trip | Verified |
| Google agent framework | Google ADK 2.6.2 application and root agent; dependencies are pinned to ADK 2.x | Verified |
| Google Cloud infrastructure | Public Cloud Run revision `proofline-00001-rqw` in `europe-west1` | Verified |
| New project during the contest | First commit `1a55d8f` on 2026-08-05 | Verified |
| Reproducible repository | Public source, local commands, container contract, deployment guide, and nine passing tests | Verified |
| Architecture diagram | `docs/architecture.md` and the generated diagram used in the demo | Verified |
| Public demonstration under four minutes | Public 2:53 YouTube demo with live Cloud Run evidence | Verified |
| Public submission | Devpost project `proofline-65a8t4` | Verified |

## Public verification endpoints

- Submission: <https://devpost.com/software/proofline-65a8t4>
- Repository: <https://github.com/ceodaradigu/proofline-agent>
- Video: <https://youtu.be/khPpdq7GcTk>
- Cloud Run app discovery:
  <https://proofline-343140361830.europe-west1.run.app/list-apps>

The public Devpost page returned HTTP 200 and contained the expected submission,
repository, video, Cloud Run, Gemini 3.6, Google ADK, and hackathon references.
The Cloud Run discovery endpoint returned HTTP 200 with `["proofline"]`.

## Claim boundary

- Firestore and Pub/Sub are documented extension points, not claimed as active
  in the current in-memory demonstration.
- The deterministic gate, not the language model, makes the final packet-state
  decision.
- External actions remain behind explicit human approval.
- Submission does not imply selection, award, or payment. Confirmed prize and
  revenue remain zero until the organizer provides award and payment evidence.
