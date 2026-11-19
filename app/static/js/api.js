/**
 * ProjectHub API Client Module
 */
const API = {
  TOKEN_KEY: 'projecthub_token',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  clearToken() {
    localStorage.removeItem(this.TOKEN_KEY);
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(endpoint, {
        ...options,
        headers,
      });

      if (response.status === 401 && endpoint !== '/auth/login') {
        this.clearToken();
        window.dispatchEvent(new CustomEvent('auth:expired'));
        throw new Error('Session expired or unauthorized. Please log in again.');
      }

      const contentType = response.headers.get('content-type') || '';
      let data = null;
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        let errorMsg = 'An unexpected error occurred.';
        if (data && typeof data === 'object') {
          if (data.detail) {
            if (Array.isArray(data.detail)) {
              errorMsg = data.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg}`).join('\n');
            } else {
              errorMsg = data.detail;
            }
          } else if (data.message) {
            errorMsg = data.message;
          }
        }
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth & User
  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const data = await this.request('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (data.access_token) {
      this.setToken(data.access_token);
    }
    return data;
  },

  async getMe() {
    return this.request('/users/me');
  },

  async createUser(payload) {
    return this.request('/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Dashboard
  async getDashboard() {
    return this.request('/dashboard');
  },

  // Teams
  async getTeams() {
    return this.request('/teams');
  },

  async getTeam(id) {
    return this.request(`/teams/${id}`);
  },

  async createTeam(name, academicYear) {
    return this.request('/teams', {
      method: 'POST',
      body: JSON.stringify({
        name,
        academic_year: academicYear,
      }),
    });
  },

  async addTeamMember(teamId, studentEmail) {
    return this.request(`/teams/${teamId}/members`, {
      method: 'POST',
      body: JSON.stringify({ student_email: studentEmail }),
    });
  },

  async removeTeamMember(teamId, userId) {
    return this.request(`/teams/${teamId}/members/${userId}`, {
      method: 'DELETE',
    });
  },

  async assignGuide(teamId, facultyId) {
    return this.request(`/teams/${teamId}/guide`, {
      method: 'PUT',
      body: JSON.stringify({ faculty_id: Number(facultyId) }),
    });
  },

  // Proposals
  async getTeamProposal(teamId) {
    return this.request(`/teams/${teamId}/proposal`);
  },

  async submitProposal(teamId, payload) {
    return this.request(`/teams/${teamId}/proposal`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateProposal(teamId, payload) {
    return this.request(`/teams/${teamId}/proposal`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async reviewProposal(proposalId, decision, comment) {
    return this.request(`/proposals/${proposalId}/review`, {
      method: 'PATCH',
      body: JSON.stringify({ decision, comment }),
    });
  },

  // Progress & Feedback
  async getTeamProgress(teamId) {
    return this.request(`/teams/${teamId}/progress`);
  },

  async createProgressUpdate(teamId, payload) {
    return this.request(`/teams/${teamId}/progress`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async addFeedback(progressId, comments, marks) {
    const body = { comments };
    if (marks !== undefined && marks !== null && marks !== '') {
      body.marks = Number(marks);
    }
    return this.request(`/progress/${progressId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};
