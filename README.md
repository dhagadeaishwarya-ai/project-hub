# ProjectHub: College Project-Team Management API

ProjectHub is a role-based RESTful API portal designed for colleges and universities to manage final-year capstone project teams: team formation, proposal approvals, faculty guide allocation, weekly milestone progress logging, and faculty feedback with grading.

---

## 1. Tech Stack

- **Runtime & Framework**: Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Data & ORM**: [SQLAlchemy 2.x](https://www.sqlalchemy.org/) ORM, PostgreSQL (`psycopg2-binary`) for runtime / SQLite for local development
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/) with `pydantic[email]` & `pydantic-settings`
- **Security & Auth**: JWT (via `python-jose`), password hashing (via `passlib[bcrypt]`), OAuth2 Password Bearer flow
- **Testing**: [pytest](https://pytest.org/), `pytest-cov`, `httpx` with in-memory SQLite (`StaticPool`)

---

## 2. Project Architecture & Directory Map

```
project_hub/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Pydantic Settings & environment validation
│   ├── database.py          # SQLAlchemy engine, declarative Base, session generator
│   ├── deps.py              # Auth & role-based access control dependencies
│   ├── main.py              # FastAPI application, lifespan handler, static files mount
│   ├── models.py            # SQLAlchemy 2.x domain models & association table
│   ├── notifications.py     # In-memory mock notification dispatcher
│   ├── schemas.py           # Pydantic v2 schemas and Field validators
│   ├── security.py          # Bcrypt hashing and JWT token encode/decode
│   ├── static/              # Complete Frontend Web Portal (HTML5, CSS3, Vanilla JS)
│   │   ├── index.html       # Single-Page Web Application UI & Modals
│   │   ├── css/styles.css   # Modern Dark/Light Design System
│   │   └── js/
│   │       ├── api.js       # Typed Async API Client with JWT Auth
│   │       └── app.js       # State Store, Role Routing, Multi-course Filters
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Login, user creation, current user profile
│       ├── dashboard.py     # Aggregated SQL statistics scoped by user role
│       ├── progress.py      # Weekly progress milestones and faculty feedback
│       ├── proposals.py     # Project proposals & approval state machine
│       └── teams.py         # Team creation, membership, guide allocation
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # SQLite in-memory fixtures, TestClient, mock tokens
│   ├── test_auth.py         # Login, tokens, user permissions, password boundaries
│   ├── test_dashboard.py    # SQL aggregation and role-scoped dashboard views
│   ├── test_progress.py     # Milestone percent flow, boundaries, feedback grades
│   ├── test_proposals.py    # Proposal lifecycle, state transitions, notifications
│   ├── test_security.py     # Hashing verification and token expiry tests
│   ├── test_security_audit.py # Inactive user, tampered tokens, member deletions
│   └── test_teams.py        # Team creation, size boundaries (2-4), guide assignment
├── .env.example             # Template environment variables
├── .gitignore               # Ignored local files, bytecode, sqlite, coverage
├── requirements.txt         # Pinned compatible project dependencies
├── seed.py                  # Idempotent database seed script
├── SECURITY_AUDIT.md        # Comprehensive security and route audit report
├── TASKS_PROGRESS.txt       # Stage-by-stage implementation checklist
└── README.md                # Project documentation and demo walkthrough
```

---

## 3. Getting Started

### 3.1 Prerequisites
- Python 3.11 or higher installed on your operating system.
- Git installed.

### 3.2 Setup Environment
```bash
# 1. Clone the repository
git clone <repo-url> project_hub
cd project_hub

# 2. Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 3. Install pinned dependencies
python -m pip install -r requirements.txt

# 4. Configure environment variables
# Copy .env.example to .env
cp .env.example .env
```

### 3.3 Database Setup
By default, `.env` uses SQLite (`sqlite:///./projecthub.db`) for immediate out-of-the-box local development. To use PostgreSQL:
1. Ensure PostgreSQL is running.
2. Create database: `createdb projecthub`
3. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/projecthub
   ```

### 3.4 Seed Demo Data
Run the idempotent seed script to populate users, teams, proposals, and progress updates:
```bash
python seed.py
```

### 3.5 Run the Application
```bash
python -m uvicorn app.main:app --reload
```
*(Note: On Windows systems with Application Control/AppLocker policies, invoke via `python -m uvicorn` rather than `uvicorn.exe` directly).*
Open your browser at:
- **Web Application Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 4. Running Tests & Code Coverage

Tests run against an isolated in-memory SQLite database (`StaticPool`) through FastAPI's dependency overrides, requiring zero external database configuration.

```bash
# Run all tests
python -m pytest

# Run tests with code coverage report
python -m pytest --cov=app --cov-report=term-missing
```
The test suite includes **50+ comprehensive unit, boundary, and security tests** with **90% code coverage across the entire `app` package**.

---

## 5. Route Reference

| Method | Path | Allowed Roles | Description |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Authenticates credentials and returns a signed JWT |
| `POST` | `/users` | `admin` | Create new users with role validation (409 on duplicate) |
| `GET` | `/users/me` | Any Authenticated | Retrieve current user profile (excludes password) |
| `POST` | `/teams` | `student` | Creates a new team with course specification; creator becomes leader & 1st member |
| `GET` | `/teams` | Any Authenticated | Scoped visibility (Admin: all, Faculty: guided, Student: own); optional `?course=` filter |
| `GET` | `/teams/meta/courses` | Public | List all unique course names across all registered teams |
| `GET` | `/teams/{id}` | Any Authenticated | View team details with ownership verification |
| `POST` | `/teams/{id}/members` | `student` (Leader) | Add student to team (enforces 1 team per student per course, max 4 members) |
| `DELETE` | `/teams/{id}/members/{user_id}` | `student` (Leader) | Remove member (leader cannot be removed) |
| `PUT` | `/teams/{id}/guide` | `admin` | Assign active faculty guide to a team (guides can lead multiple teams/courses) |
| `POST` | `/teams/{id}/proposal` | `student` (Leader) | Submit project proposal (requires 2-4 team members) |
| `GET` | `/teams/{id}/proposal` | Team / Guide / Admin | View team proposal |
| `PUT` | `/teams/{id}/proposal` | `student` (Leader) | Edit proposal (resets `CHANGES_REQUESTED` to `SUBMITTED`) |
| `PATCH` | `/proposals/{id}/review` | `faculty` (Guide) | Review proposal (`APPROVED` or `CHANGES_REQUESTED`) |
| `POST` | `/teams/{id}/progress` | `student` (Member) | Post weekly progress update (requires `APPROVED` proposal) |
| `GET` | `/teams/{id}/progress` | Team / Guide / Admin | List team progress updates with nested faculty feedback |
| `POST` | `/progress/{id}/feedback` | `faculty` (Guide) | Provide written feedback and optional marks (0-100) |
| `GET` | `/dashboard` | Any Authenticated | Retrieve role-specific aggregate statistics via SQL queries |
| `GET` | `/health` | Public | Service health verification endpoint |

---

## 6. Business Validation Rules

| Entity / Field | Validation Rule | Enforced Layer |
|---|---|---|
| **Password** | Min 8 characters | Pydantic Schema |
| **Team Name** | 3 to 50 characters | Pydantic Schema |
| **Course** | Specified per team (e.g., CS501 Capstone, CS502 Web3, CS503 Embedded) | Pydantic Schema + Column |
| **Team Size** | 2 to 4 members (including leader) to submit a proposal; max 4 members | Schema & Router Helper |
| **Membership Rule** | A student may belong to multiple teams across **different courses**, but only ONE team per course | Router Check (`is_student_in_course_team`) |
| **Guide Allocation** | A faculty guide may manage multiple project teams across different courses | Router Logic + DB Foreign Key |
| **Course Filtering** | Filter teams by course in API (`?course=...`) and in UI dropdown | Router SQL Filter + Front-End Store |
| **Proposal Title** | 5 to 150 characters | Pydantic Schema |
| **Proposal Abstract** | Minimum 50 characters | Pydantic Schema |
| **Proposal Lifecycle** | `SUBMITTED` -> `APPROVED` or `CHANGES_REQUESTED`; `CHANGES_REQUESTED` -> `SUBMITTED` on edit; `APPROVED` is permanently locked | Transition State Machine Dictionary |
| **Week Number** | Integers 1 to 20; unique per team | Schema + SQL UniqueConstraint |
| **Completion Percent**| Integers 0 to 100; must not decrease vs previous updates | Schema + Router Helper |
| **Faculty Marks** | Integers 0 to 100 (optional) | Pydantic Schema |

---

## 7. Mock Notification System

ProjectHub implements a clean mock notification subsystem in [app/notifications.py](file:///c:/Users/AISHWARYA/OneDrive/Desktop/Sem5/AISD/project_hub/app/notifications.py). Whenever significant events occur (such as proposal submission, review outcome decisions, or faculty progress feedback), the `notify(to_email, subject, message)` helper:
1. Records a structured notification entry in an in-memory `SENT` list.
2. Logs an informational log entry (`logger.info`).
3. Does not block execution or require an external SMTP server.

---

## 8. Seed Demo Credentials

| Role | Name | Email | Password | Assigned Context |
|---|---|---|---|---|
| **Admin** | System Administrator | `admin@projecthub.edu` | `AdminPass123!` | System-wide Coordinator |
| **Faculty** | Dr. Ramesh Sharma | `dr.sharma@projecthub.edu` | `FacultyPass123!` | Guide of Team 1 |
| **Faculty** | Dr. Priya Patel | `dr.patel@projecthub.edu` | `FacultyPass123!` | Guide of Team 2 |
| **Student** | Aarav Mehta | `student1@projecthub.edu` | `StudentPass123!` | Leader of Team 1 (Autonomous Rover AI) |
| **Student** | Diya Sen | `student2@projecthub.edu` | `StudentPass123!` | Member of Team 1 |
| **Student** | Rohan Gupta | `student3@projecthub.edu` | `StudentPass123!` | Member of Team 1 |
| **Student** | Ananya Iyer | `student4@projecthub.edu` | `StudentPass123!` | Leader of Team 2 (Decentralized MedRecords) |
| **Student** | Kabir Verma | `student5@projecthub.edu` | `StudentPass123!` | Member of Team 2 |
| **Student** | Meera Nair | `student6@projecthub.edu` | `StudentPass123!` | Member of Team 2 |

---

## 9. 10-Step Interactive Demo Walkthrough (Swagger UI)

Navigate to `http://127.0.0.1:8000/docs` to execute the following walkthrough:

1. **Check Health**:
   - Execute `GET /health`. Expect `{"status": "ok"}`.
2. **Authorize as Admin**:
   - Click the green **Authorize** button at top right.
   - Enter `admin@projecthub.edu` and `AdminPass123!`. Click **Authorize**.
3. **Inspect Admin Dashboard**:
   - Execute `GET /dashboard`.
   - Verify aggregate counts: `total_students: 6`, `total_faculty: 2`, `total_teams: 2`, and proposals breakdown.
4. **Authorize as Student 1 (Aarav Mehta - Leader of Team 1)**:
   - Click **Authorize** -> Logout -> Enter `student1@projecthub.edu` and `StudentPass123!`.
5. **View Own Team & Proposal**:
   - Execute `GET /teams`. Observe that only Team 1 (`Autonomous Rover AI`) is returned.
   - Execute `GET /teams/1/progress`. Observe 3 weeks of logged progress with faculty marks (85, 90, 92).
6. **Submit Week 4 Progress**:
   - Execute `POST /teams/1/progress` with:
     ```json
     {
       "week_number": 4,
       "description": "Completed end-to-end integration tests on simulated course.",
       "completion_percent": 95,
       "deliverable_url": "https://rover.projecthub.edu/demo/week4"
     }
     ```
   - Expect `201 Created` with `completion_percent: 95`.
7. **Demonstrate Percentage Validation Rejection (400)**:
   - Attempt `POST /teams/1/progress` with a decreased completion percent:
     ```json
     {
       "week_number": 5,
       "description": "Hardware rollback",
       "completion_percent": 70
     }
     ```
   - Expect `400 Bad Request` with message: *"Completion percent (70%) cannot decrease versus previous update (95% in week 4)"*.
8. **Demonstrate Cross-Team Ownership Protection (403 Forbidden)**:
   - Attempt `GET /teams/2` while authenticated as Student 1.
   - Expect `403 Forbidden` with message: *"Students may only view their own team"*.
9. **Authorize as Faculty Guide (Dr. Ramesh Sharma)**:
   - Authorize with `dr.sharma@projecthub.edu` and `FacultyPass123!`.
   - Execute `GET /dashboard`. Verify `assigned_teams: 1`.
10. **Grade Week 4 Progress**:
    - Execute `POST /progress/4/feedback` with:
      ```json
      {
        "comments": "Superb final integration testing. You are cleared for the final evaluation.",
        "marks": 96
      }
      ```
    - Expect `201 Created` with marks 96. Notice the mock notification recorded for the team leader.

---

## 10. Future Work (Scoped Beyond 3-Day Plan)

The following capabilities were intentionally excluded from the 3-day MVP scope and are slated for future releases:
- **Review Scheduling & Calendaring**: Automated slot booking for mid-term project defense presentations.
- **Individual Contribution Tracking**: Git commit telemetry, per-student task allocation, and individual viva marks.
- **AI-Powered Similarity Detection**: Automated semantic analysis of project abstracts against past semester projects using LLM embeddings.
- **GitHub & GitLab Webhooks**: Automated repository synchronization, commit tracking, and PR review milestones.
- **Production Notification Integrations**: Integration with SendGrid / Amazon SES for transactional emails and Slack webhooks for team notifications.
- **Final Report Archiving**: S3-compatible cloud storage for PDF final reports with digital signature verification.
- **Alembic Database Migrations**: Automated schema upgrade and downgrade migration scripts for evolving production databases.
- **Single Page Application (SPA) Frontend**: Modern web frontend built with React / Next.js or Vue.js.
- **Docker & Kubernetes Deployment**: Dockerfile containerization and Helm chart deployment manifests.
