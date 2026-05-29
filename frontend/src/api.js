// 開発時は .env の VITE_API_BASE=http://localhost:8000
// 本番は空文字（FastAPI と同一オリジンで配信するため不要）
const BASE = import.meta.env.VITE_API_BASE ?? ''

function token() {
  return localStorage.getItem('token')
}

function authHeaders() {
  const t = token()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'エラーが発生しました' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

function qs(params) {
  const p = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== ''))
  return new URLSearchParams(p).toString()
}

export const api = {
  // Schools
  getSchools:    (p = {}) => request(`/schools/?${qs(p)}`),
  getSchool:     (id)     => request(`/schools/${id}`),
  createSchool:  (data)   => request('/schools/', { method: 'POST', body: JSON.stringify(data) }),
  updateSchool:  (id, data) => request(`/schools/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSchool:  (id)     => request(`/schools/${id}`, { method: 'DELETE' }),
  reactToSchool: (id, data) => request(`/schools/${id}/react`, { method: 'POST', body: JSON.stringify(data) }),

  // Courses
  getCourses:    (p = {})   => request(`/courses/?${qs(p)}`),
  createCourse:  (data)     => request('/courses/', { method: 'POST', body: JSON.stringify(data) }),
  updateCourse:  (id, data) => request(`/courses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCourse:  (id)       => request(`/courses/${id}`, { method: 'DELETE' }),
  reactToCourse: (id, data) => request(`/courses/${id}/react`, { method: 'POST', body: JSON.stringify(data) }),

  // Incidents
  getIncidents:     (p = {})   => request(`/incidents/?${qs(p)}`),
  getIncident:      (id)       => request(`/incidents/${id}`),
  createIncident:   (data)     => request('/incidents/', { method: 'POST', body: JSON.stringify(data) }),
  updateIncident:   (id, data) => request(`/incidents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteIncident:   (id)       => request(`/incidents/${id}`, { method: 'DELETE' }),
  reactToIncident:  (id, data) => request(`/incidents/${id}/react`, { method: 'POST', body: JSON.stringify(data) }),

  // Posts
  getPost:     (id)       => request(`/posts/${id}`),
  getPosts:    (p = {})   => request(`/posts/?${qs(p)}`),
  createPost:  (data)     => request('/posts/', { method: 'POST', body: JSON.stringify(data) }),
  updatePost:  (id, data) => request(`/posts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePost:  (id)       => request(`/posts/${id}`, { method: 'DELETE' }),

  // Reposts
  getAllReposts: (p = {})        => request(`/reposts/?${qs(p)}`),
  getReposts:   (postId, p = {}) => request(`/posts/${postId}/reposts?${qs(p)}`),
  createRepost: (postId, data)   => request(`/posts/${postId}/reposts`, { method: 'POST', body: JSON.stringify(data) }),
  updateRepost: (id, data)       => request(`/reposts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRepost: (id)             => request(`/reposts/${id}`, { method: 'DELETE' }),

  // Reviews
  getAllReviews:  (p = {})           => request(`/schools/reviews/?${qs(p)}`),
  getReviews:    (schoolId, p = {}) => request(`/schools/${schoolId}/reviews?${qs(p)}`),
  createReview:  (schoolId, data)   => request(`/schools/${schoolId}/reviews`, { method: 'POST', body: JSON.stringify(data) }),
  deleteReview:  (id)               => request(`/schools/reviews/${id}`, { method: 'DELETE' }),
  getUserReviews: (userId, p = {})  => request(`/users/${userId}/reviews?${qs(p)}`),

  // Reactions
  reactToPost:   (id, data) => request(`/posts/${id}/react`,   { method: 'POST', body: JSON.stringify(data) }),
  reactToRepost: (id, data) => request(`/reposts/${id}/react`, { method: 'POST', body: JSON.stringify(data) }),

  // Users
  getUsers:        (p = {})  => request(`/users/?${qs(p)}`),
  updateUserRole:  (id, data) => request(`/users/${id}/role`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateProfile:   (data)    => request('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
  changePassword:  (data)    => request('/users/me/change-password', { method: 'POST', body: JSON.stringify(data) }),
  getUserProfile:  (id)      => request(`/users/${id}/profile`),
  followUser:      (id)      => request(`/users/${id}/follow`, { method: 'POST' }),
  unfollowUser:    (id)      => request(`/users/${id}/follow`, { method: 'DELETE' }),
  getFollowStatus: (id)      => request(`/users/${id}/follow-status`),
  getFollowers:    (id, p={})=> request(`/users/${id}/followers?${qs(p)}`),
  getFollowing:    (id, p={})=> request(`/users/${id}/following?${qs(p)}`),
  deleteUser:        (id)       => request(`/users/${id}`, { method: 'DELETE' }),
  deleteMyAccount:   (data)     => request('/users/me', { method: 'DELETE', body: JSON.stringify(data) }),
  getBlockedEmails:  (p = {})   => request(`/users/blocked-emails?${qs(p)}`),
  unblockEmail:      (id)       => request(`/users/blocked-emails/${id}`, { method: 'DELETE' }),

  // Auth
  login:    (data) => request('/users/login',    { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/users/register', { method: 'POST', body: JSON.stringify(data) }),
  getMe:    ()     => request('/users/me'),

  // Avatar
  uploadAvatar: (file) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/users/me/avatar`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    }).then(async r => {
      if (!r.ok) { const e = await r.json().catch(() => ({ detail: 'エラー' })); throw new Error(e.detail) }
      return r.json()
    })
  },

  // User search (for @mentions)
  searchUsers: (q = '', limit = 8) => request(`/users/search?${qs({ q, limit })}`),

  // Site content
  getSiteContent:    (key)        => request(`/settings/${key}`),
  updateSiteContent: (key, value) => request(`/settings/${key}`, { method: 'PUT', body: JSON.stringify({ value }) }),

  // Reports
  createReport:           (data)             => request('/reports/', { method: 'POST', body: JSON.stringify(data) }),
  getReports:             (p = {})           => request(`/reports/?${qs(p)}`),
  deleteReport:           (id)               => request(`/reports/${id}`, { method: 'DELETE' }),
  deleteReportedContent:  (type, id)         => request(`/reports/content/${type}/${id}`, { method: 'DELETE' }),

  // User approval (admin)
  getPendingUsers:   (p = {})  => request(`/users/pending?${qs(p)}`),
  approveUser:       (id)      => request(`/users/${id}/approve`, { method: 'PATCH' }),
}
