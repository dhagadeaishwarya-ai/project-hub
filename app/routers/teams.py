from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, User, UserRole, team_members
from app.schemas import TeamCreate, TeamRead, TeamMemberAdd, TeamGuideAssign
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/teams", tags=["Teams"])


# ============================================================================
# Helper Functions
# ============================================================================
def is_student_in_course_team(db: Session, user_id: int, course: str) -> bool:
    """Check if the user is already part of a team for the given course."""
    exists = (
        db.query(Team)
        .join(Team.members)
        .filter(User.id == user_id, Team.course == course)
        .first()
    )
    return exists is not None


def ensure_leader(team: Team, user: User) -> None:
    """Verify that the user is the team leader; raise 403 if not."""
    if team.leader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can perform this operation"
        )


def ensure_can_view_team(team: Team, user: User) -> None:
    """Verify that the user is permitted to view the team."""
    user_role = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    if user_role == UserRole.ADMIN.value:
        return
    if user_role == UserRole.FACULTY.value:
        if team.guide_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faculty can only view teams they guide"
            )
        return
    # Student role: must be a member or leader
    is_member = any(m.id == user.id for m in team.members)
    if not is_member and team.leader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students may only view their own team"
        )


# ============================================================================
# Routes
# ============================================================================
@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT))
):
    """Create a new team. Student creator becomes leader and first member."""
    if is_student_in_course_team(db, current_user.id, team_in.course):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student is already a member of a team for course '{team_in.course}'"
        )

    team = Team(
        name=team_in.name,
        academic_year=team_in.academic_year,
        course=team_in.course,
        leader_id=current_user.id
    )
    team.members.append(current_user)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=List[TeamRead])
def list_teams(
    course: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List teams scoped by user role and optional course filter: admin sees all, faculty sees guided, student sees own."""
    user_role = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    query = db.query(Team)

    if user_role == UserRole.ADMIN.value:
        pass
    elif user_role == UserRole.FACULTY.value:
        query = query.filter(Team.guide_id == current_user.id)
    else:
        # Student role
        query = query.join(Team.members).filter(User.id == current_user.id)

    if course:
        query = query.filter(Team.course == course)

    return query.all()


@router.get("/meta/courses", response_model=List[str])
def get_courses(db: Session = Depends(get_db)):
    """Retrieve unique list of all course names with existing teams."""
    rows = db.query(Team.course).distinct().all()
    courses = [r[0] for r in rows if r[0]]
    return sorted(courses)


@router.get("/{team_id}", response_model=TeamRead)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team details by ID with role-based access checks."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_can_view_team(team, current_user)
    return team


@router.post("/{team_id}/members", response_model=TeamRead)
def add_team_member(
    team_id: int,
    member_in: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to the team (Leader only, max 4 members)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_leader(team, current_user)

    if len(team.members) >= 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team size cannot exceed 4 members"
        )

    target_user = db.query(User).filter(User.email == member_in.student_email).first()
    if not target_user or not target_user.is_active or target_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user must be an active student"
        )

    if is_student_in_course_team(db, target_user.id, team.course):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student is already a member of a team for course '{team.course}'"
        )

    team.members.append(target_user)
    db.commit()
    db.refresh(team)
    return team

    team.members.append(target_user)
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}/members/{user_id}")
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from the team (Leader only). Cannot remove the leader."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_leader(team, current_user)

    if user_id == team.leader_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the team leader from the team"
        )

    target_member = next((m for m in team.members if m.id == user_id), None)
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this team"
        )

    team.members.remove(target_member)
    db.commit()
    return {"message": "Member removed successfully"}


@router.put("/{team_id}/guide", response_model=TeamRead)
def assign_guide(
    team_id: int,
    guide_in: TeamGuideAssign,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN))
):
    """Assign a faculty guide to a team (Admin only)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    faculty = db.query(User).filter(User.id == guide_in.faculty_id).first()
    if not faculty or not faculty.is_active or faculty.role != UserRole.FACULTY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified user must be an active faculty member"
        )

    team.guide_id = faculty.id
    db.commit()
    db.refresh(team)
    return team
