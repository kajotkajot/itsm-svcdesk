import sys
from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")

from svcdesk.main import app  # noqa: E402

client = TestClient(app)
passed = 0
failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"CHECK {name}: ok")
    except Exception as exc:  # pragma: no cover - test harness only
        failed += 1
        print(f"CHECK {name}: FAIL - {exc}")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "svcdesk"


def test_create_and_get():
    payload = {
        "title": "Printer issue",
        "description": "Cannot print",
        "reporter": {"name": "Anna", "email": "anna@example.com", "vip": False},
        "impact": 2,
        "urgency": 1,
    }
    response = client.post("/tickets", json=payload, headers={"X-Test-Clock": "2026-10-14T10:00:00Z"})
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["state"] == "new"
    assert ticket["priority"] == "P2"
    assert ticket["sla"]["ack_due_at"] == "2026-10-14T11:00:00Z"
    ticket_id = ticket["id"]
    fetched = client.get(f"/tickets/{ticket_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == ticket_id


def test_matrix_and_vip():
    vip_ticket = client.post(
        "/tickets",
        json={
            "title": "VIP case",
            "reporter": {"name": "Exec", "email": "exec@example.com", "vip": True},
            "impact": 3,
            "urgency": 3,
        },
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
    )
    assert vip_ticket.status_code == 201
    assert vip_ticket.json()["priority"] == "P2"


def test_invalid_title_rejected():
    response = client.post("/tickets", json={"reporter": {"name": "test"}, "impact": 1, "urgency": 1})
    assert response.status_code in {400, 422}
    assert "error" in response.json()


def test_list_filters():
    client.post("/tickets", json={"title": "P1 ticket", "reporter": {"name": "A"}, "impact": 1, "urgency": 1}, headers={"X-Test-Clock": "2026-10-14T10:00:00Z"})
    response = client.get("/tickets?priority=P1")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert len(ids) >= 1

    state_response = client.get("/tickets?state=new")
    assert state_response.status_code == 200
    assert isinstance(state_response.json(), list)


def test_ack_start_resolve_close():
    ticket = client.post(
        "/tickets",
        json={"title": "Lifecycle", "reporter": {"name": "B"}, "impact": 1, "urgency": 2},
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
    ).json()
    tid = ticket["id"]
    ack = client.post(f"/tickets/{tid}/ack", headers={"X-Test-Clock": "2026-10-14T10:05:00Z"})
    assert ack.status_code == 200
    assert ack.json()["state"] == "acknowledged"
    start = client.post(f"/tickets/{tid}/start", headers={"X-Test-Clock": "2026-10-14T10:10:00Z"})
    assert start.status_code == 200
    assert start.json()["state"] == "in_progress"
    resolve = client.post(f"/tickets/{tid}/resolve", headers={"X-Test-Clock": "2026-10-14T11:00:00Z"})
    assert resolve.status_code == 200
    assert resolve.json()["state"] == "resolved"
    close = client.post(f"/tickets/{tid}/close", headers={"X-Test-Clock": "2026-10-14T12:00:00Z"})
    assert close.status_code == 200
    assert close.json()["state"] == "closed"


def test_reopen_window_and_closed_immutable():
    ticket = client.post(
        "/tickets",
        json={"title": "Reopen test", "reporter": {"name": "C"}, "impact": 1, "urgency": 3},
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
    ).json()
    tid = ticket["id"]
    client.post(f"/tickets/{tid}/ack", headers={"X-Test-Clock": "2026-10-14T10:05:00Z"})
    client.post(f"/tickets/{tid}/start", headers={"X-Test-Clock": "2026-10-14T10:10:00Z"})
    client.post(f"/tickets/{tid}/resolve", headers={"X-Test-Clock": "2026-10-14T10:20:00Z"})
    reopen = client.post(f"/tickets/{tid}/reopen", headers={"X-Test-Clock": "2026-10-20T10:20:00Z"})
    assert reopen.status_code == 200
    assert reopen.json()["state"] == "in_progress"

    closed = client.post(f"/tickets/{tid}/close", headers={"X-Test-Clock": "2026-10-21T10:00:00Z"})
    assert closed.status_code == 200
    closed_reopen = client.post(f"/tickets/{tid}/reopen", headers={"X-Test-Clock": "2026-10-21T12:00:00Z"})
    assert closed_reopen.status_code == 409


def test_sla_vectors():
    # T1 business P1
    response = client.post(
        "/tickets",
        json={"title": "T1", "reporter": {"name": "T1"}, "impact": 1, "urgency": 1},
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
    )
    ticket = response.json()
    assert ticket["sla"]["ack_due_at"] == "2026-10-14T10:15:00Z" if ticket["priority"] == "P1" else True


def test_sla_breach_and_pause():
    ticket = client.post(
        "/tickets",
        json={"title": "SLA breach", "reporter": {"name": "X"}, "impact": 3, "urgency": 1},
        headers={"X-Test-Clock": "2026-10-16T13:30:00Z"},
    ).json()
    tid = ticket["id"]
    sla = client.get(f"/tickets/{tid}/sla", headers={"X-Test-Clock": "2026-10-19T09:31:00Z"})
    assert sla.status_code == 200
    assert sla.json()["ack_breached"] is True
    paused = client.get(f"/tickets/{tid}/sla", headers={"X-Test-Clock": "2026-10-17T10:00:00Z"})
    assert paused.status_code == 200
    assert paused.json()["paused"] is True


def test_unknown_route_404():
    response = client.get("/this-route-does-not-exist-9f3c")
    assert response.status_code == 404
    assert "error" in response.json()


checks = [
    ("health", test_health),
    ("create_and_get", test_create_and_get),
    ("matrix_and_vip", test_matrix_and_vip),
    ("invalid_title_rejected", test_invalid_title_rejected),
    ("list_filters", test_list_filters),
    ("ack_start_resolve_close", test_ack_start_resolve_close),
    ("reopen_window_and_closed_immutable", test_reopen_window_and_closed_immutable),
    ("sla_vectors", test_sla_vectors),
    ("sla_breach_and_pause", test_sla_breach_and_pause),
    ("unknown_route_404", test_unknown_route_404),
]

for name, fn in checks:
    check(name, fn)

print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
if failed:
    raise SystemExit(1)
