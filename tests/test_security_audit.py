import pytest
from app.models import UserRole, ProposalStatus
from app.security import create_access_token
from tests.conftest import auth_header

VALID_ABSTRACT_50 = "This is a valid abstract that contains at least fifty characters for proposal!"


def test_inactive_user_cannot_login(client, make_user):
    make_user("deactivated@test.com", UserRole.STUDENT, password="Password123!", is_active=False)

    response = client.post("/auth/login", data={"username": "deactivated@test.com", "password": "Password123!"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_inactive_user_token_is_blocked(client, make_user):
    user = make_user("deactivated_token@test.com", UserRole.STUDENT, is_active=False)
    # Generate token directly
    token = create_access_token(user.email, role="student")

    response = client.get("/users/me", headers=auth_header(token))
    assert response.status_code == 401
    assert "Inactive user account" in response.json()["detail"]


def test_tampered_token_returns_401(client, student_token):
    tampered_token = student_token[:-5] + "XXXXX"
    response = client.get("/users/me", headers=auth_header(tampered_token))
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_member_removal_by_leader(client, student_token, make_user):
    # Leader creates team
    r_team = client.post("/teams", json={"name": "Removal Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    # Add second student
    s2 = make_user("removable@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))

    # Leader removes member
    r_del = client.delete(f"/teams/{team_id}/members/{s2.id}", headers=auth_header(student_token))
    assert r_del.status_code == 200
    assert r_del.json()["message"] == "Member removed successfully"


def test_cannot_remove_leader_400(client, student_user, student_token):
    r_team = client.post("/teams", json={"name": "Leader Protect Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    r_del = client.delete(f"/teams/{team_id}/members/{student_user.id}", headers=auth_header(student_token))
    assert r_del.status_code == 400
    assert "leader" in r_del.json()["detail"].lower()


def test_cannot_remove_non_member_404(client, student_token, make_user):
    r_team = client.post("/teams", json={"name": "Non Member Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    outsider = make_user("outsider@test.com", UserRole.STUDENT)
    r_del = client.delete(f"/teams/{team_id}/members/{outsider.id}", headers=auth_header(student_token))
    assert r_del.status_code == 404
    assert "not a member" in r_del.json()["detail"].lower()


def test_changes_requested_and_resubmit_workflow(client, student_token, make_user, admin_token, faculty_user):
    r_team = client.post("/teams", json={"name": "Review Flow Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    s2 = make_user("rf_s2@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    # Submit proposal
    r_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Edge AI Diagnostics",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Edge compute for sensors.",
            "domain": "Embedded AI",
            "tech_stack": "TensorFlow Lite, C++"
        },
        headers=auth_header(student_token)
    )
    prop_id = r_prop.json()["id"]

    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]

    # 1. Request changes without comment -> 400
    r_no_cmt = client.patch(
        f"/proposals/{prop_id}/review",
        json={"decision": "CHANGES_REQUESTED", "comment": ""},
        headers=auth_header(fac_token)
    )
    assert r_no_cmt.status_code == 400
    assert "comment is required" in r_no_cmt.json()["detail"].lower()

    # 2. Request changes with comment -> 200 (status: CHANGES_REQUESTED)
    r_req = client.patch(
        f"/proposals/{prop_id}/review",
        json={"decision": "CHANGES_REQUESTED", "comment": "Please narrow the sensor scope."},
        headers=auth_header(fac_token)
    )
    assert r_req.status_code == 200
    assert r_req.json()["status"] == "CHANGES_REQUESTED"

    # 3. Leader edits proposal -> status automatically resets to SUBMITTED
    r_edit = client.put(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Edge AI Diagnostics for Temperature Sensors",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Narrowed scope to temperature sensor arrays.",
            "domain": "Embedded AI",
            "tech_stack": "TensorFlow Lite, C++"
        },
        headers=auth_header(student_token)
    )
    assert r_edit.status_code == 200
    assert r_edit.json()["status"] == "SUBMITTED"

    # 4. Guide now approves
    r_app = client.patch(
        f"/proposals/{prop_id}/review",
        json={"decision": "APPROVED", "comment": "Scope revision looks great."},
        headers=auth_header(fac_token)
    )
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "APPROVED"


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_database_get_db_generator():
    from app.database import get_db
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
