from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, User, UserRole, ProgressUpdate, Feedback, ProposalStatus
from app.schemas import ProgressUpdateCreate, ProgressUpdateRead, FeedbackCreate, FeedbackRead
from app.deps import get_current_user
from app.routers.teams import ensure_can_view_team
from app.notifications import notify

router = APIRouter(tags=["Progress & Feedback"])


@router.post("/teams/{team_id}/progress", response_model=ProgressUpdateRead, status_code=status.HTTP_201_CREATED)
def create_progress_update(
    team_id: int,
    progress_in: ProgressUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post weekly progress update (Team members only, requires APPROVED proposal)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check team membership
    is_member = any(m.id == current_user.id for m in team.members) or team.leader_id == current_user.id
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can submit progress updates"
        )

    # Requires approved proposal
    if not team.proposal or team.proposal.status != ProposalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress updates are only allowed after the team proposal has been approved"
        )

    # Unique week_number per team (409)
    existing_week = db.query(ProgressUpdate).filter(
        ProgressUpdate.team_id == team.id,
        ProgressUpdate.week_number == progress_in.week_number
    ).first()
    if existing_week:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Progress update for week {progress_in.week_number} already exists"
        )

    # Completion percent must not decrease versus previous update by week order
    prev_update = (
        db.query(ProgressUpdate)
        .filter(ProgressUpdate.team_id == team.id, ProgressUpdate.week_number < progress_in.week_number)
        .order_by(ProgressUpdate.week_number.desc())
        .first()
    )
    if prev_update and progress_in.completion_percent < prev_update.completion_percent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Completion percent ({progress_in.completion_percent}%) cannot decrease versus previous update ({prev_update.completion_percent}% in week {prev_update.week_number})"
        )

    # Ensure it also does not exceed any existing future week updates
    future_update = (
        db.query(ProgressUpdate)
        .filter(ProgressUpdate.team_id == team.id, ProgressUpdate.week_number > progress_in.week_number)
        .order_by(ProgressUpdate.week_number.asc())
        .first()
    )
    if future_update and progress_in.completion_percent > future_update.completion_percent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Completion percent ({progress_in.completion_percent}%) cannot exceed future update ({future_update.completion_percent}% in week {future_update.week_number})"
        )

    update = ProgressUpdate(
        team_id=team.id,
        week_number=progress_in.week_number,
        description=progress_in.description,
        completion_percent=progress_in.completion_percent,
        deliverable_url=progress_in.deliverable_url
    )
    db.add(update)
    db.commit()
    db.refresh(update)
    return update


@router.get("/teams/{team_id}/progress", response_model=List[ProgressUpdateRead])
def list_team_progress(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all progress updates for a team (Team members, guide, and admin)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_can_view_team(team, current_user)

    updates = (
        db.query(ProgressUpdate)
        .filter(ProgressUpdate.team_id == team.id)
        .order_by(ProgressUpdate.week_number.asc())
        .all()
    )
    return updates


@router.post("/progress/{progress_id}/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def add_faculty_feedback(
    progress_id: int,
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provide faculty feedback and marks on a progress update (Assigned Guide only)."""
    update = db.query(ProgressUpdate).filter(ProgressUpdate.id == progress_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress update not found"
        )

    team = update.team
    if team.guide_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned faculty guide can provide feedback"
        )

    feedback = Feedback(
        progress_update_id=update.id,
        faculty_id=current_user.id,
        comments=feedback_in.comments,
        marks=feedback_in.marks
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Notify team leader
    if team.leader:
        notify(
            to_email=team.leader.email,
            subject=f"New Feedback on Week {update.week_number} Progress",
            message=f"Faculty {current_user.name} reviewed your week {update.week_number} update. Comments: {feedback.comments} (Marks: {feedback.marks or 'N/A'})"
        )

    return feedback
