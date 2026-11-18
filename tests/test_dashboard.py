from app.models import UserRole
from tests.conftest import auth_header

VALID_ABSTRACT_50 = "This is a valid abstract that contains at least fifty characters for proposal!"


def test_admin_dashboard_counts(client, admin_token, make_user):
    # Create 3 students, 2 faculty
    make_user("stud1@test.com", UserRole.STUDENT)
    make_user("stud2@test.com", UserRole.STUDENT)
    make_user("stud3@test.com", UserRole.STUDENT)
    fac1 = make_user("fac1@test.com", UserRole.FACULTY)
    make_user("fac2@test.com", UserRole.FACULTY)

    # Student 1 creates team
    s1_login = client.post("/auth/login", data={"username": "stud1@test.com", "password": "Password123!"})
    s1_token = s1_login.json()["access_token"]
    r_team = client.post("/teams", json={"name": "Dashboard Team 1", "academic_year": "2026-2027"}, headers=auth_header(s1_token))
    team_id = r_team.json()["id"]

    # Assign guide
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": fac1.id}, headers=auth_header(admin_token))

    # Add second student and submit proposal
    client.post(f"/teams/{team_id}/members", json={"student_email": "stud2@test.com"}, headers=auth_header(s1_token))
    client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Solar Optimization Engine",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Solar efficiency prediction.",
            "domain": "CleanTech",
            "tech_stack": "Python, Scikit-learn"
        },
        headers=auth_header(s1_token)
    )

    response = client.get("/dashboard", headers=auth_header(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["total_students"] == 3
    assert data["total_faculty"] == 2
    assert data["total_teams"] == 1
    assert data["unassigned_teams"] == 0
    assert data["proposals_by_status"]["SUBMITTED"] == 1


def test_student_sees_only_own_team_info(client, student_token, make_user, admin_token, faculty_user):
    # Leader creates team
    r_team = client.post("/teams", json={"name": "Alpha Pioneers", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]

    # Add member, guide, submit proposal
    s2 = make_user("s2_dash@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    r_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Bioinformatics Pipeline",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Fast genome sequence alignment.",
            "domain": "Bioinformatics",
            "tech_stack": "Nextflow, Python"
        },
        headers=auth_header(student_token)
    )
    prop_id = r_prop.json()["id"]

    # Guide approves
    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]
    client.patch(f"/proposals/{prop_id}/review", json={"decision": "APPROVED", "comment": "Approved."}, headers=auth_header(fac_token))

    # Student posts progress
    r_prog = client.post(
        f"/teams/{team_id}/progress",
        json={"week_number": 1, "description": "Completed pipeline parser", "completion_percent": 35},
        headers=auth_header(student_token)
    )
    prog_id = r_prog.json()["id"]

    # Guide gives feedback
    client.post(f"/progress/{prog_id}/feedback", json={"comments": "Outstanding progress!", "marks": 95}, headers=auth_header(fac_token))

    # Student checks dashboard
    response = client.get("/dashboard", headers=auth_header(student_token))
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "student"
    assert data["team_name"] == "Alpha Pioneers"
    assert data["guide_name"] == faculty_user.name
    assert data["proposal_status"] == "APPROVED"
    assert data["latest_completion_percent"] == 35
    assert data["last_feedback_comment"] == "Outstanding progress!"


def test_faculty_dashboard(client, admin_token, faculty_user, student_token, make_user):
    # Create team with guide
    r_team = client.post("/teams", json={"name": "Faculty Guided Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r_team.json()["id"]
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    # Add second student and submit proposal (remains in SUBMITTED)
    s2 = make_user("m2_fac@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))
    client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Pending Proposal Review",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Needs review from faculty.",
            "domain": "AI",
            "tech_stack": "PyTorch"
        },
        headers=auth_header(student_token)
    )

    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]

    response = client.get("/dashboard", headers=auth_header(fac_token))
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "faculty"
    assert data["assigned_teams"] == 1
    assert data["pending_reviews"] == 1
    assert data["teams_without_recent_progress"] == 1
