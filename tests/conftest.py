import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    def _make_user(
        email: str,
        role: UserRole,
        password: str = "Password123!",
        is_active: bool = True,
        name: str = "Test User"
    ) -> User:
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _make_user


@pytest.fixture
def admin_user(make_user):
    return make_user("admin@test.com", UserRole.ADMIN, name="Admin User")


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(admin_user.email, role=admin_user.role.value)


@pytest.fixture
def faculty_user(make_user):
    return make_user("faculty@test.com", UserRole.FACULTY, name="Faculty User")


@pytest.fixture
def faculty_token(faculty_user):
    return create_access_token(faculty_user.email, role=faculty_user.role.value)


@pytest.fixture
def student_user(make_user):
    return make_user("student@test.com", UserRole.STUDENT, name="Student User")


@pytest.fixture
def student_token(student_user):
    return create_access_token(student_user.email, role=student_user.role.value)
