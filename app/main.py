import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.database import engine, Base, SessionLocal
from app.models import User, UserRole
from app.security import hash_password
from app.config import settings
from app.routers import auth, teams, proposals, progress, dashboard

logger = logging.getLogger("projecthub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)

    # Seed initial admin if none exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin = User(
                name="System Administrator",
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="ProjectHub",
    description="Role-based portal for managing college project teams",
    version="1.0.0",
    lifespan=lifespan
)


# Global exception handler to prevent leaking stack traces or SQL errors
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc
    logger.error("Unhandled server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )


# Root Landing Page
@app.get("/", response_class=HTMLResponse, tags=["General"], include_in_schema=False)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ProjectHub - College Project Portal</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #2563eb;
                --primary-hover: #1d4ed8;
                --bg: #0f172a;
                --card-bg: #1e293b;
                --border: #334155;
                --text: #f8fafc;
                --text-muted: #94a3b8;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 1rem; }
            .container { max-width: 900px; width: 100%; }
            .header { text-align: center; margin-bottom: 2.5rem; }
            .badge { display: inline-block; background: rgba(37, 99, 235, 0.2); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 500; margin-bottom: 1rem; }
            h1 { font-size: 2.75rem; font-weight: 700; margin-bottom: 0.75rem; letter-spacing: -0.025em; }
            p.lead { color: var(--text-muted); font-size: 1.15rem; max-width: 650px; margin: 0 auto; line-height: 1.6; }
            .actions { display: flex; justify-content: center; gap: 1rem; margin-top: 1.75rem; flex-wrap: wrap; }
            .btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.85rem 1.75rem; border-radius: 0.5rem; font-weight: 600; text-decoration: none; transition: all 0.2s; font-size: 1rem; }
            .btn-primary { background: var(--primary); color: white; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4); }
            .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
            .btn-secondary { background: var(--card-bg); color: var(--text); border: 1px solid var(--border); }
            .btn-secondary:hover { background: #283548; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; margin-top: 3rem; }
            .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; }
            .card-role { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-bottom: 0.5rem; }
            .role-admin { color: #f87171; }
            .role-faculty { color: #34d399; }
            .role-student { color: #60a5fa; }
            .card-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; }
            .card-desc { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem; line-height: 1.5; }
            .cred-box { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 0.375rem; padding: 0.75rem; font-family: monospace; font-size: 0.85rem; color: #cbd5e1; }
            .cred-item { margin-bottom: 0.25rem; }
            .footer { text-align: center; margin-top: 3rem; color: var(--text-muted); font-size: 0.85rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge">API v1.0 Operational</span>
                <h1>ProjectHub</h1>
                <p class="lead">A role-based university portal managing capstone project teams, proposals, faculty guide allocation, weekly milestones, and feedback.</p>
                <div class="actions">
                    <a href="/docs" class="btn btn-primary">
                        <span>🚀 Open Interactive Swagger UI</span>
                    </a>
                    <a href="/redoc" class="btn btn-secondary">
                        <span>📖 ReDoc API Docs</span>
                    </a>
                    <a href="/health" class="btn btn-secondary">
                        <span>🩺 Health Check</span>
                    </a>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-role role-admin">Administrator</div>
                    <div class="card-title">Coordinator Portal</div>
                    <div class="card-desc">Create users, allocate faculty guides to project teams, and review institution-wide aggregate analytics.</div>
                    <div class="cred-box">
                        <div class="cred-item"><strong>Email:</strong> admin@projecthub.edu</div>
                        <div class="cred-item"><strong>Pass:</strong> AdminPass123!</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-role role-faculty">Faculty</div>
                    <div class="card-title">Guide Dashboard</div>
                    <div class="card-desc">Review and approve project proposals, track weekly milestone progress, and assign marks with feedback.</div>
                    <div class="cred-box">
                        <div class="cred-item"><strong>Email:</strong> dr.sharma@projecthub.edu</div>
                        <div class="cred-item"><strong>Pass:</strong> FacultyPass123!</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-role role-student">Student</div>
                    <div class="card-title">Team Leader & Member</div>
                    <div class="card-desc">Form teams (2-4 members), submit proposals, log weekly completion percentages, and review guide evaluations.</div>
                    <div class="cred-box">
                        <div class="cred-item"><strong>Email:</strong> student1@projecthub.edu</div>
                        <div class="cred-item"><strong>Pass:</strong> StudentPass123!</div>
                    </div>
                </div>
            </div>

            <div class="footer">
                Built with FastAPI, SQLAlchemy 2.x, PostgreSQL/SQLite & Pydantic v2.
            </div>
        </div>
    </body>
    </html>
    """


# Health check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}



# Routers
app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(proposals.router)
app.include_router(progress.router)
app.include_router(dashboard.router)
