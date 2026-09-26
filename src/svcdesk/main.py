# ai-generated: 100% - Implemented the full svcdesk HTTP API, persistence layer, SLA clock logic, and ticket lifecycle enforcement.

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

WARSAW = ZoneInfo("Europe/Warsaw")
DECISION_C1 = "wallclock"
DECISION_C2 = "immutable"
DECISION_C3 = "vip"
PRIORITY_ORDER = ["P1", "P2", "P3", "P4"]


class ValidationError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_rfc3339(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_request_now(request: Request) -> datetime:
    header_value = request.headers.get("x-test-clock")
    if header_value is not None:
        raw = header_value.strip()
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                raise ValueError
            return parsed.astimezone(timezone.utc)
        except ValueError as exc:
            raise ValidationError("X-Test-Clock header is not a valid RFC 3339 instant") from exc

    env_value = os.getenv("SVCDESK_TEST_CLOCK", "").strip().lower()
    if env_value in {"1", "true"}:
        return utc_now()
    return utc_now()


def error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def is_business_day(day: date) -> bool:
    return day.weekday() < 5


def is_business_window(local_dt: datetime) -> bool:
    local_time = local_dt.timetz()
    return local_dt.weekday() < 5 and time(8, 0, 0) <= local_time < time(16, 0, 0)


def next_business_start(local_dt: datetime) -> datetime:
    candidate = local_dt.date()
    if local_dt.weekday() < 5 and local_dt.timetz() < time(8, 0, 0):
        return datetime.combine(candidate, time(8, 0, 0), tzinfo=local_dt.tzinfo)

    for offset in range(1, 14):
        day = candidate + timedelta(days=offset)
        if is_business_day(day):
            return datetime.combine(day, time(8, 0, 0), tzinfo=local_dt.tzinfo)
    raise ValueError("no business day found")


def business_due_for(created_at: datetime, target: timedelta) -> datetime:
    local = created_at.astimezone(WARSAW)

    # If the ticket is created outside working hours, SLA starts
    # at the next business window.
    if local.weekday() >= 5 or local.timetz() >= time(16, 0):
        local = next_business_start(local)
    elif local.timetz() < time(8, 0):
        local = local.replace(hour=8, minute=0, second=0, microsecond=0)

    remaining = target

    while remaining > timedelta(0):
        end = local.replace(hour=16, minute=0, second=0, microsecond=0)
        available = end - local

        if remaining <= available:
            return (local + remaining).astimezone(timezone.utc)

        remaining -= available
        local = next_business_start(end)

    return local.astimezone(timezone.utc)


def compute_sla_for_priority(created_at: datetime, priority: str) -> dict[str, str]:
    ack_window = {"P1": timedelta(hours=1), "P2": timedelta(hours=1), "P3": timedelta(hours=4), "P4": timedelta(hours=8)}
    resolve_window = {"P1": timedelta(hours=4), "P2": timedelta(hours=8), "P3": timedelta(hours=24), "P4": timedelta(hours=72)}

    if priority == "P1" and DECISION_C1 == "wallclock":
        ack_due = created_at + ack_window[priority]
        resolve_due = created_at + resolve_window[priority]
    else:
        ack_due = business_due_for(created_at, ack_window[priority])
        resolve_due = business_due_for(created_at, resolve_window[priority])

    return {"ack_due_at": to_rfc3339(ack_due), "resolve_due_at": to_rfc3339(resolve_due)}


def matrix_priority(impact: int, urgency: int) -> str:
    table = {
        (1, 1): "P1",
        (1, 2): "P2",
        (1, 3): "P3",
        (2, 1): "P2",
        (2, 2): "P3",
        (2, 3): "P4",
        (3, 1): "P3",
        (3, 2): "P4",
        (3, 3): "P4",
    }
    return table[(impact, urgency)]


def vip_priority(base_priority: str) -> str:
    if base_priority in {"P3", "P4"}:
        return "P2"
    return base_priority


def validate_ticket_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("request body must be a JSON object")

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValidationError("title is required")

    description = payload.get("description", "")
    if description is None:
        description = ""
    if not isinstance(description, str) or len(description) > 4000:
        raise ValidationError("description exceeds 4000 characters")

    reporter = payload.get("reporter")
    if not isinstance(reporter, dict):
        raise ValidationError("reporter is required")

    reporter_name = reporter.get("name")
    if not isinstance(reporter_name, str) or not reporter_name.strip() or len(reporter_name) > 100:
        raise ValidationError("reporter.name is required")

    reporter_email = reporter.get("email")
    if reporter_email is not None and (not isinstance(reporter_email, str) or len(reporter_email) > 255):
        raise ValidationError("reporter.email is invalid")

    vip = reporter.get("vip", False)
    if not isinstance(vip, bool):
        raise ValidationError("reporter.vip must be a boolean")

    impact = payload.get("impact")
    urgency = payload.get("urgency")
    if isinstance(impact, bool) or not isinstance(impact, int) or impact not in (1, 2, 3):
        raise ValidationError("impact is required")
    if isinstance(urgency, bool) or not isinstance(urgency, int) or urgency not in (1, 2, 3):
        raise ValidationError("urgency is required")

    related_to = payload.get("related_to")
    if related_to is not None and not isinstance(related_to, str):
        raise ValidationError("related_to must be a string or null")

    return {
        "title": title,
        "description": description,
        "reporter": {"name": reporter_name, "email": reporter_email, "vip": vip},
        "impact": impact,
        "urgency": urgency,
        "related_to": related_to,
    }


def get_db_connection() -> sqlite3.Connection:
    db_path = os.getenv("SVCDESK_DB", "/data/svcdesk.db")
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            reporter_name TEXT NOT NULL,
            reporter_email TEXT,
            reporter_vip INTEGER NOT NULL,
            impact INTEGER NOT NULL,
            urgency INTEGER NOT NULL,
            priority TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            acknowledged_at TEXT,
            resolved_at TEXT,
            closed_at TEXT,
            related_to TEXT
        )
        """
    )
    conn.commit()
    return conn


def row_to_ticket(row: sqlite3.Row) -> dict[str, Any]:
    ticket = {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "reporter": {
            "name": row["reporter_name"],
            "email": row["reporter_email"],
            "vip": bool(row["reporter_vip"]),
        },
        "impact": row["impact"],
        "urgency": row["urgency"],
        "priority": row["priority"],
        "state": row["state"],
        "created_at": row["created_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
        "closed_at": row["closed_at"],
        "related_to": row["related_to"],
    }
    ticket["sla"] = compute_sla_for_priority(datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")), row["priority"])
    return ticket


def fetch_ticket(ticket_id: str) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return row


def fetch_all_tickets(filters: dict[str, str]) -> list[dict[str, Any]]:
    conn = get_db_connection()
    query = "SELECT * FROM tickets"
    where: list[str] = []
    params: list[str] = []
    if "state" in filters:
        where.append("state = ?")
        params.append(filters["state"])
    if "priority" in filters:
        where.append("priority = ?")
        params.append(filters["priority"])
    if where:
        query += " WHERE " + " AND ".join(where)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_ticket(row) for row in rows]


def save_ticket(ticket: dict[str, Any]) -> None:
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO tickets (
            id, title, description, reporter_name, reporter_email, reporter_vip,
            impact, urgency, priority, state, created_at, acknowledged_at, resolved_at, closed_at, related_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket["id"],
            ticket["title"],
            ticket["description"],
            ticket["reporter"]["name"],
            ticket["reporter"]["email"],
            int(ticket["reporter"]["vip"]),
            ticket["impact"],
            ticket["urgency"],
            ticket["priority"],
            ticket["state"],
            ticket["created_at"],
            ticket["acknowledged_at"],
            ticket["resolved_at"],
            ticket["closed_at"],
            ticket["related_to"],
        ),
    )
    conn.commit()
    conn.close()


def update_ticket(ticket_id: str, updates: dict[str, Any]) -> None:
    conn = get_db_connection()
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = list(updates.values())
    values.append(ticket_id)
    conn.execute(f"UPDATE tickets SET {assignments} WHERE id = ?", values)
    conn.commit()
    conn.close()


def build_ticket_from_payload(payload: dict[str, Any], now: datetime) -> dict[str, Any]:
    validated = validate_ticket_payload(payload)
    base_priority = matrix_priority(validated["impact"], validated["urgency"])
    final_priority = vip_priority(base_priority) if validated["reporter"]["vip"] else base_priority
    created_at = to_rfc3339(now)
    ticket = {
        "id": str(uuid.uuid4()),
        "title": validated["title"],
        "description": validated["description"],
        "reporter": {
            "name": validated["reporter"]["name"],
            "email": validated["reporter"]["email"],
            "vip": validated["reporter"]["vip"],
        },
        "impact": validated["impact"],
        "urgency": validated["urgency"],
        "priority": final_priority,
        "state": "new",
        "created_at": created_at,
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": validated["related_to"],
    }
    ticket["sla"] = compute_sla_for_priority(now, final_priority)
    return ticket


def load_ticket_for_response(ticket_id: str) -> Optional[dict[str, Any]]:
    row = fetch_ticket(ticket_id)
    if row is None:
        return None
    return row_to_ticket(row)


def is_ticket_breached_for_ack(ticket: dict[str, Any], now: datetime) -> bool:
    ack_due = datetime.fromisoformat(ticket["sla"]["ack_due_at"].replace("Z", "+00:00"))
    if ticket["acknowledged_at"] is None:
        return now > ack_due
    acknowledged_at = datetime.fromisoformat(ticket["acknowledged_at"].replace("Z", "+00:00"))
    return acknowledged_at > ack_due


def is_ticket_breached_for_resolve(ticket: dict[str, Any], now: datetime) -> bool:
    resolve_due = datetime.fromisoformat(ticket["sla"]["resolve_due_at"].replace("Z", "+00:00"))
    if ticket["state"] in {"resolved", "closed"}:
        if ticket["resolved_at"] is None:
            return False
        resolved_at = datetime.fromisoformat(ticket["resolved_at"].replace("Z", "+00:00"))
        return resolved_at > resolve_due
    return now > resolve_due


def compute_paused(ticket: dict[str, Any], now: datetime) -> bool:
    if ticket["state"] in {"resolved", "closed"}:
        return False
    if ticket["priority"] == "P1":
        return False
    return not is_business_window(now.astimezone(WARSAW))


app = FastAPI(title="svcdesk")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response("validation", "validation error", 422)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response("not_found", "route not found", 404)
    return error_response("validation", str(exc.detail), exc.status_code)


@app.post("/tickets")
async def create_ticket(request: Request) -> Any:
    try:
        payload = await request.json()
    except Exception:
        return error_response("validation", "request body must be valid JSON", 400)

    try:
        now = parse_request_now(request)
        ticket = build_ticket_from_payload(payload, now)
    except ValidationError as exc:
        return error_response("validation", str(exc), 400)

    save_ticket(ticket)
    return JSONResponse(status_code=201, content=ticket)


@app.get("/tickets")
def list_tickets(state: Optional[str] = Query(default=None), priority: Optional[str] = Query(default=None)) -> list[dict[str, Any]]:
    filters: dict[str, str] = {}
    if state is not None:
        filters["state"] = state
    if priority is not None:
        filters["priority"] = priority
    return fetch_all_tickets(filters)


@app.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: str) -> Any:
    ticket = load_ticket_for_response(ticket_id)
    if ticket is None:
        return error_response("not_found", "ticket not found", 404)
    return ticket


@app.get("/tickets/{ticket_id}/sla")
def ticket_sla(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)

    now = parse_request_now(request)
    ticket = row_to_ticket(row)
    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        "ack_breached": is_ticket_breached_for_ack(ticket, now),
        "resolve_breached": is_ticket_breached_for_resolve(ticket, now),
        "paused": compute_paused(ticket, now),
    }


@app.post("/tickets/{ticket_id}/ack")
async def acknowledge_ticket(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)
    if row["state"] != "new":
        return error_response("invalid_transition", "invalid ticket transition", 409)
    now = parse_request_now(request)
    update_ticket(ticket_id, {"state": "acknowledged", "acknowledged_at": to_rfc3339(now)})
    return JSONResponse(content=load_ticket_for_response(ticket_id))


@app.post("/tickets/{ticket_id}/start")
async def start_ticket(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)
    if row["state"] != "acknowledged":
        return error_response("invalid_transition", "invalid ticket transition", 409)
    now = parse_request_now(request)
    update_ticket(ticket_id, {"state": "in_progress", "acknowledged_at": row["acknowledged_at"] or to_rfc3339(now)})
    return JSONResponse(content=load_ticket_for_response(ticket_id))


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)
    if row["state"] != "in_progress":
        return error_response("invalid_transition", "invalid ticket transition", 409)
    now = parse_request_now(request)
    update_ticket(ticket_id, {"state": "resolved", "resolved_at": to_rfc3339(now)})
    return JSONResponse(content=load_ticket_for_response(ticket_id))


@app.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)
    if row["state"] not in {"resolved", "in_progress"}:
        return error_response("invalid_transition", "invalid ticket transition", 409)
    now = parse_request_now(request)
    update_ticket(ticket_id, {"state": "closed", "closed_at": to_rfc3339(now)})
    return JSONResponse(content=load_ticket_for_response(ticket_id))


@app.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, request: Request) -> Any:
    row = fetch_ticket(ticket_id)
    if row is None:
        return error_response("not_found", "ticket not found", 404)
    now = parse_request_now(request)

    if row["state"] == "resolved":
        resolved_at = datetime.fromisoformat(row["resolved_at"].replace("Z", "+00:00"))
        if now > resolved_at + timedelta(days=7):
            return error_response("reopen_window_expired", "reopen window expired", 409)
        update_ticket(ticket_id, {"state": "in_progress", "resolved_at": None})
        return JSONResponse(content=load_ticket_for_response(ticket_id))

    if row["state"] == "closed":
        if DECISION_C2 == "reopen":
            closed_at = datetime.fromisoformat(row["closed_at"].replace("Z", "+00:00"))
            if now > closed_at + timedelta(days=7):
                return error_response("reopen_window_expired", "reopen window expired", 409)
            update_ticket(ticket_id, {"state": "in_progress", "closed_at": None, "resolved_at": None})
            return JSONResponse(content=load_ticket_for_response(ticket_id))
        return error_response("ticket_closed", "closed tickets are immutable", 409)

    return error_response("invalid_transition", "invalid ticket transition", 409)
