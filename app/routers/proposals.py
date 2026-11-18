from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, User, UserRole, Proposal, ProposalStatus
from app.schemas import ProposalCreate, ProposalUpdate, ProposalReview, ProposalRead
from app.deps import get_current_user
from app.routers.teams import ensure_leader, ensure_can_view_team
from app.notifications import notify

router = APIRouter(tags=["Proposals"])

# State machine: dictionary of allowed transitions
ALLOWED_TRANSITIONS: Dict[ProposalStatus, List[ProposalStatus]] = {
    ProposalStatus.SUBMITTED: [ProposalStatus.APPROVED, ProposalStatus.CHANGES_REQUESTED],
    ProposalStatus.CHANGES_REQUESTED: [ProposalStatus.SUBMITTED],
    ProposalStatus.APPROVED: [],  # Approved proposals are permanently locked
}


@router.post("/teams/{team_id}/proposal", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def submit_proposal(
    team_id: int,
    proposal_in: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a project proposal (Team Leader only, team size must be 2-4)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_leader(team, current_user)

    if len(team.members) < 2 or len(team.members) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team size must be between 2 and 4 members to submit a proposal"
        )

    if team.proposal is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A proposal has already been submitted for this team"
        )

    proposal = Proposal(
        team_id=team.id,
        title=proposal_in.title,
        abstract=proposal_in.abstract,
        problem_statement=proposal_in.problem_statement,
        domain=proposal_in.domain,
        tech_stack=proposal_in.tech_stack,
        status=ProposalStatus.SUBMITTED
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    # Notify guide if assigned
    if team.guide:
        notify(
            to_email=team.guide.email,
            subject=f"New Proposal Submitted: {proposal.title}",
            message=f"Team '{team.name}' has submitted a new project proposal for your review."
        )

    return proposal


@router.get("/teams/{team_id}/proposal", response_model=ProposalRead)
def get_team_proposal(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the proposal for a team (Authorized team members, guide, or admin)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_can_view_team(team, current_user)

    if not team.proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No proposal found for this team"
        )
    return team.proposal


@router.put("/teams/{team_id}/proposal", response_model=ProposalRead)
def update_proposal(
    team_id: int,
    proposal_in: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit proposal (Leader only, allowed only when status is SUBMITTED or CHANGES_REQUESTED)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    ensure_leader(team, current_user)

    proposal = team.proposal
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No proposal found for this team"
        )

    if proposal.status == ProposalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approved proposals are locked and cannot be edited"
        )

    # Editing resets CHANGES_REQUESTED back to SUBMITTED
    if proposal.status == ProposalStatus.CHANGES_REQUESTED:
        proposal.status = ProposalStatus.SUBMITTED

    proposal.title = proposal_in.title
    proposal.abstract = proposal_in.abstract
    proposal.problem_statement = proposal_in.problem_statement
    proposal.domain = proposal_in.domain
    proposal.tech_stack = proposal_in.tech_stack

    db.commit()
    db.refresh(proposal)
    return proposal


@router.patch("/proposals/{proposal_id}/review", response_model=ProposalRead)
def review_proposal(
    proposal_id: int,
    review_in: ProposalReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review proposal decision (Assigned Faculty Guide only)."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    team = proposal.team
    # Faculty ownership check: must be assigned guide
    if team.guide_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned faculty guide can review this proposal"
        )

    # Validate transition
    allowed = ALLOWED_TRANSITIONS.get(proposal.status, [])
    if review_in.decision not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition proposal from {proposal.status.value} to {review_in.decision.value}"
        )

    # Comment requirement for changes requested
    if review_in.decision == ProposalStatus.CHANGES_REQUESTED:
        if not review_in.comment or not review_in.comment.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A comment is required when requesting changes"
            )

    proposal.status = review_in.decision
    proposal.faculty_comment = review_in.comment
    db.commit()
    db.refresh(proposal)

    # Notify all team members of the outcome
    for member in team.members:
        notify(
            to_email=member.email,
            subject=f"Proposal Decision: {proposal.title} - {proposal.status.value}",
            message=f"Your proposal '{proposal.title}' has been reviewed: {proposal.status.value}. Faculty comment: {proposal.faculty_comment or 'None'}"
        )

    return proposal
