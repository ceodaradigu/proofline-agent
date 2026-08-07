# Vercel Deployment Operations Airlock

Governed Vercel release operations for RailCall. The module gives an operator
nine focused commands for inspecting projects and deployments, reviewing
privacy-safe event metadata, and canceling or deleting a deployment only after
RailCall's preview → approval → execute → signed-receipt loop.

`contest:2026Q3`

## The operational problem

A deployment incident is exactly when a fast automation is most likely to act
on the wrong project, stale state, or an ambiguous URL. This module keeps the
fast path, but makes the consequential actions explicit:

- Read commands return bounded projections instead of proxying full API
  responses into receipts.
- Build-event content is hashed and omitted from receipts, preventing a build
  log from becoming a new secret-leak surface.
- Cancellation requires the exact live state observed during planning.
- Deletion requires both the exact deployment URL and its `createdAt` value.
- Every network destination is declared; subprocesses and filesystem writes
  are disabled.
- The Vercel token is read only through RailCall's local credential vault.

## Commands

| Command | Mode | Purpose |
| --- | --- | --- |
| `vercel.list_projects` | Read | List projects with pagination metadata. |
| `vercel.get_project` | Read | Inspect one project without returning environment variables. |
| `vercel.list_deployments` | Read | Filter deployments by project, target, state, and time. |
| `vercel.get_deployment` | Read | Fetch the safe state needed for an informed approval. |
| `vercel.get_deployment_events` | Read | Return event type/time plus a SHA-256 content fingerprint, never raw logs. |
| `vercel.list_deployment_files` | Read | List file metadata without downloading contents. |
| `vercel.list_deployment_aliases` | Read | Show aliases currently pointing at a deployment. |
| `vercel.cancel_deployment` | Approval required | Cancel only if the live state still matches the approved state. |
| `vercel.delete_deployment` | Approval required | Delete only after URL and creation-time preconditions both match. |

## Install and configure

After the marketplace listing is approved:

```sh
railcall market install relaunch-dept/vercel-deployment-ops
```

In RailCall Studio, open **Connect → Vercel** and save a Vercel access token as
`VERCEL_ACCESS_TOKEN`. For team-owned resources, pass `team_id` on commands.
The token remains local; it is never included in a receipt or marketplace
request.

Vercel recommends expiring access tokens rather than permanent tokens. Grant
only the account or team scope needed for the projects an operator will manage.

## Safe operating sequence

Inspect a deployment:

```sh
railcall airlock stage vercel.get_deployment \
  --inputs '{"deployment_id_or_url":"dpl_example","team_id":"team_example"}'
```

To cancel it, copy the observed `readyState` into a new plan. RailCall will
require approval and the handler will fetch the deployment again before acting:

```sh
railcall airlock stage vercel.cancel_deployment \
  --inputs '{"deployment_id":"dpl_example","expected_ready_state":"BUILDING","team_id":"team_example"}'
```

Deletion deliberately needs two independently visible values:

```sh
railcall airlock stage vercel.delete_deployment \
  --inputs '{"deployment_id":"dpl_example","confirm_deployment_url":"app-example.vercel.app","expected_created_at":1786000000000,"team_id":"team_example"}'
```

If the URL, creation time, or current state changed after preview, execution
refuses and tells the operator to fetch and approve a fresh plan.

## Reliability behavior

- GET, PATCH-cancel, and DELETE calls retry boundedly on HTTP 429 and transient
  5xx responses.
- `Retry-After` is honored up to 60 seconds; otherwise exponential delays are
  used.
- API errors retain Vercel's error code and message but redact the active token.
- Cancellation is polled after the API accepts it; an unverified transition is
  reported as a failure, not a false success.
- Deletion is followed by an authoritative GET and succeeds only on a 404.

## Local checks

The repository uses only Python's standard library:

```sh
python -m json.tool module.json > /dev/null
python -m unittest discover -s tests -v
```

Before marketplace publication, the release checklist also requires a real,
least-privilege Vercel token and a disposable preview deployment for the live
read/cancel/delete smoke test. No production deployment should be used.

## Source and disclosure

Original work by RELAUNCH DEPT for the 2026 Q3 RailCall contest. Development was
LLM-assisted; the implementation is kept small, provider-specific, and backed
by explicit acceptance tests rather than generic generated documentation.

Public source lives in the Proofline Agent repository under
`integrations/railcall-vercel-deployment-ops`.
