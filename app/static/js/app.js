/**
 * ProjectHub Main Application Logic
 */

const App = {
  state: {
    currentUser: null,
    currentTab: 'dashboard',
    activeTeamId: null,
    selectedCourse: '',
    availableCourses: [],
    teams: [],
    dashboard: null,
    activeTeam: null,
    activeProposal: null,
    activeProgress: [],
  },

  demoUsers: {
    admin: { email: 'admin@projecthub.edu', pass: 'AdminPass123!' },
    faculty1: { email: 'dr.sharma@projecthub.edu', pass: 'FacultyPass123!' },
    faculty2: { email: 'dr.patel@projecthub.edu', pass: 'FacultyPass123!' },
    student1: { email: 'student1@projecthub.edu', pass: 'StudentPass123!' },
    student4: { email: 'student4@projecthub.edu', pass: 'StudentPass123!' },
  },

  async init() {
    this.bindEvents();
    if (API.isAuthenticated()) {
      try {
        await this.loadUserProfile();
      } catch (err) {
        this.showLoginView();
      }
    } else {
      this.showLoginView();
    }
  },

  bindEvents() {
    window.addEventListener('auth:expired', () => {
      this.showToast('Your session has expired. Please log in again.', 'error');
      this.showLoginView();
    });

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const btn = document.getElementById('login-submit-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Signing in...';
        try {
          await API.login(email, password);
          await this.loadUserProfile();
          this.showToast('Welcome back!', 'success');
        } catch (err) {
          this.showToast(err.message, 'error');
        } finally {
          btn.disabled = false;
          btn.innerText = 'Sign In';
        }
      });
    }
  },

  // Toast Helper
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span><span style="flex:1;">${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // Authentication & Views
  async loadUserProfile() {
    this.state.currentUser = await API.getMe();
    document.getElementById('auth-view').style.display = 'none';
    document.getElementById('app-view').style.display = 'block';

    this.renderHeader();
    this.switchTab('dashboard');
  },

  showLoginView() {
    this.state.currentUser = null;
    API.clearToken();
    document.getElementById('auth-view').style.display = 'flex';
    document.getElementById('app-view').style.display = 'none';
  },

  async quickLogin(key) {
    const cred = this.demoUsers[key];
    if (!cred) return;
    document.getElementById('login-email').value = cred.email;
    document.getElementById('login-password').value = cred.pass;

    try {
      this.showToast(`Authenticating demo user (${cred.email})...`, 'info');
      await API.login(cred.email, cred.pass);
      await this.loadUserProfile();
      this.showToast(`Logged in as ${this.state.currentUser.name} (${this.state.currentUser.role})`, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  logout() {
    API.clearToken();
    this.showLoginView();
    this.showToast('You have been logged out.', 'info');
  },

  renderHeader() {
    const user = this.state.currentUser;
    const userPill = document.getElementById('user-profile-pill');
    if (userPill) {
      userPill.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.65rem;">
          <div style="width:32px; height:32px; border-radius:50%; background:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem;">
            ${user.name.charAt(0)}
          </div>
          <div style="text-align:left;">
            <div style="font-weight:600; font-size:0.875rem;">${user.name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${user.email}</div>
          </div>
          <span class="badge badge-${user.role}">${user.role}</span>
        </div>
      `;
    }

    // Adjust navigation items based on role
    const adminNav = document.getElementById('nav-admin-users');
    if (adminNav) {
      adminNav.style.display = user.role === 'admin' ? 'inline-flex' : 'none';
    }
  },

  switchTab(tabName) {
    this.state.currentTab = tabName;
    document.querySelectorAll('.nav-link').forEach((link) => {
      link.classList.toggle('active', link.dataset.tab === tabName);
    });

    const contentArea = document.getElementById('tab-content-area');
    contentArea.innerHTML = '<div style="padding:3rem; text-align:center; color:var(--text-muted);">Loading...</div>';

    if (tabName === 'dashboard') {
      this.renderDashboardView();
    } else if (tabName === 'teams') {
      this.renderTeamsView();
    } else if (tabName === 'admin-users') {
      this.renderAdminUsersView();
    }
  },

  // --------------------------------------------------------------------------
  // Dashboard View
  // --------------------------------------------------------------------------
  async renderDashboardView() {
    const area = document.getElementById('tab-content-area');
    try {
      const data = await API.getDashboard();
      this.state.dashboard = data;
      const role = data.role;

      let html = `<div style="max-width:1100px; margin:0 auto;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
          <div>
            <h2 style="font-size:1.75rem; font-weight:700;">Welcome, ${this.state.currentUser.name}</h2>
            <p style="color:var(--text-muted);">Role Overview & Key Metrics</p>
          </div>
          <div>
            <button class="btn btn-secondary btn-sm" onclick="App.renderDashboardView()">🔄 Refresh Data</button>
          </div>
        </div>`;

      if (role === 'admin') {
        html += `
          <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1.25rem; margin-bottom:2rem;">
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Total Students</div>
              <div style="font-size:2.2rem; font-weight:700; color:#60a5fa; margin-top:0.25rem;">${data.total_students}</div>
            </div>
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Total Faculty</div>
              <div style="font-size:2.2rem; font-weight:700; color:#34d399; margin-top:0.25rem;">${data.total_faculty}</div>
            </div>
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Total Teams</div>
              <div style="font-size:2.2rem; font-weight:700; color:#a78bfa; margin-top:0.25rem;">${data.total_teams}</div>
            </div>
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Unassigned Teams</div>
              <div style="font-size:2.2rem; font-weight:700; color:${data.unassigned_teams > 0 ? '#f87171' : '#94a3b8'}; margin-top:0.25rem;">${data.unassigned_teams}</div>
            </div>
          </div>

          <div class="card" style="margin-bottom:2rem;">
            <h3 style="font-size:1.15rem; font-weight:600; margin-bottom:1.25rem;">Proposals by Approval Status</h3>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem;">
              <div style="background:var(--bg-input); padding:1rem; border-radius:var(--radius-md); border-left:4px solid var(--info);">
                <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Submitted (Pending Review)</div>
                <div style="font-size:1.8rem; font-weight:700; color:#38bdf8;">${data.proposals_by_status.SUBMITTED || 0}</div>
              </div>
              <div style="background:var(--bg-input); padding:1rem; border-radius:var(--radius-md); border-left:4px solid var(--warning);">
                <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Changes Requested</div>
                <div style="font-size:1.8rem; font-weight:700; color:#fbbf24;">${data.proposals_by_status.CHANGES_REQUESTED || 0}</div>
              </div>
              <div style="background:var(--bg-input); padding:1rem; border-radius:var(--radius-md); border-left:4px solid var(--success);">
                <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Approved</div>
                <div style="font-size:1.8rem; font-weight:700; color:#34d399;">${data.proposals_by_status.APPROVED || 0}</div>
              </div>
            </div>
          </div>
        `;
      } else if (role === 'faculty') {
        html += `
          <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:1.25rem; margin-bottom:2rem;">
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Assigned Guided Teams</div>
              <div style="font-size:2.2rem; font-weight:700; color:#34d399; margin-top:0.25rem;">${data.assigned_teams}</div>
            </div>
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Pending Proposals to Review</div>
              <div style="font-size:2.2rem; font-weight:700; color:#fbbf24; margin-top:0.25rem;">${data.pending_reviews}</div>
            </div>
            <div class="card">
              <div style="color:var(--text-muted); font-size:0.85rem;">Teams Without Progress (&gt;14 days)</div>
              <div style="font-size:2.2rem; font-weight:700; color:${data.teams_without_recent_progress > 0 ? '#f87171' : '#34d399'}; margin-top:0.25rem;">${data.teams_without_recent_progress}</div>
            </div>
          </div>
        `;
      } else {
        // Student role
        if (!data.team_name) {
          html += `
            <div class="card" style="text-align:center; padding:3rem 1.5rem;">
              <div style="font-size:3rem; margin-bottom:1rem;">👥</div>
              <h3 style="font-size:1.35rem; font-weight:600; margin-bottom:0.5rem;">You are not in any project team yet</h3>
              <p style="color:var(--text-muted); max-width:450px; margin:0 auto 1.5rem auto;">Create a team as the student leader or request your team leader to add your email to their team.</p>
              <button class="btn btn-primary" onclick="App.openCreateTeamModal()">➕ Create New Team</button>
            </div>
          `;
        } else {
          const statusBadge = data.proposal_status
            ? `<span class="badge badge-${data.proposal_status.toLowerCase()}">${data.proposal_status}</span>`
            : '<span class="badge" style="background:#334155; color:#94a3b8;">Not Submitted</span>';

          html += `
            <div class="card" style="margin-bottom:1.5rem;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.25rem; flex-wrap:wrap; gap:1rem;">
                <div>
                  <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
                    <span style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase;">My Active Team</span>
                    ${data.course ? `<span class="badge" style="background:rgba(99, 102, 241, 0.15); color:#a5b4fc; text-transform:none;">📚 ${data.course}</span>` : ''}
                  </div>
                  <h3 style="font-size:1.5rem; font-weight:700;">${data.team_name}</h3>
                </div>
                <div>${statusBadge}</div>
              </div>

              ${data.enrolled_courses && data.enrolled_courses.length > 0 ? `
                <div style="background:rgba(15, 23, 42, 0.6); padding:0.75rem 1rem; border-radius:var(--radius-md); border:1px solid var(--border-color); margin-bottom:1.25rem; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.5rem;">
                  <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                    <span style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Enrolled Courses (${data.enrolled_courses.length}):</span>
                    ${data.enrolled_courses.map(c => `
                      <span class="badge" style="background:rgba(99, 102, 241, 0.15); color:#a5b4fc; cursor:pointer;" onclick="App.state.selectedCourse='${c}'; App.switchTab('teams');" title="Click to view teams in this course">📚 ${c}</span>
                    `).join('')}
                  </div>
                  <button class="btn btn-secondary btn-sm" onclick="App.openCreateTeamModal()">➕ Create Another Team (New Course)</button>
                </div>
              ` : ''}

              <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
                <div style="background:var(--bg-input); padding:1rem; border-radius:var(--radius-md);">
                  <div style="font-size:0.8rem; color:var(--text-muted);">Assigned Faculty Guide</div>
                  <div style="font-size:1.1rem; font-weight:600; margin-top:0.25rem; color:#f8fafc;">${data.guide_name || 'None Assigned'}</div>
                </div>
                <div style="background:var(--bg-input); padding:1rem; border-radius:var(--radius-md);">
                  <div style="font-size:0.8rem; color:var(--text-muted);">Latest Completion</div>
                  <div style="font-size:1.1rem; font-weight:600; margin-top:0.25rem; color:#34d399;">${data.latest_completion_percent}%</div>
                </div>
              </div>

              <div style="margin-bottom:1.5rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:var(--text-muted); margin-bottom:0.4rem;">
                  <span>Overall Project Progress</span>
                  <span style="font-weight:600; color:white;">${data.latest_completion_percent}%</span>
                </div>
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" style="width:${data.latest_completion_percent}%;"></div>
                </div>
              </div>

              ${data.last_feedback_comment ? `
                <div style="background:rgba(59, 130, 246, 0.08); border-left:4px solid var(--primary); padding:1rem; border-radius:var(--radius-md);">
                  <div style="font-size:0.8rem; font-weight:600; color:#60a5fa; text-transform:uppercase;">Latest Guide Feedback</div>
                  <div style="margin-top:0.35rem; font-style:italic;">"${data.last_feedback_comment}"</div>
                </div>
              ` : ''}

              <div style="margin-top:1.5rem; display:flex; gap:0.75rem;">
                <button class="btn btn-primary" onclick="App.switchTab('teams')">View Team & Proposal Details</button>
              </div>
            </div>
          `;
        }
      }

      html += `</div>`;
      area.innerHTML = html;
    } catch (err) {
      area.innerHTML = `<div class="card" style="color:var(--danger); text-align:center; padding:2rem;">Error loading dashboard: ${err.message}</div>`;
    }
  },

  // --------------------------------------------------------------------------
  // Teams View
  // --------------------------------------------------------------------------
  async renderTeamsView() {
    const area = document.getElementById('tab-content-area');
    try {
      const courses = await API.getCourses().catch(() => []);
      this.state.availableCourses = courses;
      const teams = await API.getTeams(this.state.selectedCourse);
      this.state.teams = teams;
      const user = this.state.currentUser;

      let html = `<div style="max-width:1100px; margin:0 auto;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
          <div>
            <h2 style="font-size:1.75rem; font-weight:700;">Project Teams</h2>
            <p style="color:var(--text-muted);">${user.role === 'admin' ? 'All College Teams Across All Courses' : user.role === 'faculty' ? 'Your Guided Project Teams Across Courses' : 'Your Enrolled Project Teams'}</p>
          </div>
          <div style="display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap;">
            <!-- Course Filter Option -->
            <div style="display:flex; align-items:center; gap:0.4rem; background:var(--bg-input); padding:0.35rem 0.65rem; border-radius:var(--radius-md); border:1px solid var(--border-color);">
              <span style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">📚 Filter Course:</span>
              <select class="form-control" style="width:auto; padding:0.2rem 0.5rem; font-size:0.8rem;" onchange="App.handleCourseFilter(this.value)">
                <option value="">All Courses (${courses.length})</option>
                ${courses.map(c => `<option value="${c}" ${c === App.state.selectedCourse ? 'selected' : ''}>${c}</option>`).join('')}
              </select>
              ${this.state.selectedCourse ? `<button class="btn btn-secondary btn-sm" style="padding:0.15rem 0.4rem; font-size:0.75rem;" onclick="App.handleCourseFilter('')" title="Clear course filter">✕</button>` : ''}
            </div>

            ${user.role === 'student' ? `
              <button class="btn btn-primary" onclick="App.openCreateTeamModal()">➕ Create Team</button>
            ` : ''}
          </div>
        </div>`;

      if (teams.length === 0) {
        html += `
          <div class="card" style="text-align:center; padding:3rem 1.5rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
            <h3 style="font-size:1.25rem; font-weight:600; margin-bottom:0.5rem;">No teams found</h3>
            <p style="color:var(--text-muted); max-width:400px; margin:0 auto 1.5rem auto;">
              ${this.state.selectedCourse ? `No teams found enrolled in course "${this.state.selectedCourse}".` : user.role === 'student' ? 'You have not joined or created a team yet.' : 'There are currently no teams in your scope.'}
            </p>
            ${this.state.selectedCourse ? `
              <button class="btn btn-secondary btn-sm" onclick="App.handleCourseFilter('')">Show All Courses</button>
            ` : user.role === 'student' ? `
              <button class="btn btn-primary" onclick="App.openCreateTeamModal()">Create New Team</button>
            ` : ''}
          </div>
        `;
      } else {
        html += `<div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:1.25rem;">`;
        for (const t of teams) {
          const isLeader = t.leader_id === user.id;
          const membersList = t.members.map(m => m.name || m.email).join(', ');

          html += `
            <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.6rem; flex-wrap:wrap; gap:0.35rem;">
                  <span class="badge" style="background:#1e293b; color:#94a3b8;">${t.academic_year}</span>
                  ${t.guide ? `<span class="badge badge-faculty">Guide: ${t.guide.name}</span>` : `<span class="badge" style="background:rgba(239, 68, 68, 0.15); color:#f87171;">No Guide</span>`}
                </div>

                <!-- Course badge on each team card -->
                <div style="margin-bottom:0.65rem;">
                  <span class="badge" style="background:rgba(99, 102, 241, 0.15); color:#a5b4fc; border:1px solid rgba(99, 102, 241, 0.35); text-transform:none; font-size:0.78rem; font-weight:600;">
                    📚 ${t.course}
                  </span>
                </div>

                <h3 style="font-size:1.2rem; font-weight:700; margin-bottom:0.5rem;">${t.name}</h3>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.5rem;">
                  <strong>Leader:</strong> ${t.leader ? t.leader.name : 'Unknown'}
                </div>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
                  <strong>Members (${t.members.length}/4):</strong> ${membersList}
                </div>
              </div>

              <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:1rem; border-top:1px solid var(--border-color); padding-top:1rem;">
                <button class="btn btn-primary btn-sm" onclick="App.openTeamDetail(${t.id})">🔍 Team Details</button>
                ${user.role === 'admin' ? `
                  <button class="btn btn-secondary btn-sm" onclick="App.openAssignGuideModal(${t.id}, '${t.name.replace(/'/g, "\\'")}')">👨‍🏫 Assign Guide</button>
                ` : ''}
              </div>
            </div>
          `;
        }
        html += `</div>`;
      }

      html += `</div>`;
      area.innerHTML = html;
    } catch (err) {
      area.innerHTML = `<div class="card" style="color:var(--danger); text-align:center; padding:2rem;">Error loading teams: ${err.message}</div>`;
    }
  },

  handleCourseFilter(course) {
    this.state.selectedCourse = course;
    this.renderTeamsView();
  },

  // --------------------------------------------------------------------------
  // Team Detail & Proposal & Progress Combined View
  // --------------------------------------------------------------------------
  async openTeamDetail(teamId) {
    this.state.activeTeamId = teamId;
    const area = document.getElementById('tab-content-area');
    area.innerHTML = '<div style="padding:3rem; text-align:center; color:var(--text-muted);">Loading team details...</div>';

    try {
      const team = await API.getTeam(teamId);
      this.state.activeTeam = team;

      let proposal = null;
      try {
        proposal = await API.getTeamProposal(teamId);
      } catch (err) {
        proposal = null;
      }
      this.state.activeProposal = proposal;

      let progressList = [];
      try {
        progressList = await API.getTeamProgress(teamId);
      } catch (err) {
        progressList = [];
      }
      this.state.activeProgress = progressList;

      const user = this.state.currentUser;
      const isLeader = team.leader_id === user.id;
      const isGuide = team.guide_id === user.id;

      let html = `
        <div style="max-width:1100px; margin:0 auto;">
          <div style="margin-bottom:1.5rem;">
            <button class="btn btn-secondary btn-sm" onclick="App.switchTab('teams')">← Back to Teams</button>
          </div>

          <div class="card" style="margin-bottom:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
              <div>
                <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom:0.5rem; flex-wrap:wrap;">
                  <span class="badge" style="background:#1e293b; color:#94a3b8;">Academic Year: ${team.academic_year}</span>
                  <span class="badge" style="background:rgba(99, 102, 241, 0.15); color:#a5b4fc; border:1px solid rgba(99, 102, 241, 0.35); text-transform:none; font-size:0.8rem; font-weight:600;">📚 ${team.course}</span>
                </div>
                <h2 style="font-size:1.85rem; font-weight:700;">${team.name}</h2>
                <div style="font-size:0.9rem; color:var(--text-muted); margin-top:0.25rem;">
                  Leader: <strong>${team.leader ? team.leader.name : 'Unknown'}</strong> (${team.leader ? team.leader.email : ''})
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:0.8rem; color:var(--text-muted);">Faculty Guide</div>
                <div style="font-weight:600; font-size:1.1rem; color:#34d399;">
                  ${team.guide ? team.guide.name : 'None Assigned'}
                </div>
                ${user.role === 'admin' ? `
                  <button class="btn btn-secondary btn-sm" style="margin-top:0.5rem;" onclick="App.openAssignGuideModal(${team.id}, '${team.name.replace(/'/g, "\\'")}')">Change Guide</button>
                ` : ''}
              </div>
            </div>

            <!-- Members section -->
            <div style="margin-top:1.5rem; border-top:1px solid var(--border-color); padding-top:1.25rem;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <h4 style="font-size:1rem; font-weight:600;">Team Members (${team.members.length}/4)</h4>
                ${isLeader && team.members.length < 4 ? `
                  <button class="btn btn-primary btn-sm" onclick="App.openAddMemberModal(${team.id})">➕ Add Member</button>
                ` : ''}
              </div>

              <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:0.75rem;">
                ${team.members.map(m => `
                  <div style="background:var(--bg-input); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:0.75rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                      <div style="font-weight:600; font-size:0.9rem;">${m.name} ${m.id === team.leader_id ? '⭐ (Leader)' : ''}</div>
                      <div style="font-size:0.75rem; color:var(--text-muted);">${m.email}</div>
                    </div>
                    ${isLeader && m.id !== team.leader_id ? `
                      <button class="btn btn-danger btn-sm" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="App.removeMember(${team.id}, ${m.id})">Remove</button>
                    ` : ''}
                  </div>
                `).join('')}
              </div>
            </div>
          </div>

          <!-- Proposal Section -->
          <div class="card" style="margin-bottom:1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:1rem;">
              <div>
                <h3 style="font-size:1.25rem; font-weight:700;">Project Proposal</h3>
                <p style="color:var(--text-muted); font-size:0.85rem;">Scope statement and technical stack</p>
              </div>
              <div>
                ${proposal ? `
                  <span class="badge badge-${proposal.status.toLowerCase()}">${proposal.status}</span>
                ` : ''}
              </div>
            </div>
      `;

      if (!proposal) {
        html += `
          <div style="text-align:center; padding:2rem 1rem; background:var(--bg-input); border-radius:var(--radius-md);">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📑</div>
            <p style="color:var(--text-muted); margin-bottom:1rem;">No proposal has been submitted for this team yet.</p>
            ${isLeader ? `
              ${team.members.length >= 2 && team.members.length <= 4 ? `
                <button class="btn btn-primary" onclick="App.openSubmitProposalModal(${team.id})">📝 Submit Project Proposal</button>
              ` : `
                <div style="color:#f87171; font-size:0.85rem;">⚠️ Team size must be between 2 and 4 members to submit a proposal (Current size: ${team.members.length}).</div>
              `}
            ` : `
              <div style="color:var(--text-dim); font-size:0.85rem;">Only the team leader can submit the proposal.</div>
            `}
          </div>
        `;
      } else {
        html += `
          <div style="background:var(--bg-input); padding:1.25rem; border-radius:var(--radius-md); margin-bottom:1rem;">
            <h4 style="font-size:1.15rem; font-weight:700; color:#60a5fa; margin-bottom:0.75rem;">${proposal.title}</h4>
            <div style="margin-bottom:0.75rem;">
              <strong style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase;">Domain:</strong>
              <span style="font-size:0.9rem; margin-left:0.35rem;">${proposal.domain}</span>
              <strong style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase; margin-left:1.5rem;">Tech Stack:</strong>
              <span style="font-size:0.9rem; margin-left:0.35rem;">${proposal.tech_stack}</span>
            </div>
            <div style="margin-bottom:0.75rem;">
              <strong style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase;">Problem Statement:</strong>
              <div style="font-size:0.9rem; margin-top:0.25rem; line-height:1.5;">${proposal.problem_statement}</div>
            </div>
            <div>
              <strong style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase;">Abstract:</strong>
              <div style="font-size:0.9rem; margin-top:0.25rem; line-height:1.5;">${proposal.abstract}</div>
            </div>
            ${proposal.faculty_comment ? `
              <div style="margin-top:1rem; padding:0.75rem; background:rgba(245, 158, 11, 0.1); border-left:3px solid var(--warning); border-radius:var(--radius-sm);">
                <strong style="color:#fbbf24; font-size:0.85rem;">Faculty Review Comment:</strong>
                <div style="font-size:0.9rem; margin-top:0.2rem;">${proposal.faculty_comment}</div>
              </div>
            ` : ''}
          </div>

          <div style="display:flex; gap:0.75rem; flex-wrap:wrap;">
            ${isLeader && (proposal.status === 'SUBMITTED' || proposal.status === 'CHANGES_REQUESTED') ? `
              <button class="btn btn-warning btn-sm" onclick="App.openEditProposalModal()">✏️ Edit Proposal</button>
            ` : ''}

            ${isGuide && proposal.status === 'SUBMITTED' ? `
              <button class="btn btn-success btn-sm" onclick="App.openReviewProposalModal(${proposal.id})">🔍 Review & Approve Proposal</button>
            ` : ''}
          </div>
        `;
      }

      html += `</div>`;

      // Weekly Progress Updates Section
      html += `
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
            <div>
              <h3 style="font-size:1.25rem; font-weight:700;">Weekly Progress & Feedback</h3>
              <p style="color:var(--text-muted); font-size:0.85rem;">Milestone delivery and faculty evaluations</p>
            </div>
            <div>
              ${proposal && proposal.status === 'APPROVED' ? `
                <button class="btn btn-primary btn-sm" onclick="App.openAddProgressModal(${team.id})">➕ Log Weekly Progress</button>
              ` : `
                <span style="font-size:0.85rem; color:var(--text-dim);">Progress logging unlocked after proposal approval</span>
              `}
            </div>
          </div>
      `;

      if (progressList.length === 0) {
        html += `
          <div style="text-align:center; padding:2.5rem 1rem; color:var(--text-muted);">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">⏱️</div>
            <div>No weekly progress updates recorded yet.</div>
          </div>
        `;
      } else {
        html += `<div class="timeline">`;
        for (const prog of progressList) {
          const maxFeedbackMarks = prog.feedbacks && prog.feedbacks.length > 0 ? prog.feedbacks[0].marks : null;

          html += `
            <div class="timeline-item">
              <div class="timeline-dot completed">✓</div>
              <div style="background:var(--bg-input); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:1.25rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem; flex-wrap:wrap; gap:0.5rem;">
                  <div>
                    <span style="font-weight:700; font-size:1.05rem; color:#60a5fa;">Week ${prog.week_number} Update</span>
                    <span style="font-size:0.8rem; color:var(--text-muted); margin-left:0.5rem;">(${new Date(prog.created_at).toLocaleDateString()})</span>
                  </div>
                  <div>
                    <span class="badge badge-approved" style="font-size:0.85rem;">${prog.completion_percent}% Complete</span>
                    ${maxFeedbackMarks !== null ? `<span class="badge" style="background:#065f46; color:#a7f3d0; margin-left:0.4rem;">Grade: ${maxFeedbackMarks}/100</span>` : ''}
                  </div>
                </div>

                <div style="font-size:0.95rem; line-height:1.5; margin-bottom:0.75rem;">${prog.description}</div>

                ${prog.deliverable_url ? `
                  <div style="margin-bottom:0.75rem;">
                    <a href="${prog.deliverable_url}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; font-size:0.85rem; text-decoration:none; display:inline-flex; align-items:center; gap:0.3rem;">
                      🔗 View Deliverable / Artifact
                    </a>
                  </div>
                ` : ''}

                <!-- Nested Faculty Feedback -->
                <div style="border-top:1px solid rgba(255, 255, 255, 0.08); padding-top:0.75rem; margin-top:0.75rem;">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <span style="font-size:0.85rem; font-weight:600; color:var(--text-muted);">Faculty Feedback</span>
                    ${isGuide ? `
                      <button class="btn btn-secondary btn-sm" style="font-size:0.75rem; padding:0.25rem 0.5rem;" onclick="App.openFeedbackModal(${prog.id}, ${prog.week_number})">💬 Give Feedback & Grade</button>
                    ` : ''}
                  </div>

                  ${prog.feedbacks && prog.feedbacks.length > 0 ? `
                    ${prog.feedbacks.map(f => `
                      <div style="background:rgba(15, 23, 42, 0.6); padding:0.75rem; border-radius:var(--radius-sm); border-left:3px solid var(--success); margin-bottom:0.5rem;">
                        <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted); margin-bottom:0.25rem;">
                          <span>By Guide: ${f.faculty ? f.faculty.name : 'Assigned Guide'}</span>
                          ${f.marks !== null ? `<strong style="color:#34d399;">Marks: ${f.marks}/100</strong>` : ''}
                        </div>
                        <div style="font-size:0.9rem; font-style:italic;">"${f.comments}"</div>
                      </div>
                    `).join('')}
                  ` : `
                    <div style="font-size:0.85rem; color:var(--text-dim); font-style:italic;">No feedback posted yet for week ${prog.week_number}.</div>
                  `}
                </div>
              </div>
            </div>
          `;
        }
        html += `</div>`;
      }

      html += `</div></div>`;
      area.innerHTML = html;
    } catch (err) {
      area.innerHTML = `<div class="card" style="color:var(--danger); text-align:center; padding:2rem;">Error loading team detail: ${err.message}</div>`;
    }
  },

  // --------------------------------------------------------------------------
  // Admin User Management View
  // --------------------------------------------------------------------------
  async renderAdminUsersView() {
    const area = document.getElementById('tab-content-area');
    area.innerHTML = `
      <div style="max-width:1100px; margin:0 auto;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
          <div>
            <h2 style="font-size:1.75rem; font-weight:700;">User Management</h2>
            <p style="color:var(--text-muted);">Admin Provisioning for Students and Faculty</p>
          </div>
          <div>
            <button class="btn btn-primary" onclick="App.openCreateUserModal()">➕ Provision New User</button>
          </div>
        </div>

        <div class="card">
          <div style="padding:1rem; background:rgba(59, 130, 246, 0.08); border-radius:var(--radius-md); margin-bottom:1.5rem; font-size:0.9rem;">
            ℹ️ System Administrators can provision new accounts. Passwords must be at least 8 characters. Email must be unique.
          </div>

          <div style="text-align:center; padding:2rem; color:var(--text-muted);">
            <p>Click the button above to provision a new student or faculty member into the university portal.</p>
          </div>
        </div>
      </div>
    `;
  },

  // --------------------------------------------------------------------------
  // Modals & Action Handlers
  // --------------------------------------------------------------------------
  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('active');
  },

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
  },

  openCreateTeamModal() {
    this.openModal('modal-create-team');
  },

  async handleCreateTeam(e) {
    e.preventDefault();
    const name = document.getElementById('team-name-input').value.trim();
    const year = document.getElementById('team-year-input').value.trim();
    const course = document.getElementById('team-course-input')?.value.trim() || 'CS501 - Capstone Project';
    try {
      await API.createTeam(name, year, course);
      this.closeModal('modal-create-team');
      this.showToast(`Team '${name}' for course '${course}' created successfully!`, 'success');
      this.renderTeamsView();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openAddMemberModal(teamId) {
    document.getElementById('add-member-team-id').value = teamId;
    this.openModal('modal-add-member');
  },

  async handleAddMember(e) {
    e.preventDefault();
    const teamId = document.getElementById('add-member-team-id').value;
    const email = document.getElementById('add-member-email').value.trim();
    try {
      await API.addTeamMember(teamId, email);
      this.closeModal('modal-add-member');
      this.showToast(`Student ${email} added to team!`, 'success');
      this.openTeamDetail(teamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  async removeMember(teamId, userId) {
    if (!confirm('Are you sure you want to remove this member from the team?')) return;
    try {
      await API.removeTeamMember(teamId, userId);
      this.showToast('Member removed successfully', 'success');
      this.openTeamDetail(teamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openAssignGuideModal(teamId, teamName) {
    document.getElementById('assign-guide-team-id').value = teamId;
    document.getElementById('assign-guide-team-name').innerText = teamName;
    this.openModal('modal-assign-guide');
  },

  async handleAssignGuide(e) {
    e.preventDefault();
    const teamId = document.getElementById('assign-guide-team-id').value;
    const facultyId = document.getElementById('assign-guide-faculty-id').value;
    try {
      await API.assignGuide(teamId, facultyId);
      this.closeModal('modal-assign-guide');
      this.showToast('Faculty guide assigned successfully!', 'success');
      if (this.state.currentTab === 'teams') {
        this.renderTeamsView();
      } else {
        this.openTeamDetail(teamId);
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openSubmitProposalModal(teamId) {
    document.getElementById('proposal-team-id').value = teamId;
    this.openModal('modal-submit-proposal');
  },

  async handleSubmitProposal(e) {
    e.preventDefault();
    const teamId = document.getElementById('proposal-team-id').value;
    const payload = {
      title: document.getElementById('prop-title').value.trim(),
      domain: document.getElementById('prop-domain').value.trim(),
      tech_stack: document.getElementById('prop-tech-stack').value.trim(),
      problem_statement: document.getElementById('prop-problem').value.trim(),
      abstract: document.getElementById('prop-abstract').value.trim(),
    };
    try {
      await API.submitProposal(teamId, payload);
      this.closeModal('modal-submit-proposal');
      this.showToast('Proposal submitted successfully for guide review!', 'success');
      this.openTeamDetail(teamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openEditProposalModal() {
    const prop = this.state.activeProposal;
    if (!prop) return;
    document.getElementById('edit-prop-team-id').value = prop.team_id;
    document.getElementById('edit-prop-title').value = prop.title;
    document.getElementById('edit-prop-domain').value = prop.domain;
    document.getElementById('edit-prop-tech-stack').value = prop.tech_stack;
    document.getElementById('edit-prop-problem').value = prop.problem_statement;
    document.getElementById('edit-prop-abstract').value = prop.abstract;
    this.openModal('modal-edit-proposal');
  },

  async handleEditProposal(e) {
    e.preventDefault();
    const teamId = document.getElementById('edit-prop-team-id').value;
    const payload = {
      title: document.getElementById('edit-prop-title').value.trim(),
      domain: document.getElementById('edit-prop-domain').value.trim(),
      tech_stack: document.getElementById('edit-prop-tech-stack').value.trim(),
      problem_statement: document.getElementById('edit-prop-problem').value.trim(),
      abstract: document.getElementById('edit-prop-abstract').value.trim(),
    };
    try {
      await API.updateProposal(teamId, payload);
      this.closeModal('modal-edit-proposal');
      this.showToast('Proposal edited and resubmitted to guide!', 'success');
      this.openTeamDetail(teamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openReviewProposalModal(proposalId) {
    document.getElementById('review-prop-id').value = proposalId;
    this.openModal('modal-review-proposal');
  },

  async handleReviewProposal(e) {
    e.preventDefault();
    const proposalId = document.getElementById('review-prop-id').value;
    const decision = document.getElementById('review-decision').value;
    const comment = document.getElementById('review-comment').value.trim();

    if (decision === 'CHANGES_REQUESTED' && !comment) {
      this.showToast('A feedback comment is required when requesting changes.', 'error');
      return;
    }

    try {
      await API.reviewProposal(proposalId, decision, comment);
      this.closeModal('modal-review-proposal');
      this.showToast(`Proposal review recorded: ${decision}!`, 'success');
      this.openTeamDetail(this.state.activeTeamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openAddProgressModal(teamId) {
    document.getElementById('progress-team-id').value = teamId;
    // Suggest next week number
    const nextWeek = (this.state.activeProgress.length || 0) + 1;
    document.getElementById('progress-week-num').value = Math.min(nextWeek, 20);
    this.openModal('modal-add-progress');
  },

  async handleAddProgress(e) {
    e.preventDefault();
    const teamId = document.getElementById('progress-team-id').value;
    const payload = {
      week_number: Number(document.getElementById('progress-week-num').value),
      completion_percent: Number(document.getElementById('progress-percent').value),
      description: document.getElementById('progress-desc').value.trim(),
      deliverable_url: document.getElementById('progress-url').value.trim() || null,
    };

    try {
      await API.createProgressUpdate(teamId, payload);
      this.closeModal('modal-add-progress');
      this.showToast(`Week ${payload.week_number} progress update recorded!`, 'success');
      this.openTeamDetail(teamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openFeedbackModal(progressId, weekNum) {
    document.getElementById('feedback-progress-id').value = progressId;
    document.getElementById('feedback-week-label').innerText = `Week ${weekNum}`;
    this.openModal('modal-add-feedback');
  },

  async handleAddFeedback(e) {
    e.preventDefault();
    const progressId = document.getElementById('feedback-progress-id').value;
    const marks = document.getElementById('feedback-marks').value;
    const comments = document.getElementById('feedback-comments').value.trim();

    try {
      await API.addFeedback(progressId, comments, marks);
      this.closeModal('modal-add-feedback');
      this.showToast('Faculty feedback and grade recorded!', 'success');
      this.openTeamDetail(this.state.activeTeamId);
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  openCreateUserModal() {
    this.openModal('modal-create-user');
  },

  async handleCreateUser(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('user-name-input').value.trim(),
      email: document.getElementById('user-email-input').value.trim(),
      password: document.getElementById('user-pass-input').value,
      role: document.getElementById('user-role-input').value,
    };

    try {
      await API.createUser(payload);
      this.closeModal('modal-create-user');
      this.showToast(`User ${payload.email} provisioned successfully!`, 'success');
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },
};

// Initialize App on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
