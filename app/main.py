import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
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
