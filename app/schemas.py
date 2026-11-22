from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import UserRole, ProposalStatus


# ============================================================================
# User Schemas
# ============================================================================
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Auth Schemas
# ============================================================================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# Team Schemas
# ============================================================================
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    academic_year: str = Field(..., min_length=1, max_length=20)
    course: str = Field(default="CS501 - Capstone Project", min_length=2, max_length=100)


class TeamMemberAdd(BaseModel):
    student_email: EmailStr


class TeamGuideAssign(BaseModel):
    faculty_id: int


class TeamRead(BaseModel):
    id: int
    name: str
    academic_year: str
    course: str
    leader_id: int
    guide_id: Optional[int] = None
    leader: Optional[UserRead] = None
    guide: Optional[UserRead] = None
    members: List[UserRead] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Proposal Schemas
# ============================================================================
class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    abstract: str = Field(..., min_length=50)
    problem_statement: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1, max_length=100)
    tech_stack: str = Field(..., min_length=1, max_length=255)


class ProposalUpdate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    abstract: str = Field(..., min_length=50)
    problem_statement: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1, max_length=100)
    tech_stack: str = Field(..., min_length=1, max_length=255)


class ProposalReview(BaseModel):
    decision: ProposalStatus
    comment: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: ProposalStatus) -> ProposalStatus:
        if v not in (ProposalStatus.APPROVED, ProposalStatus.CHANGES_REQUESTED):
            raise ValueError("Decision must be either APPROVED or CHANGES_REQUESTED")
        return v


class ProposalRead(BaseModel):
    id: int
    team_id: int
    title: str
    abstract: str
    problem_statement: str
    domain: str
    tech_stack: str
    status: ProposalStatus
    faculty_comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Progress and Feedback Schemas
# ============================================================================
class FeedbackCreate(BaseModel):
    comments: str = Field(..., min_length=1)
    marks: Optional[int] = Field(default=None, ge=0, le=100)


class FeedbackRead(BaseModel):
    id: int
    progress_update_id: int
    faculty_id: int
    comments: str
    marks: Optional[int] = None
    created_at: datetime
    faculty: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


class ProgressUpdateCreate(BaseModel):
    week_number: int = Field(..., ge=1, le=20)
    description: str = Field(..., min_length=1)
    completion_percent: int = Field(..., ge=0, le=100)
    deliverable_url: Optional[str] = None

    @field_validator("deliverable_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("deliverable_url must start with http:// or https://")
        return v


class ProgressUpdateRead(BaseModel):
    id: int
    team_id: int
    week_number: int
    description: str
    completion_percent: int
    deliverable_url: Optional[str] = None
    created_at: datetime
    feedbacks: List[FeedbackRead] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Dashboard Schemas
# ============================================================================
class AdminDashboard(BaseModel):
    total_students: int
    total_faculty: int
    total_teams: int
    unassigned_teams: int
    proposals_by_status: Dict[str, int]


class FacultyDashboard(BaseModel):
    assigned_teams: int
    pending_reviews: int
    teams_without_recent_progress: int


class StudentDashboard(BaseModel):
    team_name: Optional[str] = None
    guide_name: Optional[str] = None
    proposal_status: Optional[str] = None
    course: Optional[str] = None
    latest_completion_percent: int = 0
    last_feedback_comment: Optional[str] = None
    teams_count: int = 0
    enrolled_courses: List[str] = []
