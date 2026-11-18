from app.models import UserRole
from tests.conftest import auth_header


def test_create_team(client, student_token):
    payload = {"name": "Alpha Squad", "academic_year": "2026-2027"}
    response = client.post("/teams", json=payload, headers=auth_header(student_token))
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alpha Squad"
    assert len(data["members"]) == 1
    assert data["members"][0]["email"] == "student@test.com"


def test_student_already_in_team_400(client, student_token):
    # First creation succeeds
    client.post("/teams", json={"name": "Alpha Squad", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    # Second creation fails with 400
    response = client.post(
        "/teams",
        json={"name": "Beta Squad", "academic_year": "2026-2027"},
        headers=auth_header(student_token)
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]


def test_team_size_boundaries(client, student_token, make_user):
    # Leader creates team (size 1)
    res = client.post("/teams", json={"name": "Boundary Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = res.json()["id"]

    # Create 4 additional students
    s2 = make_user("s2@test.com", UserRole.STUDENT)
    s3 = make_user("s3@test.com", UserRole.STUDENT)
    s4 = make_user("s4@test.com", UserRole.STUDENT)
    s5 = make_user("s5@test.com", UserRole.STUDENT)

    # Adding members 2, 3, 4 succeeds (total size reaches 4)
    r2 = client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))
    assert r2.status_code == 200
    assert len(r2.json()["members"]) == 2

    r3 = client.post(f"/teams/{team_id}/members", json={"student_email": s3.email}, headers=auth_header(student_token))
    assert r3.status_code == 200
    assert len(r3.json()["members"]) == 3

    r4 = client.post(f"/teams/{team_id}/members", json={"student_email": s4.email}, headers=auth_header(student_token))
    assert r4.status_code == 200
    assert len(r4.json()["members"]) == 4

    # Adding 5th member fails with 400
    r5 = client.post(f"/teams/{team_id}/members", json={"student_email": s5.email}, headers=auth_header(student_token))
    assert r5.status_code == 400
    assert "cannot exceed 4 members" in r5.json()["detail"]


def test_non_leader_adding_member_403(client, student_token, make_user):
    res = client.post("/teams", json={"name": "Leader Only Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = res.json()["id"]

    # Add s2 as member
    s2 = make_user("member@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))

    # s2 tries to add s3
    s3 = make_user("other@test.com", UserRole.STUDENT)
    s2_login = client.post("/auth/login", data={"username": s2.email, "password": "Password123!"})
    s2_token = s2_login.json()["access_token"]

    r = client.post(f"/teams/{team_id}/members", json={"student_email": s3.email}, headers=auth_header(s2_token))
    assert r.status_code == 403
    assert "leader" in r.json()["detail"].lower()


def test_admin_assigns_guide(client, admin_token, student_token, faculty_user):
    res = client.post("/teams", json={"name": "Guided Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = res.json()["id"]

    response = client.put(
        f"/teams/{team_id}/guide",
        json={"faculty_id": faculty_user.id},
        headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["guide_id"] == faculty_user.id
    assert data["guide"]["email"] == faculty_user.email


def test_student_cannot_assign_guide_403(client, student_token, faculty_user):
    res = client.post("/teams", json={"name": "Student Guide Attempt", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = res.json()["id"]

    response = client.put(
        f"/teams/{team_id}/guide",
        json={"faculty_id": faculty_user.id},
        headers=auth_header(student_token)
    )
    assert response.status_code == 403


def test_student_cannot_view_another_team_403(client, student_token, make_user):
    res = client.post("/teams", json={"name": "Team One", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_1_id = res.json()["id"]

    # Student 2 from different team
    s2 = make_user("otherstudent@test.com", UserRole.STUDENT)
    s2_login = client.post("/auth/login", data={"username": s2.email, "password": "Password123!"})
    s2_token = s2_login.json()["access_token"]

    response = client.get(f"/teams/{team_1_id}", headers=auth_header(s2_token))
    assert response.status_code == 403
    assert "Students may only view their own team" in response.json()["detail"]
