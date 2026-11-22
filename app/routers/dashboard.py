from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, User, UserRole, Proposal, ProposalStatus, ProgressUpdate, Feedback
from app.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retrieve role-specific dashboard statistics using SQL aggregate queries."""
    user_role = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)

    # ------------------------------------------------------------------------
    # 1. Admin Dashboard
    # ------------------------------------------------------------------------
    if user_role == UserRole.ADMIN.value:
        total_students = db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
        total_faculty = db.query(func.count(User.id)).filter(User.role == UserRole.FACULTY).scalar() or 0
        total_teams = db.query(func.count(Team.id)).scalar() or 0
        unassigned_teams = db.query(func.count(Team.id)).filter(Team.guide_id.is_(None)).scalar() or 0

        # Aggregated proposals by status using group_by
        proposals_grouped = (
            db.query(Proposal.status, func.count(Proposal.id))
            .group_by(Proposal.status)
            .all()
        )
        status_counts = {
            ProposalStatus.SUBMITTED.value: 0,
            ProposalStatus.CHANGES_REQUESTED.value: 0,
            ProposalStatus.APPROVED.value: 0
        }
        for st, count in proposals_grouped:
            key = st.value if hasattr(st, "value") else str(st)
            status_counts[key] = count

        return {
            "role": "admin",
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_teams": total_teams,
            "unassigned_teams": unassigned_teams,
            "proposals_by_status": status_counts
        }

    # ------------------------------------------------------------------------
    # 2. Faculty Dashboard
    # ------------------------------------------------------------------------
    elif user_role == UserRole.FACULTY.value:
        assigned_teams = db.query(func.count(Team.id)).filter(Team.guide_id == current_user.id).scalar() or 0

        pending_reviews = (
            db.query(func.count(Proposal.id))
            .join(Team, Proposal.team_id == Team.id)
            .filter(Team.guide_id == current_user.id, Proposal.status == ProposalStatus.SUBMITTED)
            .scalar() or 0
        )

        # Teams without progress in the latest 14 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        teams_with_recent = (
            db.query(ProgressUpdate.team_id)
            .join(Team, ProgressUpdate.team_id == Team.id)
            .filter(Team.guide_id == current_user.id, ProgressUpdate.created_at >= cutoff)
            .distinct()
            .subquery()
        )
        teams_without_recent = (
            db.query(func.count(Team.id))
            .filter(Team.guide_id == current_user.id, Team.id.notin_(db.query(teams_with_recent.c.team_id)))
            .scalar() or 0
        )

        return {
            "role": "faculty",
            "assigned_teams": assigned_teams,
            "pending_reviews": pending_reviews,
            "teams_without_recent_progress": teams_without_recent
        }

    # ------------------------------------------------------------------------
    # 3. Student Dashboard
    # ------------------------------------------------------------------------
    else:
        student_teams = (
            db.query(Team)
            .join(Team.members)
            .filter(User.id == current_user.id)
            .all()
        )

        if not student_teams:
            return {
                "role": "student",
                "team_name": None,
                "course": None,
                "guide_name": None,
                "proposal_status": None,
                "latest_completion_percent": 0,
                "last_feedback_comment": None,
                "teams_count": 0,
                "enrolled_courses": []
            }

        team = student_teams[0]

        # Latest progress update
        latest_update = (
            db.query(ProgressUpdate)
            .filter(ProgressUpdate.team_id == team.id)
            .order_by(ProgressUpdate.week_number.desc())
            .first()
        )

        # Most recent feedback comment
        last_feedback = (
            db.query(Feedback)
            .join(ProgressUpdate, Feedback.progress_update_id == ProgressUpdate.id)
            .filter(ProgressUpdate.team_id == team.id)
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
            .first()
        )

        return {
            "role": "student",
            "team_name": team.name,
            "course": team.course,
            "guide_name": team.guide.name if team.guide else None,
            "proposal_status": team.proposal.status.value if team.proposal else None,
            "latest_completion_percent": latest_update.completion_percent if latest_update else 0,
            "last_feedback_comment": last_feedback.comments if last_feedback else None,
            "teams_count": len(student_teams),
            "enrolled_courses": list(dict.fromkeys(t.course for t in student_teams if t.course))
        }
