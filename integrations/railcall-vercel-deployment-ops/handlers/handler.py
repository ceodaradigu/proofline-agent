"""RailCall handlers for governed Vercel deployment operations.

The bundle uses only Python's standard library. In RailCall, the Vercel token
is resolved exclusively through the injected local vault helper. The direct
environment fallback exists only so maintainers can run the standalone tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


try:
    _RC_HELPERS = __rc_helpers__
except NameError:  # Standalone tests only; never reached inside RailCall.
    _RC_HELPERS = {}


API_ROOT = "https://api.vercel.com"
MAX_ATTEMPTS = 3
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
SAFE_RETRY_METHODS = {"GET", "PATCH", "DELETE"}
CANCELLABLE_STATES = {"BUILDING", "INITIALIZING", "QUEUED"}


class VercelApiError(RuntimeError):
    """A definite non-success response from the Vercel API."""


class ApiResult:
    """Small response value used without leaking headers or credentials."""

    def __init__(self, data: Any, status: int, attempts: int):
        self.data = data
        self.status = status
        self.attempts = attempts


def list_projects(inputs: dict, context: dict) -> dict:
    """List projects visible to the token, returning a bounded safe projection."""
    _unused(context)
    query = _team_query(inputs)
    query["limit"] = _bounded_int(inputs.get("limit", 20), "limit", 1, 100)
    cursor = _optional_str(inputs, "from", max_length=500)
    if cursor:
        query["from"] = cursor
    result = _request("GET", "/v9/projects", query=query)
    envelope = _require_dict(result.data, "project-list response")
    return {
        "projects": [_safe_project(item) for item in _dict_list(envelope.get("projects"), "projects")],
        "pagination": _safe_pagination(envelope.get("pagination")),
        "api_status": result.status,
        "attempts": result.attempts,
    }


def get_project(inputs: dict, context: dict) -> dict:
    """Get one project without returning environment variables or secrets."""
    _unused(context)
    project = _required_str(inputs, "project_id_or_name", max_length=200)
    result = _request(
        "GET",
        f"/v9/projects/{_path(project)}",
        query=_team_query(inputs),
    )
    return {
        "project": _safe_project(_require_dict(result.data, "project response")),
        "api_status": result.status,
        "attempts": result.attempts,
    }


def list_deployments(inputs: dict, context: dict) -> dict:
    """List deployments with optional project, target, state, and time filters."""
    _unused(context)
    query = _team_query(inputs)
    query["limit"] = _bounded_int(inputs.get("limit", 20), "limit", 1, 100)
    _copy_optional_str(inputs, query, "project_id", "projectId", 200)
    _copy_optional_choice(inputs, query, "target", {"production", "preview"})
    _copy_optional_choice(
        inputs,
        query,
        "state",
        {"BUILDING", "CANCELED", "ERROR", "INITIALIZING", "QUEUED", "READY"},
    )
    for key in ("since", "until"):
        if key in inputs:
            query[key] = _bounded_int(inputs[key], key, 0, 9_999_999_999_999)

    result = _request("GET", "/v6/deployments", query=query)
    envelope = _require_dict(result.data, "deployment-list response")
    return {
        "deployments": [
            _safe_deployment(item)
            for item in _dict_list(envelope.get("deployments"), "deployments")
        ],
        "pagination": _safe_pagination(envelope.get("pagination")),
        "api_status": result.status,
        "attempts": result.attempts,
    }


def get_deployment(inputs: dict, context: dict) -> dict:
    """Get one deployment by ID or URL."""
    _unused(context)
    identifier = _required_str(inputs, "deployment_id_or_url", max_length=500)
    result = _get_deployment_result(identifier, inputs)
    return {
        "deployment": _safe_deployment(_require_dict(result.data, "deployment response")),
        "api_status": result.status,
        "attempts": result.attempts,
    }


def get_deployment_events(inputs: dict, context: dict) -> dict:
    """Return event metadata and content hashes, never raw build-log content."""
    _unused(context)
    identifier = _required_str(inputs, "deployment_id_or_url", max_length=500)
    query = _team_query(inputs)
    query["limit"] = _bounded_int(inputs.get("limit", 50), "limit", 1, 100)
    result = _request(
        "GET",
        f"/v2/deployments/{_path(identifier)}/events",
        query=query,
    )
    events = _event_list(result.data)
    return {
        "events": [_safe_event(item) for item in events],
        "event_count": len(events),
        "content_omitted_from_receipt": True,
        "api_status": result.status,
        "attempts": result.attempts,
    }


def list_deployment_files(inputs: dict, context: dict) -> dict:
    """List deployment file metadata without downloading file contents."""
    _unused(context)
    deployment_id = _required_str(inputs, "deployment_id", max_length=200)
    result = _request(
        "GET",
        f"/v6/deployments/{_path(deployment_id)}/files",
        query=_team_query(inputs),
    )
    raw_files = result.data
    if isinstance(raw_files, dict):
        raw_files = raw_files.get("files", raw_files.get("items", []))
    files = _dict_list(raw_files, "deployment files")
    return {
        "files": [_safe_file(item) for item in files],
        "api_status": result.status,
        "attempts": result.attempts,
    }


def list_deployment_aliases(inputs: dict, context: dict) -> dict:
    """List aliases currently assigned to one deployment."""
    _unused(context)
    deployment_id = _required_str(inputs, "deployment_id", max_length=200)
    result = _request(
        "GET",
        f"/v2/deployments/{_path(deployment_id)}/aliases",
        query=_team_query(inputs),
    )
    raw_aliases = result.data
    if isinstance(raw_aliases, dict):
        raw_aliases = raw_aliases.get("aliases", [])
    aliases = _dict_list(raw_aliases, "deployment aliases")
    return {
        "aliases": [_safe_alias(item) for item in aliases],
        "api_status": result.status,
        "attempts": result.attempts,
    }


def cancel_deployment(inputs: dict, context: dict) -> dict:
    """Cancel only when the live deployment state matches the approved state."""
    _unused(context)
    deployment_id = _required_str(inputs, "deployment_id", max_length=200)
    expected = _required_choice(inputs, "expected_ready_state", CANCELLABLE_STATES)
    before_result = _get_deployment_result(deployment_id, inputs)
    before_raw = _require_dict(before_result.data, "deployment response")
    before = _safe_deployment(before_raw)
    live_state = _deployment_state(before_raw)

    if live_state == "CANCELED":
        return {
            "before": before,
            "after": before,
            "changed": False,
            "api_status": before_result.status,
            "attempts": before_result.attempts,
        }
    if live_state != expected:
        raise RuntimeError(
            "Refusing stale cancellation: expected_ready_state "
            f"{expected!r}, live deployment is {live_state!r}. "
            "Fetch the deployment again and approve a fresh plan."
        )
    if live_state not in CANCELLABLE_STATES:
        raise RuntimeError(f"Deployment state {live_state!r} cannot be canceled safely.")

    cancel_result = _request(
        "PATCH",
        f"/v12/deployments/{_path(deployment_id)}/cancel",
        query=_team_query(inputs),
    )
    attempts = before_result.attempts + cancel_result.attempts
    after_result = _poll_deployment_state(deployment_id, inputs, {"CANCELED", "ERROR"})
    attempts += after_result.attempts
    after_raw = _require_dict(after_result.data, "post-cancel deployment response")
    after_state = _deployment_state(after_raw)
    if after_state not in {"CANCELED", "ERROR"}:
        raise RuntimeError(
            "Vercel accepted the cancellation but the live deployment state "
            f"could not be verified (current state: {after_state!r})."
        )
    return {
        "before": before,
        "after": _safe_deployment(after_raw),
        "changed": True,
        "api_status": cancel_result.status,
        "attempts": attempts,
    }


def delete_deployment(inputs: dict, context: dict) -> dict:
    """Delete a deployment only after URL and creation-time preconditions match."""
    _unused(context)
    deployment_id = _required_str(inputs, "deployment_id", max_length=200)
    confirm_url = _required_str(inputs, "confirm_deployment_url", max_length=500)
    expected_created_at = _bounded_int(
        inputs.get("expected_created_at"),
        "expected_created_at",
        0,
        9_999_999_999_999,
    )
    before_result = _get_deployment_result(deployment_id, inputs)
    before_raw = _require_dict(before_result.data, "deployment response")
    live_url = str(before_raw.get("url") or "")
    live_created_at = before_raw.get("createdAt")
    if live_url != confirm_url:
        raise RuntimeError(
            "Refusing deletion: confirm_deployment_url does not match the live deployment URL."
        )
    if live_created_at != expected_created_at:
        raise RuntimeError(
            "Refusing stale deletion: expected_created_at does not match the live deployment. "
            "Fetch the deployment again and approve a fresh plan."
        )

    delete_result = _request(
        "DELETE",
        f"/v13/deployments/{_path(deployment_id)}",
        query=_team_query(inputs),
    )
    verify_result = _request(
        "GET",
        f"/v13/deployments/{_path(deployment_id)}",
        query=_team_query(inputs),
        allowed_statuses={404},
    )
    if verify_result.status != 404:
        raise RuntimeError("Vercel accepted the deletion but the deployment still exists.")
    return {
        "deleted": True,
        "deployment": _safe_deployment(before_raw),
        "api_status": delete_result.status,
        "attempts": before_result.attempts + delete_result.attempts + verify_result.attempts,
    }


def _request(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    allowed_statuses: set[int] | None = None,
) -> ApiResult:
    method = method.upper()
    url = f"{API_ROOT}{path}"
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    allowed_statuses = allowed_statuses or set()

    for attempt in range(MAX_ATTEMPTS):
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {_vercel_token()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "RailCall-Vercel-Deployment-Ops/0.1.0",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8", errors="replace")
                data = json.loads(raw) if raw else {}
                status = int(getattr(response, "status", response.getcode()))
                return ApiResult(data, status, attempt + 1)
        except HTTPError as exc:
            status = int(exc.code)
            if status in allowed_statuses:
                try:
                    exc.close()
                except Exception:
                    pass
                return ApiResult(None, status, attempt + 1)
            retryable = status in RETRYABLE_STATUSES and method in SAFE_RETRY_METHODS
            if retryable and attempt < MAX_ATTEMPTS - 1:
                delay = _retry_delay(exc, attempt)
                try:
                    exc.close()
                except Exception:
                    pass
                time.sleep(delay)
                continue
            detail = _error_detail(exc)
            raise VercelApiError(
                f"Vercel {method} {path} failed with HTTP {status}: {detail}"
            ) from exc
        except URLError as exc:
            if method in SAFE_RETRY_METHODS and attempt < MAX_ATTEMPTS - 1:
                time.sleep(float(2**attempt))
                continue
            raise VercelApiError(
                f"Vercel {method} {path} failed: {_safe_text(getattr(exc, 'reason', exc))}"
            ) from exc

    raise VercelApiError(f"Vercel {method} {path} failed after {MAX_ATTEMPTS} attempts.")


def _get_deployment_result(identifier: str, inputs: dict) -> ApiResult:
    return _request(
        "GET",
        f"/v13/deployments/{_path(identifier)}",
        query=_team_query(inputs),
    )


def _poll_deployment_state(
    deployment_id: str,
    inputs: dict,
    terminal_states: set[str],
) -> ApiResult:
    total_attempts = 0
    latest: ApiResult | None = None
    for delay in (0.0, 0.5, 1.0):
        if delay:
            time.sleep(delay)
        latest = _get_deployment_result(deployment_id, inputs)
        total_attempts += latest.attempts
        raw = _require_dict(latest.data, "deployment response")
        if _deployment_state(raw) in terminal_states:
            return ApiResult(raw, latest.status, total_attempts)
    if latest is None:
        raise RuntimeError("Deployment verification did not run.")
    return ApiResult(latest.data, latest.status, total_attempts)


def _vercel_token() -> str:
    token = ""
    vault_get = _RC_HELPERS.get("vault_get") if isinstance(_RC_HELPERS, dict) else None
    if callable(vault_get):
        entry = vault_get("vercel")
        if isinstance(entry, str):
            token = entry.strip()
        elif isinstance(entry, dict):
            for key in ("VERCEL_ACCESS_TOKEN", "access_token", "token", "api_key"):
                if entry.get(key):
                    token = str(entry[key]).strip()
                    break
    else:
        token = os.environ.get("VERCEL_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Vercel credential missing. Open RailCall Studio > Connect > Vercel, "
            "paste VERCEL_ACCESS_TOKEN, and save it locally."
        )
    if any(character.isspace() for character in token):
        raise RuntimeError("The saved Vercel credential has an invalid shape; replace it in Studio.")
    return token


def _team_query(inputs: dict) -> dict[str, Any]:
    query: dict[str, Any] = {}
    team_id = _optional_str(inputs, "team_id", max_length=200)
    if team_id:
        query["teamId"] = team_id
    return query


def _safe_project(project: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        project,
        (
            "id",
            "name",
            "accountId",
            "framework",
            "createdAt",
            "updatedAt",
            "latestDeployments",
            "link",
            "paused",
        ),
        nested_limits={"latestDeployments": 3},
    )


def _safe_deployment(deployment: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        deployment,
        (
            "uid",
            "id",
            "name",
            "url",
            "projectId",
            "readyState",
            "state",
            "target",
            "createdAt",
            "buildingAt",
            "ready",
            "readySubstate",
            "creator",
            "alias",
        ),
        nested_limits={"alias": 20},
    )


def _safe_event(event: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return {
        "id": event.get("id"),
        "type": event.get("type"),
        "created": event.get("created", event.get("createdAt")),
        "serial": event.get("serial"),
        "content_sha256": hashlib.sha256(encoded).hexdigest(),
        "content_bytes": len(encoded),
    }


def _safe_file(item: dict[str, Any]) -> dict[str, Any]:
    return _pick(item, ("name", "type", "mode", "uid", "size", "sha"))


def _safe_alias(item: dict[str, Any]) -> dict[str, Any]:
    return _pick(item, ("uid", "alias", "created", "createdAt", "projectId", "deploymentId"))


def _safe_pagination(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return _pick(value, ("count", "next", "prev", "nextFrom"))


def _pick(
    value: dict[str, Any],
    keys: tuple[str, ...],
    *,
    nested_limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    nested_limits = nested_limits or {}
    for key in keys:
        if key not in value:
            continue
        item = value[key]
        if key in nested_limits and isinstance(item, list):
            item = item[: nested_limits[key]]
        if key == "creator" and isinstance(item, dict):
            item = _pick(item, ("uid", "username"))
        elif key == "link" and isinstance(item, dict):
            item = _pick(item, ("type", "repo", "repoId", "org", "gitCredentialId"))
        elif key == "latestDeployments" and isinstance(item, list):
            item = [_safe_deployment(x) for x in item if isinstance(x, dict)]
        result[key] = item
    return result


def _deployment_state(deployment: dict[str, Any]) -> str:
    return str(deployment.get("readyState") or deployment.get("state") or "UNKNOWN").upper()


def _event_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return _dict_list(value, "deployment events")
    if isinstance(value, dict):
        for key in ("events", "items"):
            if key in value:
                return _dict_list(value[key], "deployment events")
    raise RuntimeError("Vercel returned an invalid deployment-events response.")


def _dict_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise RuntimeError(f"Vercel returned an invalid {label} list.")
    return value


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"Vercel returned an invalid {label}.")
    return value


def _copy_optional_str(
    inputs: dict,
    query: dict[str, Any],
    input_key: str,
    query_key: str,
    max_length: int,
) -> None:
    value = _optional_str(inputs, input_key, max_length=max_length)
    if value:
        query[query_key] = value


def _copy_optional_choice(
    inputs: dict,
    query: dict[str, Any],
    key: str,
    allowed: set[str],
) -> None:
    if key in inputs:
        query[key] = _required_choice(inputs, key, allowed)


def _required_choice(inputs: dict, key: str, allowed: set[str]) -> str:
    value = _required_str(inputs, key, max_length=100)
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(allowed))}.")
    return value


def _required_str(inputs: dict, key: str, *, max_length: int) -> str:
    if key not in inputs:
        raise ValueError(f"{key} is required.")
    value = inputs[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{key} must not be empty.")
    if len(value) > max_length:
        raise ValueError(f"{key} must be at most {max_length} characters.")
    return value


def _optional_str(inputs: dict, key: str, *, max_length: int) -> str:
    if key not in inputs or inputs[key] in (None, ""):
        return ""
    return _required_str(inputs, key, max_length=max_length)


def _bounded_int(value: Any, key: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        raise ValueError(f"{key} must be an integer between {minimum} and {maximum}.")
    return value


def _path(value: str) -> str:
    return quote(value, safe="")


def _retry_delay(exc: HTTPError, attempt: int) -> float:
    retry_after = exc.headers.get("Retry-After") if exc.headers else None
    if retry_after:
        try:
            return min(max(float(retry_after), 0.0), 60.0)
        except (TypeError, ValueError):
            pass
    return float(2**attempt)


def _error_detail(exc: HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw) if raw else {}
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, dict):
                code = error.get("code")
                message = error.get("message")
                return _safe_text(f"{code}: {message}")
        return _safe_text(raw or exc.reason or "unknown error")
    except Exception:
        return _safe_text(exc.reason or "unknown error")
    finally:
        try:
            exc.close()
        except Exception:
            pass


def _safe_text(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    try:
        token = _vercel_token()
    except Exception:
        token = os.environ.get("VERCEL_ACCESS_TOKEN", "")
    if token:
        text = text.replace(token, "[REDACTED]")
    return text[:500]


def _unused(*_values: Any) -> None:
    return None


# Station registers dotted command IDs by replacing dots with underscores and
# expects each handler to return (receipt_output, optional_artifact_path).
def vercel_list_projects(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return list_projects(inputs, stamp), None


def vercel_get_project(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return get_project(inputs, stamp), None


def vercel_list_deployments(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return list_deployments(inputs, stamp), None


def vercel_get_deployment(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return get_deployment(inputs, stamp), None


def vercel_get_deployment_events(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return get_deployment_events(inputs, stamp), None


def vercel_list_deployment_files(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return list_deployment_files(inputs, stamp), None


def vercel_list_deployment_aliases(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return list_deployment_aliases(inputs, stamp), None


def vercel_cancel_deployment(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return cancel_deployment(inputs, stamp), None


def vercel_delete_deployment(inputs: dict, stamp: Any) -> tuple[dict, None]:
    return delete_deployment(inputs, stamp), None
