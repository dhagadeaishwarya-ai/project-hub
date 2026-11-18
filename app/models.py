import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Table,
    UniqueConstraint,
    Enum as SQLEnum,
    func
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"


class ProposalStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"


# Association table for team membership
# Rule: a student may belong to only ONE team -> UNIQUE constraint on user_id
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, unique=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    led_teams = relationship("Team", foreign_keys="Team.leader_id", back_populates="leader")
    guided_teams = relationship("Team", foreign_keys="Team.guide_id", back_populates="guide")
    teams = relationship("Team", secondary=team_members, back_populates="members")
    feedbacks = relationship("Feedback", back_populates="faculty")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    guide_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    leader = relationship("User", foreign_keys=[leader_id], back_populates="led_teams")
    guide = relationship("User", foreign_keys=[guide_id], back_populates="guided_teams")
    members = relationship("User", secondary=team_members, back_populates="teams")
    proposal = relationship("Proposal", back_populates="team", uselist=False, cascade="all, delete-orphan")
    progress_updates = relationship(
        "ProgressUpdate",
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="ProgressUpdate.week_number"
    )


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(String(150), nullable=False)
    abstract = Column(Text, nullable=False)
    problem_statement = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False)
    tech_stack = Column(String(255), nullable=False)
    status = Column(
        SQLEnum(ProposalStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProposalStatus.SUBMITTED
    )
    faculty_comment = Column(Text, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="proposal")


class ProgressUpdate(Base):
    __tablename__ = "progress_updates"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    completion_percent = Column(Integer, nullable=False)
    deliverable_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("team_id", "week_number", name="uq_team_week"),
    )

    # Relationships
    team = relationship("Team", back_populates="progress_updates")
    feedbacks = relationship("Feedback", back_populates="progress_update", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    progress_update_id = Column(Integer, ForeignKey("progress_updates.id", ondelete="CASCADE"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comments = Column(Text, nullable=False)
    marks = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    progress_update = relationship("ProgressUpdate", back_populates="feedbacks")
    faculty = relationship("User", back_populates="feedbacks")
