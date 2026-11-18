from tests.conftest import auth_header


def test_login_success(client, make_user):
    make_user("alice@student.edu", role="student", password="Password123!")

    response = client.post(
        "/auth/login",
        data={"username": "alice@student.edu", "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_401(client, make_user):
    make_user("alice@student.edu", role="student", password="Password123!")

    response = client.post(
        "/auth/login",
        data={"username": "alice@student.edu", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_no_token_401(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_student_creating_user_403(client, student_token):
    payload = {
        "email": "newbie@student.edu",
        "name": "New Student",
        "password": "Password123!",
        "role": "student"
    }
    response = client.post("/users", json=payload, headers=auth_header(student_token))
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]


def test_password_length_boundary_7_chars_422(client, admin_token):
    payload = {
        "email": "shortpw@student.edu",
        "name": "Short PW",
        "password": "1234567",  # 7 chars (boundary below 8)
        "role": "student"
    }
    response = client.post("/users", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 422


def test_password_length_boundary_8_chars_201(client, admin_token):
    payload = {
        "email": "validpw@student.edu",
        "name": "Valid PW",
        "password": "12345678",  # 8 chars (valid min)
        "role": "student"
    }
    response = client.post("/users", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "validpw@student.edu"
    assert "hashed_password" not in data
    assert "password" not in data
