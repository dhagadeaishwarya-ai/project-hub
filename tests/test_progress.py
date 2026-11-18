import pytest
from app.models import UserRole
from tests.conftest import auth_header

VALID_ABSTRACT_50 = "This is a valid abstract that contains at least fifty characters for proposal!"


def create_approved_team(client, student_token, make_user, admin_token, faculty_user):
    # Leader creates team
    r_team = client.post("/teams", json={"name": "Progress Pioneers", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    # Add second student
    s2 = make_user("member2_prog@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))

    # Admin assigns guide
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    # Submit proposal
    r_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Quantum Algorithm Simulator",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Quantum simulation on classical clusters.",
            "domain": "Quantum Computing",
            "tech_stack": "Qiskit, Python, C++"
        },
        headers=auth_header(student_token)
    )
    prop_id = r_prop.json()["id"]

    # Guide approves
    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]
    client.patch(
        f"/proposals/{prop_id}/review",
        json={"decision": "APPROVED", "comment": "Approved for development."},
        headers=auth_header(fac_token)
    )

    return team_id, fac_token


def test_progress_blocked_before_approval(client, student_token, make_user):
    r_team = client.post("/teams", json={"name": "Unapproved Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    s2 = make_user("m2_unapp@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))

    # No approved proposal
    response = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Week 1 work", "completion_percent": 10},
        headers=auth_header(student_token)
    )
    assert response.status_code == 400
    assert "approved" in response.json()["detail"].lower()


@pytest.mark.parametrize("percent, expected_status", [
    (-1, 422),
    (0, 201),
    (100, 201),
    (101, 422)
])
def test_completion_boundaries(client, student_token, make_user, admin_token, faculty_user, percent, expected_status):
    team_id, _ = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    payload = {
        "week_number": 1,
        "description": f"Testing completion {percent}%",
        "completion_percent": percent
    }
    response = client.post(f"/teams/{team_id}/progress", json=payload, headers=auth_header(student_token))
    assert response.status_code == expected_status


def test_percentage_cannot_decrease(client, student_token, make_user, admin_token, faculty_user):
    team_id, _ = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    # Week 1: 30%
    r1 = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Week 1", "completion_percent": 30},
        headers=auth_header(student_token)
    )
    assert r1.status_code == 201

    # Week 2: 25% (decrease -> should be rejected with 400)
    r2 = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 2, "description": "Week 2", "completion_percent": 25},
        headers=auth_header(student_token)
    )
    assert r2.status_code == 400
    assert "cannot decrease" in r2.json()["detail"].lower()


@pytest.mark.parametrize("week, expected_status", [
    (0, 422),
    (1, 201),
    (20, 201),
    (21, 422)
])
def test_week_boundaries(client, student_token, make_user, admin_token, faculty_user, week, expected_status):
    team_id, _ = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    payload = {
        "week_number": week,
        "description": f"Testing week {week}",
        "completion_percent": 50
    }
    response = client.post(f"/teams/{team_id}/progress", json=payload, headers=auth_header(student_token))
    assert response.status_code == expected_status


def test_guide_adds_feedback(client, student_token, make_user, admin_token, faculty_user):
    team_id, fac_token = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    # Student posts week 1
    r_prog = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Initial literature review and environment setup", "completion_percent": 15},
        headers=auth_header(student_token)
    )
    prog_id = r_prog.json()["id"]

    # Guide adds feedback
    r_feed = client.post(
        f"/progress/{prog_id}/feedback",
        json={"comments": "Solid start on the background research. Proceed with baseline model.", "marks": 85},
        headers=auth_header(fac_token)
    )
    assert r_feed.status_code == 201
    data = r_feed.json()
    assert data["marks"] == 85
    assert "Solid start" in data["comments"]

    # Progress list includes the feedback
    r_list = client.get(f"/teams/{team_id}/progress", headers=auth_header(student_token))
    assert r_list.status_code == 200
    assert len(r_list.json()[0]["feedbacks"]) == 1


@pytest.mark.parametrize("marks, expected_status", [
    (-1, 422),
    (0, 201),
    (100, 201),
    (101, 422)
])
def test_marks_boundaries(client, student_token, make_user, admin_token, faculty_user, marks, expected_status):
    team_id, fac_token = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    r_prog = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Week 1 work", "completion_percent": 20},
        headers=auth_header(student_token)
    )
    prog_id = r_prog.json()["id"]

    response = client.post(
        f"/progress/{prog_id}/feedback",
        json={"comments": f"Mark boundary test with {marks}", "marks": marks},
        headers=auth_header(fac_token)
    )
    assert response.status_code == expected_status


def test_student_cannot_add_feedback_403(client, student_token, make_user, admin_token, faculty_user):
    team_id, _ = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    r_prog = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Week 1", "completion_percent": 10},
        headers=auth_header(student_token)
    )
    prog_id = r_prog.json()["id"]

    response = client.post(
        f"/progress/{prog_id}/feedback",
        json={"comments": "Student attempting to grade own team", "marks": 100},
        headers=auth_header(student_token)
    )
    assert response.status_code == 403


def test_student_cannot_view_another_team_progress_403(client, student_token, make_user, admin_token, faculty_user):
    team_id, _ = create_approved_team(client, student_token, make_user, admin_token, faculty_user)

    # Different student
    s_other = make_user("stranger@test.com", UserRole.STUDENT)
    s_other_login = client.post("/auth/login", data={"username": s_other.email, "password": "Password123!"})
    s_other_token = s_other_login.json()["access_token"]

    response = client.get(f"/teams/{team_id}/progress", headers=auth_header(s_other_token))
    assert response.status_code == 403
    assert "Students may only view their own team" in response.json()["detail"]
