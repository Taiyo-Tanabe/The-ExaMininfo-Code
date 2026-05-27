import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'
import SchoolAutocomplete from '../components/SchoolAutocomplete'

const ORG_COLORS = [
  ['#29B6F6','#0288D1'],['#66BB6A','#2E7D32'],['#AB47BC','#6A1B9A'],
  ['#FF7043','#BF360C'],['#26C6DA','#00838F'],['#EC407A','#880E4F'],
]
function OrgIcon({ name, url, posX = 50, posY = 50, size = 32 }) {
  const [bg, fg] = ORG_COLORS[(name?.charCodeAt(0) ?? 0) % ORG_COLORS.length]
  if (url) return (
    <img src={url} alt={name} style={{
      width: size, height: size, borderRadius: '50%', flexShrink: 0,
      objectFit: 'cover', objectPosition: `${posX}% ${posY}%`,
    }} />
  )
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%', flexShrink: 0,
      background: `linear-gradient(135deg, ${bg}, ${fg})`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.42, fontWeight: 800, color: '#fff',
    }}>
      {name?.charAt(0).toUpperCase()}
    </div>
  )
}

function formatDate(iso) {
  if (!iso) return '日時未定'
  return new Date(iso).toLocaleString('ja-JP', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function StatusBadge({ status }) {
  if (status === 'attending')     return <span className="badge" style={{ background: 'rgba(102,187,106,0.25)', color: '#2e7d32' }}>参加予定</span>
  if (status === 'not_attending') return <span className="badge" style={{ background: 'rgba(239,83,80,0.2)',  color: '#c62828' }}>不参加</span>
  if (status === 'pending')       return <span className="badge" style={{ background: 'rgba(255,193,7,0.2)',  color: '#856404' }}>承認待ち</span>
  return null
}

export default function EventsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [schools, setSchools] = useState([])
  const [courses, setCourses] = useState([])
  const [schoolId, setSchoolId] = useState(null)
  const [department, setDepartment] = useState('')
  const [myOrgs, setMyOrgs] = useState(!!user)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getSchools({ limit: 2000 }).then(d => setSchools(d.items ?? [])).catch(() => {})
  }, [])

  // 大学が変わったらコース一覧を更新
  useEffect(() => {
    setDepartment('')
    if (!schoolId) { setCourses([]); return }
    api.getCourses({ school_id: Number(schoolId), limit: 200 })
      .then(d => setCourses(d.items ?? []))
      .catch(() => setCourses([]))
  }, [schoolId])

  const load = useCallback(() => {
    setLoading(true)
    const params = { limit: 100 }
    if (schoolId)   params.school_id   = schoolId
    if (department) params.department  = department
    if (myOrgs && user) params.my_orgs = true
    api.getEvents(params)
      .then(setData)
      .catch(() => setError('読み込みに失敗しました'))
      .finally(() => setLoading(false))
  }, [schoolId, department, myOrgs, user])

  useEffect(() => { load() }, [load])

  async function handleAttend(event, newStatus) {
    try {
      if (event.my_status === newStatus) await api.cancelAttendance(event.id)
      else await api.attendEvent(event.id, newStatus)
      load()
    } catch (e) { alert(e.message) }
  }

  if (error) return <div className="container"><p className="muted">{error}</p></div>

  const events = data?.items ?? []

  return (
    <div className="container" style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>イベント</h1>
        {user && (
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/events/new')}>
            + 新規イベント
          </button>
        )}
      </div>

      {/* フィルタ */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: '0.85rem 1rem', marginBottom: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px', minWidth: 0 }}>
            <SchoolAutocomplete
              schools={schools}
              schoolId={schoolId}
              onSelect={setSchoolId}
              placeholder="🏫 大学で絞り込む..."
            />
          </div>
          {schoolId && courses.length > 0 && (
            <select
              className="input"
              style={{ flex: '1 1 160px', minWidth: 0 }}
              value={department}
              onChange={e => setDepartment(e.target.value)}
            >
              <option value="">すべてのコース</option>
              {courses.map(c => (
                <option key={c.id} value={c.name}>{c.name}</option>
              ))}
            </select>
          )}
        </div>
        {user && (
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', userSelect: 'none', fontSize: '0.88rem' }}>
            <input type="checkbox" checked={myOrgs} onChange={e => setMyOrgs(e.target.checked)} />
            自分の所属団体のイベントのみ
          </label>
        )}
      </div>

      {loading ? (
        <div className="loading">読み込み中...</div>
      ) : (
        <>
          {events.length === 0 && (
            <p className="muted" style={{ textAlign: 'center', padding: '3rem' }}>
              {myOrgs && !user
                ? 'ログインすると所属団体のイベントが表示されます'
                : 'イベントがありません'}
            </p>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {events.map(ev => (
              <div key={ev.id} className="card" style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'block' }}>
                      <Link to={`/events/${ev.id}`} style={{ fontWeight: 700, fontSize: '1.05rem', textDecoration: 'none', color: 'var(--text)' }}>
                        {ev.title ?? <span className="muted" style={{ fontStyle: 'italic' }}>非公開</span>}
                      </Link>
                    </div>
                    {ev.org_name && (
                      <Link to={`/orgs/${ev.org_id}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', color: 'var(--primary)', textDecoration: 'none', marginTop: '0.25rem' }}>
                        <OrgIcon name={ev.org_name} url={ev.org_icon_url} posX={ev.org_icon_position_x} posY={ev.org_icon_position_y} size={18} />
                        {ev.org_name}
                      </Link>
                    )}
                    <div style={{ marginTop: '0.4rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                      <span className="muted" style={{ fontSize: '0.85rem' }}>
                        📅 {formatDate(ev.start_at)}{ev.end_at ? ` 〜 ${formatDate(ev.end_at)}` : ''}
                      </span>
                      {ev.location && (
                        <span className="muted" style={{ fontSize: '0.85rem' }}>📍 {ev.location}</span>
                      )}
                    </div>
                    {ev.description && (
                      <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)', whiteSpace: 'pre-line' }}>
                        {ev.description.length > 100 ? ev.description.slice(0, 100) + '…' : ev.description}
                      </p>
                    )}
                    <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span className="muted" style={{ fontSize: '0.82rem' }}>
                        👥 {ev.attendee_count}{ev.max_participants ? ` / ${ev.max_participants}` : ''} 人
                      </span>
                      <StatusBadge status={ev.my_status} />
                      {ev.requires_view_approval && <span className="badge" style={{ fontSize: '0.75rem' }}>閲覧承認が必要</span>}
                      {ev.requires_join_approval && <span className="badge" style={{ fontSize: '0.75rem' }}>参加承認が必要</span>}
                    </div>
                  </div>

                  {user && ev.title && ev.my_status !== 'pending' && !ev.requires_view_approval && (
                    <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                      <button
                        className={`btn btn-sm ${ev.my_status === 'attending' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => handleAttend(ev, 'attending')}
                      >
                        {ev.my_status === 'attending' ? '✓ 参加' : '参加する'}
                      </button>
                      <button
                        className="btn btn-sm btn-secondary"
                        style={ev.my_status === 'not_attending' ? { opacity: 0.6 } : {}}
                        onClick={() => handleAttend(ev, 'not_attending')}
                      >
                        不参加
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
