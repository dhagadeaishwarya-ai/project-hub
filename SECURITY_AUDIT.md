# ProjectHub Security Audit & Route Matrix

This document provides a comprehensive security audit of all routes in ProjectHub, verifying authentication, role access control, ownership verification, and status codes.

## 1. Route Security Matrix

| # | Method | Path | Allowed Roles | Ownership / Scoping Rule | Status Codes Returned | Security Status |
|---|--------|------|---------------|--------------------------|-----------------------|-----------------|
| 1 | POST | `/auth/login` | Public | None (authenticates credentials) | 200, 401, 422 | SECURE |
| 2 | POST | `/users` | `admin` | Admin only | 201, 401, 403, 409, 422 | SECURE |
| 3 | GET | `/users/me` | Any authenticated user | Returns currently authenticated user | 200, 401 | SECURE |
| 4 | POST | `/teams` | `student` | Student creator becomes leader & 1st member; student cannot already be in any team | 201, 400, 401, 403, 422 | SECURE |
| 5 | GET | `/teams` | Any authenticated user | Admin: all; Faculty: guided teams; Student: own team | 200, 401 | SECURE |
| 6 | GET | `/teams/{id}` | Any authenticated user | Admin: all; Faculty: must be guide; Student: must be member | 200, 401, 403, 404 | SECURE |
| 7 | POST | `/teams/{id}/members` | `student` (leader) | Leader only; target must be active student not in any team; team size <= 4 | 200, 400, 401, 403, 404, 422 | SECURE |
| 8 | DELETE | `/teams/{id}/members/{user_id}` | `student` (leader) | Leader only; leader cannot remove self; target must belong to team | 200, 400, 401, 403, 404 | SECURE |
| 9 | PUT | `/teams/{id}/guide` | `admin` | Target must be an active faculty member | 200, 400, 401, 403, 404, 422 | SECURE |
| 10 | POST | `/teams/{id}/proposal` | `student` (leader) | Leader only; team size 2-4; one proposal per team | 201, 400, 401, 403, 404, 422 | SECURE |
| 11 | GET | `/teams/{id}/proposal` | Any authenticated user | Team members, assigned guide, admin only | 200, 401, 403, 404 | SECURE |
| 12 | PUT | `/teams/{id}/proposal` | `student` (leader) | Leader only; only allowed when SUBMITTED or CHANGES_REQUESTED (APPROVED is locked) | 200, 400, 401, 403, 404, 422 | SECURE |
| 13 | PATCH | `/proposals/{id}/review` | `faculty` (guide) | Assigned guide only; valid status transitions; comment required for CHANGES_REQUESTED | 200, 400, 401, 403, 404, 422 | SECURE |
| 14 | POST | `/teams/{id}/progress` | `student` (member) | Member only; proposal must be APPROVED; non-decreasing completion percent; unique week (1-20) | 201, 400, 401, 403, 404, 409, 422 | SECURE |
| 15 | GET | `/teams/{id}/progress` | Any authenticated user | Team members, assigned guide, admin only | 200, 401, 403, 404 | SECURE |
| 16 | POST | `/progress/{id}/feedback` | `faculty` (guide) | Assigned guide only; optional marks 0-100 | 201, 401, 403, 404, 422 | SECURE |
| 17 | GET | `/dashboard` | Any authenticated user | Role-specific aggregate statistics scoped to the user | 200, 401 | SECURE |
| 18 | GET | `/health` | Public | Operational monitoring endpoint | 200 | SECURE |

## 2. Security Invariants Verified

- **No Hard-coded Secrets**: `SECRET_KEY` is loaded from environment or `.env` and validated by Pydantic; default weak keys are rejected outside test mode.
- **Token Expiry**: Default 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=60`).
- **No Password Leaks**: `UserRead` schema excludes `hashed_password`. Database query responses are serialized through response models.
- **Generic Login Errors**: Authentication failure returns identical HTTP 401 message (`"Incorrect email or password"`), preventing user enumeration.
- **Generic 500 Responses**: Unhandled exceptions are intercepted by a global exception handler in `main.py` to prevent SQL/traceback leaks.
- **Deactivated User Protection**: Inactive users are rejected at login and blocked when presenting any token (`get_current_user` raises HTTP 401).
