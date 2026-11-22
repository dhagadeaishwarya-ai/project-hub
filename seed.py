"""ProjectHub database seeding script.
Idempotent script creating demo users, teams, proposals, progress updates, and faculty feedbacks.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models import (
    User,
    UserRole,
    Team,
    Proposal,
    ProposalStatus,
    ProgressUpdate,
    Feedback,
    team_members,
)
from app.security import hash_password


def seed():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        print("Cleaning up previous demo records for idempotency...")
        # Clear previous data in correct dependency order
        db.query(Feedback).delete()
        db.query(ProgressUpdate).delete()
        db.query(Proposal).delete()
        db.execute(team_members.delete())
        db.query(Team).delete()
        db.query(User).delete()
        db.commit()

        print("Creating users...")
        # 1 Admin
        admin = User(
            name="System Administrator",
            email="admin@projecthub.edu",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )

        # 2 Faculty
        faculty1 = User(
            name="Dr. Ramesh Sharma",
            email="dr.sharma@projecthub.edu",
            hashed_password=hash_password("FacultyPass123!"),
            role=UserRole.FACULTY,
            is_active=True,
        )
        faculty2 = User(
            name="Dr. Priya Patel",
            email="dr.patel@projecthub.edu",
            hashed_password=hash_password("FacultyPass123!"),
            role=UserRole.FACULTY,
            is_active=True,
        )

        # 6 Students
        students = [
            User(
                name="Aarav Mehta",
                email="student1@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
            User(
                name="Diya Sen",
                email="student2@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
            User(
                name="Rohan Gupta",
                email="student3@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
            User(
                name="Ananya Iyer",
                email="student4@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
            User(
                name="Kabir Verma",
                email="student5@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
            User(
                name="Meera Nair",
                email="student6@projecthub.edu",
                hashed_password=hash_password("StudentPass123!"),
                role=UserRole.STUDENT,
                is_active=True,
            ),
        ]

        db.add_all([admin, faculty1, faculty2] + students)
        db.commit()

        # Refresh instances to load IDs
        db.refresh(faculty1)
        db.refresh(faculty2)
        for s in students:
            db.refresh(s)

        print("Creating Team 1 (Autonomous Rover AI)...")
        team1 = Team(
            name="Autonomous Rover AI",
            academic_year="2026-2027",
            course="CS501 - Capstone Project",
            leader_id=students[0].id,
            guide_id=faculty1.id,
        )
        team1.members.extend([students[0], students[1], students[2]])
        db.add(team1)
        db.commit()
        db.refresh(team1)

        print("Creating Approved Proposal for Team 1...")
        prop1 = Proposal(
            team_id=team1.id,
            title="Autonomous Terrain Rover with Real-time SLAM Navigation",
            abstract="This project presents a self-navigating terrain rover leveraging 2D/3D LIDAR SLAM algorithms, stereo depth perception, and edge computing inference for GPS-denied environments.",
            problem_statement="Ground survey rovers face frequent communication loss and GPS dropouts in underground or forested environments, requiring onboard real-time mapping.",
            domain="Robotics & AI",
            tech_stack="Python, ROS2 Humble, PyTorch, OpenCV, NVIDIA Jetson",
            status=ProposalStatus.APPROVED,
            faculty_comment="Scope approved. Clear milestones and strong hardware architecture plan.",
        )
        db.add(prop1)
        db.commit()

        print("Adding Progress Updates & Feedback for Team 1...")
        now = datetime.now(timezone.utc)

        # Week 1
        w1 = ProgressUpdate(
            team_id=team1.id,
            week_number=1,
            description="Completed rover aluminum chassis assembly, mounted brushless DC motors, and verified power distribution.",
            completion_percent=25,
            deliverable_url="https://rover.projecthub.edu/demo/week1",
            created_at=now - timedelta(days=14),
        )
        db.add(w1)
        db.commit()
        db.refresh(w1)

        f1 = Feedback(
            progress_update_id=w1.id,
            faculty_id=faculty1.id,
            comments="Solid physical assembly. Ensure motor driver heatsinks are installed prior to torque benchmarking.",
            marks=85,
            created_at=now - timedelta(days=13),
        )
        db.add(f1)

        # Week 2
        w2 = ProgressUpdate(
            team_id=team1.id,
            week_number=2,
            description="Integrated RP-LIDAR A1 sensor and successfully ran Cartographer SLAM in a controlled hallway environment.",
            completion_percent=55,
            deliverable_url="https://rover.projecthub.edu/demo/week2",
            created_at=now - timedelta(days=7),
        )
        db.add(w2)
        db.commit()
        db.refresh(w2)

        f2 = Feedback(
            progress_update_id=w2.id,
            faculty_id=faculty1.id,
            comments="SLAM drift error is under 3.5%, well within acceptable boundaries. Proceed to obstacle evasion.",
            marks=90,
            created_at=now - timedelta(days=6),
        )
        db.add(f2)

        # Week 3
        w3 = ProgressUpdate(
            team_id=team1.id,
            week_number=3,
            description="Deployed YOLOv8-nano model on Jetson Orin Nano for live obstacle classification at 32 FPS.",
            completion_percent=80,
            deliverable_url="https://rover.projecthub.edu/demo/week3",
            created_at=now - timedelta(days=1),
        )
        db.add(w3)
        db.commit()
        db.refresh(w3)

        f3 = Feedback(
            progress_update_id=w3.id,
            faculty_id=faculty1.id,
            comments="Excellent performance on inference benchmarks. Finalize the outdoor testing protocol.",
            marks=92,
            created_at=now,
        )
        db.add(f3)
        db.commit()

        print("Creating Team 2 (Decentralized Medical Records)...")
        team2 = Team(
            name="Decentralized MedRecords",
            academic_year="2026-2027",
            course="CS502 - Cloud & Web3 Systems",
            leader_id=students[3].id,
            guide_id=faculty2.id,
        )
        team2.members.extend([students[3], students[4], students[5]])
        db.add(team2)
        db.commit()
        db.refresh(team2)

        print("Creating Changes-Requested Proposal for Team 2...")
        prop2 = Proposal(
            team_id=team2.id,
            title="Zero-Knowledge Medical Record Verification on Blockchain",
            abstract="A decentralized health identity architecture using zk-SNARKs to permit cryptographic verification of patient vaccination and diagnostic status without exposing clinical histories.",
            problem_statement="Centralized health registries expose private patient clinical information during verification checks by employers and insurers.",
            domain="Security & Web3",
            tech_stack="Solidity, Python, FastAPI, Circom, Ethereum",
            status=ProposalStatus.CHANGES_REQUESTED,
            faculty_comment="Scope is too broad for an undergraduate project. Please narrow the circuit complexity, address proof generation latency, and detail HIPAA compatibility.",
        )
        db.add(prop2)
        db.commit()

        print("Creating Team 3 (Edge AI Diagnostics - Multi-course demonstration)...")
        # Student 1 (Aarav) also leads Team 3 for course CS503 under Dr. Priya Patel!
        team3 = Team(
            name="Edge AI Diagnostics",
            academic_year="2026-2027",
            course="CS503 - Embedded Systems Lab",
            leader_id=students[0].id,
            guide_id=faculty2.id,
        )
        team3.members.extend([students[0], students[4], students[5]])
        db.add(team3)
        db.commit()
        db.refresh(team3)

        print("Creating Submitted Proposal for Team 3...")
        prop3 = Proposal(
            team_id=team3.id,
            title="Edge Anomaly Detection with Quantized Neural Models",
            abstract="This laboratory project explores deployable sub-watt machine learning models for early mechanical vibration anomaly detection on microcontroller-class edge nodes.",
            problem_statement="Industrial vibration monitors require expensive cloud backhauls and encounter prohibitive network latency during catastrophic motor failures.",
            domain="Embedded Systems & TinyML",
            tech_stack="C++, FreeRTOS, TensorFlow Lite for Microcontrollers, STM32",
            status=ProposalStatus.SUBMITTED,
            faculty_comment=None,
        )
        db.add(prop3)
        db.commit()

        print("\n=======================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=======================================================")
        print("Seeded Entities:")
        print("  - 1 Admin: admin@projecthub.edu (Password: AdminPass123!)")
        print("  - 2 Faculty:")
        print("      * Dr. Ramesh Sharma: dr.sharma@projecthub.edu (Password: FacultyPass123!)")
        print("      * Dr. Priya Patel: dr.patel@projecthub.edu (Password: FacultyPass123!)")
        print("  - 6 Students (student1@projecthub.edu .. student6@projecthub.edu, Password: StudentPass123!)")
        print("  - 3 Multi-Course Teams:")
        print("      * Team 1: 'Autonomous Rover AI' [CS501 - Capstone Project] (Guide: Dr. Sharma, Leader: Student 1)")
        print("      * Team 2: 'Decentralized MedRecords' [CS502 - Cloud & Web3 Systems] (Guide: Dr. Patel, Leader: Student 4)")
        print("      * Team 3: 'Edge AI Diagnostics' [CS503 - Embedded Systems Lab] (Guide: Dr. Patel, Leader: Student 1)")
        print("=======================================================\n")

    except Exception as exc:
        db.rollback()
        print(f"Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
