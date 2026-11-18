from app.models import UserRole
from app.notifications import SENT, clear_sent
from tests.conftest import auth_header

VALID_ABSTRACT_50 = "This is a valid abstract that contains at least fifty chars!"


def setup_team_with_two_members(client, student_token, make_user):
    # Leader creates team
    r = client.post("/teams", json={"name": "Proposal Team", "academic_year": "2026-2027"}, headers=auth_header(student_token))
    team_id = r.json()["id"]

    # Add second member to satisfy 2-4 members rule
    s2 = make_user("member2@test.com", UserRole.STUDENT)
    client.post(f"/teams/{team_id}/members", json={"student_email": s2.email}, headers=auth_header(student_token))
    return team_id


def test_submit_proposal_success(client, student_token, make_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)

    payload = {
        "title": "Smart Campus Navigation",
        "abstract": VALID_ABSTRACT_50,
        "problem_statement": "Students struggle to navigate the campus buildings.",
        "domain": "IoT & Mobile",
        "tech_stack": "FastAPI, React Native, Bluetooth Beacons"
    }
    response = client.post(f"/teams/{team_id}/proposal", json=payload, headers=auth_header(student_token))
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Smart Campus Navigation"
    assert data["status"] == "SUBMITTED"
    assert data["team_id"] == team_id


def test_duplicate_proposal_400(client, student_token, make_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)

    payload = {
        "title": "Smart Campus Navigation",
        "abstract": VALID_ABSTRACT_50,
        "problem_statement": "Students struggle to navigate the campus buildings.",
        "domain": "IoT & Mobile",
        "tech_stack": "FastAPI, React Native"
    }
    client.post(f"/teams/{team_id}/proposal", json=payload, headers=auth_header(student_token))
    response = client.post(f"/teams/{team_id}/proposal", json=payload, headers=auth_header(student_token))
    assert response.status_code == 400
    assert "already been submitted" in response.json()["detail"]


def test_title_length_boundaries(client, student_token, make_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)

    base_payload = {
        "abstract": VALID_ABSTRACT_50,
        "problem_statement": "Problem statement description",
        "domain": "AI",
        "tech_stack": "Python"
    }

    # Title 4 chars -> 422
    p4 = {**base_payload, "title": "1234"}
    assert client.post(f"/teams/{team_id}/proposal", json=p4, headers=auth_header(student_token)).status_code == 422

    # Title 151 chars -> 422
    p151 = {**base_payload, "title": "A" * 151}
    assert client.post(f"/teams/{team_id}/proposal", json=p151, headers=auth_header(student_token)).status_code == 422

    # Title 5 chars -> 201
    p5 = {**base_payload, "title": "12345"}
    res5 = client.post(f"/teams/{team_id}/proposal", json=p5, headers=auth_header(student_token))
    assert res5.status_code == 201


def test_abstract_boundary_49_chars_422(client, student_token, make_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)

    payload = {
        "title": "Valid Title Here",
        "abstract": "A" * 49,  # 49 chars (invalid low boundary)
        "problem_statement": "Problem statement description",
        "domain": "AI",
        "tech_stack": "Python"
    }
    response = client.post(f"/teams/{team_id}/proposal", json=payload, headers=auth_header(student_token))
    assert response.status_code == 422


def test_guide_approves_and_sent_notification(client, student_token, make_user, admin_token, faculty_user):
    clear_sent()
    team_id = setup_team_with_two_members(client, student_token, make_user)

    # Assign guide
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    # Submit proposal
    res_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Autonomous Drone Surveillance",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Security inspection needs automation.",
            "domain": "Robotics",
            "tech_stack": "ROS, OpenCV"
        },
        headers=auth_header(student_token)
    )
    proposal_id = res_prop.json()["id"]

    # Guide logs in
    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]

    # Guide approves
    initial_sent_count = len(SENT)
    res_review = client.patch(
        f"/proposals/{proposal_id}/review",
        json={"decision": "APPROVED", "comment": "Excellent project scope and objectives."},
        headers=auth_header(fac_token)
    )
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "APPROVED"
    assert len(SENT) > initial_sent_count


def test_non_guide_faculty_403(client, student_token, make_user, admin_token, faculty_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    res_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Machine Learning Diagnostic System",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Early diagnosis is crucial for health.",
            "domain": "Healthcare",
            "tech_stack": "PyTorch, FastAPI"
        },
        headers=auth_header(student_token)
    )
    proposal_id = res_prop.json()["id"]

    # Other faculty
    other_fac = make_user("otherfaculty@test.com", UserRole.FACULTY)
    other_login = client.post("/auth/login", data={"username": other_fac.email, "password": "Password123!"})
    other_token = other_login.json()["access_token"]

    response = client.patch(
        f"/proposals/{proposal_id}/review",
        json={"decision": "APPROVED", "comment": "Good idea"},
        headers=auth_header(other_token)
    )
    assert response.status_code == 403
    assert "Only the assigned faculty guide" in response.json()["detail"]


def test_editing_after_approval_400(client, student_token, make_user, admin_token, faculty_user):
    team_id = setup_team_with_two_members(client, student_token, make_user)
    client.put(f"/teams/{team_id}/guide", json={"faculty_id": faculty_user.id}, headers=auth_header(admin_token))

    res_prop = client.post(
        f"/teams/{team_id}/proposal",
        json={
            "title": "Blockchain Credentials",
            "abstract": VALID_ABSTRACT_50,
            "problem_statement": "Verifiable university degrees.",
            "domain": "Web3",
            "tech_stack": "Solidity, Ethereum"
        },
        headers=auth_header(student_token)
    )
    proposal_id = res_prop.json()["id"]

    # Guide approves
    fac_login = client.post("/auth/login", data={"username": faculty_user.email, "password": "Password123!"})
    fac_token = fac_login.json()["access_token"]
    client.patch(
        f"/proposals/{proposal_id}/review",
        json={"decision": "APPROVED", "comment": "Approved!"},
        headers=auth_header(fac_token)
    )

    # Attempt to edit after approval
    edit_payload = {
        "title": "Changed Title Post Approval",
        "abstract": VALID_ABSTRACT_50,
        "problem_statement": "Changed statement.",
        "domain": "Web3",
        "tech_stack": "Solidity"
    }
    res_edit = client.put(f"/teams/{team_id}/proposal", json=edit_payload, headers=auth_header(student_token))
    assert res_edit.status_code == 400
    assert "locked" in res_edit.json()["detail"].lower()
