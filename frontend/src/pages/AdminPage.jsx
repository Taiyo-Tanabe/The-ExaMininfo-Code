import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'
import SchoolAutocomplete from '../components/SchoolAutocomplete'
import CourseSelect from '../components/CourseSelect'

// ── ユーザー管理 ──
function UsersTab() {
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')

  function load() { api.getUsers({ limit: 200 }).then(setData) }
  useEffect(load, [])

  const items = (data?.items ?? []).filter(u => u.name.includes(q) || u.email.includes(q))

  async function toggleRole(userId, role) {
    const newRole = role === 'admin' ? 'user' : 'admin'
    if (!confirm(`ロールを「${newRole}」に変更しますか？`)) return
    await api.updateUserRole(userId, { role: newRole }); load()
  }

  async function handleDeleteUser(userId, name, email) {
    if (!confirm(`「${name}」(${email}) を削除しますか？\nこのメールアドレスは再登録できなくなります。`)) return
    try {
      await api.deleteUser(userId)
      load()
    } catch (e) { alert(e.message) }
  }

  return (
    <div>
      <div className="search-bar"><input placeholder="名前・メールで検索..." value={q} onChange={e => setQ(e.target.value)} /></div>
      {items.map(u => (
        <div key={u.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <p style={{ fontWeight: 700 }}>{u.name}</p>
            <p className="muted" style={{ fontSize: '0.85rem' }}>{u.email}</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span className="badge" style={{ background: u.role === 'admin' ? 'rgba(255,102,0,0.25)' : undefined, color: u.role === 'admin' ? 'var(--primary)' : undefined }}>{u.role}</span>
            <button className="btn btn-secondary btn-sm" onClick={() => toggleRole(u.id, u.role)}>
              {u.role === 'admin' ? '降格' : '管理者に昇格'}
            </button>
            <button
              className="btn btn-secondary btn-sm"
              style={{ color: 'var(--danger)' }}
              onClick={() => handleDeleteUser(u.id, u.name, u.email)}
            >
              削除
            </button>
          </div>
        </div>
      ))}
      {!items.length && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>ユーザーがいません</p>}
    </div>
  )
}

// ── 学校管理 ──
function SchoolsTab() {
  const [data, setData]       = useState(null)
  const [q, setQ]             = useState('')
  const [sort, setSort]       = useState('name-asc')
  const [editingId, setEditingId]     = useState(null)
  const [editName, setEditName]       = useState('')
  const [editYomi, setEditYomi]       = useState('')
  const [editPref, setEditPref]       = useState('')
  const [editPrefYomi, setEditPrefYomi] = useState('')
  const [name, setName]           = useState('')
  const [yomi, setYomi]           = useState('')
  const [pref, setPref]           = useState('')
  const [prefYomi, setPrefYomi]   = useState('')
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)

  function load() {
    const [sort_by, order] = sort.split('-')
    api.getSchools({ q: q || undefined, limit: 100, sort_by, order }).then(setData)
  }
  useEffect(load, [q, sort])

  async function handleCreate() {
    if (!name.trim()) { setError('大学名を入力してください'); return }
    if (!pref.trim()) { setError('都道府県を入力してください'); return }
    setLoading(true); setError('')
    try { await api.createSchool({ name: name.trim(), yomi: yomi.trim() || null, prefecture: pref.trim(), prefecture_yomi: prefYomi.trim() || null }); setName(''); setYomi(''); setPref(''); setPrefYomi(''); load() }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function saveEdit() {
    await api.updateSchool(editingId, { name: editName, yomi: editYomi || null, prefecture: editPref, prefecture_yomi: editPrefYomi || null })
    setEditingId(null); load()
  }

  async function handleDelete(id, n) {
    if (!confirm(`「${n}」を削除しますか？\n関連するコース・事件・ポストも削除されます。`)) return
    await api.deleteSchool(id); load()
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>大学を追加</h3>
        <div className="form-group"><label>大学名</label><input value={name} onChange={e => setName(e.target.value)} placeholder="〇〇大学" /></div>
        <div className="form-group"><label>よみがな（任意）</label><input value={yomi} onChange={e => setYomi(e.target.value)} placeholder="まるまるこうとうがっこう" /></div>
        <div className="form-group"><label>都道府県</label><input value={pref} onChange={e => setPref(e.target.value)} placeholder="東京都" /></div>
        <div className="form-group"><label>都道府県よみがな（任意）</label><input value={prefYomi} onChange={e => setPrefYomi(e.target.value)} placeholder="とうきょうと" /></div>
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" onClick={handleCreate} disabled={loading}>{loading ? '追加中...' : '追加する'}</button>
      </div>
      <div className="search-bar">
        <input placeholder="大学名で検索..." value={q} onChange={e => setQ(e.target.value)} />
        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="name-asc">名前（昇順）</option>
          <option value="name-desc">名前（降順）</option>
          <option value="prefecture-asc">都道府県（昇順）</option>
          <option value="prefecture-desc">都道府県（降順）</option>
        </select>
      </div>
      {data?.items.map(s => (
        <div key={s.id} className="card">
          {editingId === s.id ? (
            <div>
              <div className="form-group"><label>大学名</label><input value={editName} onChange={e => setEditName(e.target.value)} /></div>
              <div className="form-group"><label>よみがな（任意）</label><input value={editYomi} onChange={e => setEditYomi(e.target.value)} placeholder="ひらがな" /></div>
              <div className="form-group"><label>都道府県</label><input value={editPref} onChange={e => setEditPref(e.target.value)} /></div>
              <div className="form-group"><label>都道府県よみがな（任意）</label><input value={editPrefYomi} onChange={e => setEditPrefYomi(e.target.value)} placeholder="ひらがな" /></div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary btn-sm" onClick={saveEdit}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div><p style={{ fontWeight: 700 }}>{s.name}</p><p className="muted" style={{ fontSize: '0.85rem' }}>{s.prefecture}</p></div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => { setEditingId(s.id); setEditName(s.name); setEditYomi(s.yomi || ''); setEditPref(s.prefecture); setEditPrefYomi(s.prefecture_yomi || '') }}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(s.id, s.name)}>削除</button>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── コース管理 ──
function CoursesTab() {
  const [schools, setSchools]   = useState([])
  const [schoolId, setSchoolId] = useState(null)
  const [courses, setCourses]   = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editName, setEditName]   = useState('')
  const [editDev, setEditDev]     = useState('')
  const [name, setName]         = useState('')
  const [dev, setDev]           = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  useEffect(() => {
    api.getSchools({ limit: 1000, sort_by: 'name', order: 'asc' }).then(d => setSchools(d.items))
  }, [])

  function loadCourses() {
    if (!schoolId) { setCourses(null); return }
    api.getCourses({ school_id: schoolId, limit: 50, sort_by: 'deviation', order: 'desc' }).then(setCourses)
  }
  useEffect(loadCourses, [schoolId])

  async function handleCreate() {
    if (!schoolId)   { setError('大学を選択してください'); return }
    if (!name.trim()) { setError('コース名を入力してください'); return }
    if (!dev || isNaN(Number(dev))) { setError('偏差値を数値で入力してください'); return }
    setLoading(true); setError('')
    try { await api.createCourse({ school_id: Number(schoolId), name: name.trim(), deviation: Number(dev) }); setName(''); setDev(''); loadCourses() }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function saveEdit(id) {
    await api.updateCourse(id, { school_id: Number(schoolId), name: editName, deviation: Number(editDev) })
    setEditingId(null); loadCourses()
  }

  async function handleDelete(id, n) {
    if (!confirm(`「${n}」を削除しますか？`)) return
    await api.deleteCourse(id); loadCourses()
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: '1rem', overflow: 'visible' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>大学を選択</h3>
        <SchoolAutocomplete schools={schools} schoolId={schoolId} onSelect={setSchoolId} placeholder="大学名を入力して選択..." />
      </div>
      {schoolId && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>コースを追加</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 2, marginBottom: 0 }}><label>コース名</label><input value={name} onChange={e => setName(e.target.value)} placeholder="普通科" /></div>
            <div className="form-group" style={{ flex: 1, marginBottom: 0, minWidth: 90 }}><label>偏差値</label><input type="number" step="0.5" value={dev} onChange={e => setDev(e.target.value)} placeholder="55" /></div>
            <button className="btn btn-primary" onClick={handleCreate} disabled={loading} style={{ flexShrink: 0 }}>{loading ? '追加中...' : '追加'}</button>
          </div>
          {error && <p className="error" style={{ marginTop: '0.5rem' }}>{error}</p>}
        </div>
      )}
      {courses?.items.map(c => (
        <div key={c.id} className="card">
          {editingId === c.id ? (
            <div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <div className="form-group" style={{ flex: 2, marginBottom: 0 }}><label>コース名</label><input value={editName} onChange={e => setEditName(e.target.value)} /></div>
                <div className="form-group" style={{ flex: 1, marginBottom: 0, minWidth: 90 }}><label>偏差値</label><input type="number" step="0.5" value={editDev} onChange={e => setEditDev(e.target.value)} /></div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => saveEdit(c.id)}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
              <div><p style={{ fontWeight: 700 }}>{c.name}</p><p className="muted" style={{ fontSize: '0.85rem' }}>偏差値 {c.deviation}</p></div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => { setEditingId(c.id); setEditName(c.name); setEditDev(String(c.deviation)) }}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(c.id, c.name)}>削除</button>
              </div>
            </div>
          )}
        </div>
      ))}
      {courses?.items.length === 0 && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>コースがありません</p>}
    </div>
  )
}

// ── 事件管理 ──
function IncidentsTab() {
  const [data, setData]       = useState(null)
  const [q, setQ]             = useState('')
  const [sort, setSort]       = useState('created_at-desc')
  const [editingId, setEditingId]       = useState(null)
  const [editTitle, setEditTitle]       = useState('')
  const [editDesc, setEditDesc]         = useState('')
  const [editCourse, setEditCourse]     = useState('')
  const [editOccurredY, setEditOccurredY] = useState('')
  const [editOccurredM, setEditOccurredM] = useState('')
  const [editOccurredD, setEditOccurredD] = useState('')
  const [editSchoolId, setEditSchoolId] = useState(null)

  function load() {
    const [sort_by, order] = sort.split('-')
    api.getIncidents({ q: q || undefined, limit: 50, sort_by, order }).then(setData)
  }
  useEffect(() => { load() }, [q, sort])

  async function saveEdit(id) {
    await api.updateIncident(id, {
      title: editTitle, description: editDesc || null,
      school_id: Number(editSchoolId || 1), course_name: editCourse || null,
      occurred_year: editOccurredY ? Number(editOccurredY) : null,
      occurred_month: editOccurredM ? Number(editOccurredM) : null,
      occurred_day: editOccurredD ? Number(editOccurredD) : null,
    })
    setEditingId(null); load()
  }

  function startEdit(inc) {
    setEditingId(inc.id)
    setEditTitle(inc.title)
    setEditDesc(inc.description || '')
    setEditCourse(inc.course_name || '')
    setEditOccurredY(inc.occurred_year != null ? String(inc.occurred_year) : '')
    setEditOccurredM(inc.occurred_month != null ? String(inc.occurred_month) : '')
    setEditOccurredD(inc.occurred_day != null ? String(inc.occurred_day) : '')
    setEditSchoolId(inc.school_id)
  }

  async function handleDelete(id, t) {
    if (!confirm(`「${t}」を削除しますか？`)) return
    await api.deleteIncident(id); load()
  }

  return (
    <div>
      <p className="muted" style={{ marginBottom: '1rem', fontSize: '0.875rem' }}>
        事件の投稿はユーザー自身が行います。管理者はここから削除のみ行えます。
      </p>
      <div className="search-bar">
        <input placeholder="タイトルで検索..." value={q} onChange={e => setQ(e.target.value)} />
        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="created_at-desc">投稿日（新しい順）</option>
          <option value="created_at-asc">投稿日（古い順）</option>
          <option value="occurred_date-desc">発生日（新しい順）</option>
          <option value="title-asc">タイトル（昇順）</option>
        </select>
      </div>
      {data?.items.map(inc => (
        <div key={inc.id} className="card">
          {editingId === inc.id ? (
            <div>
              <div className="form-group"><label>タイトル</label><input value={editTitle} onChange={e => setEditTitle(e.target.value)} /></div>
              <CourseSelect schoolId={editSchoolId} value={editCourse} onChange={setEditCourse} />
              <div className="form-group"><label>内容</label><textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} /></div>
              <div className="form-group">
                <label>発生日（わからない部分は空欄）</label>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <input type="number" placeholder="年" value={editOccurredY} onChange={e => setEditOccurredY(e.target.value)} style={{ width: 80 }} />
                  <input type="number" placeholder="月" min="1" max="12" value={editOccurredM} onChange={e => setEditOccurredM(e.target.value)} style={{ width: 60 }} />
                  <input type="number" placeholder="日" min="1" max="31" value={editOccurredD} onChange={e => setEditOccurredD(e.target.value)} style={{ width: 60 }} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => saveEdit(inc.id)}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <p style={{ fontWeight: 700 }}>{inc.title}</p>
                {inc.school_name && <p style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>🏫 {inc.school_name}</p>}
                {inc.course_name && <p style={{ fontSize: '0.8rem', color: 'var(--primary)' }}>📚 {inc.course_name}</p>}
                {(inc.occurred_year != null || inc.occurred_month != null || inc.occurred_day != null) && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                    📅 {[
                      inc.occurred_year != null ? `${inc.occurred_year}年` : '不明年',
                      inc.occurred_month != null ? `${inc.occurred_month}月` : '不明月',
                      inc.occurred_day != null ? `${inc.occurred_day}日` : '不明日',
                    ].join('')}
                  </p>
                )}
                {inc.description && <p className="muted" style={{ fontSize: '0.85rem' }}>{inc.description}</p>}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => startEdit(inc)}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(inc.id, inc.title)}>削除</button>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── 評価管理 ──
function ReviewsTab() {
  const [data, setData]       = useState(null)
  const [schoolName, setSchoolName] = useState('')
  const [skip, setSkip]       = useState(0)
  const LIMIT = 30

  function load() {
    api.getAllReviews({ school_name: schoolName || undefined, skip, limit: LIMIT }).then(setData)
  }
  useEffect(() => { load() }, [schoolName, skip])

  async function handleDelete(id) {
    if (!confirm('この評価を削除しますか？')) return
    await api.deleteReview(id); load()
  }

  function Stars({ n }) {
    return <span style={{ color: '#fbbf24' }}>{'★'.repeat(n)}{'☆'.repeat(5 - n)}</span>
  }

  return (
    <div>
      <div className="search-bar">
        <input
          placeholder="大学名で検索..."
          value={schoolName}
          onChange={e => { setSchoolName(e.target.value); setSkip(0) }}
        />
      </div>
      {data?.items.map(rv => (
        <div key={rv.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.25rem' }}>
              <Stars n={rv.rating} />
              {rv.school_name && (
                <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 600 }}>🏫 {rv.school_name}</span>
              )}
              {rv.course_name && (
                <span style={{ fontSize: '0.8rem', color: 'var(--primary)' }}>📚 {rv.course_name}</span>
              )}
            </div>
            <p className="muted" style={{ fontSize: '0.82rem', marginBottom: rv.comment ? '0.25rem' : 0 }}>
              👤 {rv.user_name ?? `#${rv.user_id}`} ・ {new Date(rv.created_at).toLocaleDateString('ja-JP')}
            </p>
            {rv.comment && <p style={{ fontSize: '0.875rem' }}>{rv.comment}</p>}
          </div>
          <button
            className="btn btn-secondary btn-sm"
            style={{ color: 'var(--danger)', flexShrink: 0 }}
            onClick={() => handleDelete(rv.id)}
          >
            削除
          </button>
        </div>
      ))}
      {data?.total === 0 && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>評価がありません</p>}
      {data && data.total > LIMIT && (
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
          {skip > 0 && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => Math.max(0, s - LIMIT))}>← 前</button>}
          {skip + LIMIT < data.total && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => s + LIMIT)}>次 →</button>}
        </div>
      )}
    </div>
  )
}

// ── ポスト管理 ──
function PostsTab() {
  const [data, setData]   = useState(null)
  const [q, setQ]         = useState('')
  const [order, setOrder] = useState('desc')

  function load() { api.getPosts({ q: q || undefined, sort_by: 'created_at', order, limit: 50 }).then(setData) }
  useEffect(load, [q, order])

  async function handleDelete(id) {
    if (!confirm('この投稿を削除しますか？')) return
    await api.deletePost(id); load()
  }

  return (
    <div>
      <div className="search-bar">
        <input placeholder="内容で検索..." value={q} onChange={e => setQ(e.target.value)} />
        <select value={order} onChange={e => setOrder(e.target.value)}>
          <option value="desc">新しい順</option>
          <option value="asc">古い順</option>
        </select>
      </div>
      {data?.items.map(post => (
        <div key={post.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ flex: 1 }}>
            {post.school_name && <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.1rem' }}>🏫 {post.school_name}</p>}
            {post.course_name && <p style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.2rem' }}>📚 {post.course_name}</p>}
            <p style={{ fontSize: '0.9rem' }}>{post.content}</p>
            <p className="muted" style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>
              {post.user_name ?? `#${post.user_id}`} ・ 👍{post.like_count} 👎{post.dislike_count}
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)', flexShrink: 0 }} onClick={() => handleDelete(post.id)}>削除</button>
        </div>
      ))}
      {!data?.items.length && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>投稿がありません</p>}
    </div>
  )
}

// ── リポスト管理 ──
function RepostsAdminTab() {
  const [data, setData]   = useState(null)
  const [q, setQ]         = useState('')
  const [order, setOrder] = useState('desc')
  const [skip, setSkip]   = useState(0)
  const LIMIT = 30

  function load() {
    api.getAllReposts({ sort_by: 'created_at', order, skip, limit: LIMIT }).then(setData)
  }
  useEffect(() => { load() }, [order, skip])

  async function handleDelete(id) {
    if (!confirm('このリポストを削除しますか？')) return
    await api.deleteRepost(id); load()
  }

  const items = (data?.items ?? [])
    .filter(rp => rp.comment)
    .filter(rp => !q.trim() || (
      rp.user_name?.includes(q) ||
      rp.comment?.includes(q) ||
      rp.original_post?.content?.includes(q)
    ))

  return (
    <div>
      <div className="search-bar">
        <input
          placeholder="ユーザー名・コメントで検索..."
          value={q}
          onChange={e => setQ(e.target.value)}
        />
        <select value={order} onChange={e => { setOrder(e.target.value); setSkip(0) }}>
          <option value="desc">新しい順</option>
          <option value="asc">古い順</option>
        </select>
      </div>
      {items.length === 0 && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>引用リポストがありません</p>}
      {items.map(rp => (
        <div key={rp.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
              <span className="badge">引用リポスト</span>
              <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{rp.user_name ?? `#${rp.user_id}`}</span>
              <span className="muted" style={{ fontSize: '0.78rem', marginLeft: 'auto' }}>{new Date(rp.created_at).toLocaleDateString('ja-JP')}</span>
            </div>
            {rp.comment && (
              <p style={{ fontSize: '0.88rem', marginBottom: '0.25rem' }}>{rp.comment}</p>
            )}
            {rp.original_post && (
              <p className="muted" style={{ fontSize: '0.8rem', borderLeft: '2px solid var(--border)', paddingLeft: '0.5rem' }}>
                {rp.original_post.content?.slice(0, 80)}{(rp.original_post.content?.length ?? 0) > 80 ? '…' : ''}
              </p>
            )}
            <p className="muted" style={{ fontSize: '0.78rem', marginTop: '0.25rem' }}>
              👍{rp.like_count} 👎{rp.dislike_count}
            </p>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            style={{ color: 'var(--danger)', flexShrink: 0 }}
            onClick={() => handleDelete(rp.id)}
          >削除</button>
        </div>
      ))}
      {data && data.total > LIMIT && !q && (
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
          {skip > 0 && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => Math.max(0, s - LIMIT))}>← 前</button>}
          {skip + LIMIT < data.total && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => s + LIMIT)}>次 →</button>}
        </div>
      )}
    </div>
  )
}

// ── 通報管理 ──
function ReportsTab() {
  const [data, setData]   = useState(null)
  const [filter, setFilter] = useState('')
  const LIMIT = 30
  const [skip, setSkip]   = useState(0)

  function load() {
    api.getReports({ target_type: filter || undefined, skip, limit: LIMIT }).then(setData)
  }
  useEffect(() => { load() }, [filter, skip])

  async function handleDeleteReport(id) {
    if (!confirm('この通報を削除しますか？')) return
    await api.deleteReport(id); load()
  }

  async function handleDeleteContent(type, id) {
    if (!confirm(`この${type === 'post' ? 'ポスト' : type === 'repost' ? 'リポスト' : type === 'incident' ? '事件' : '評価'}を削除しますか？\n関連する通報もすべて削除されます。`)) return
    await api.deleteReportedContent(type, id); load()
  }

  async function handleDeleteReporter(reporterId, reporterName) {
    if (!confirm(`通報者「${reporterName ?? `#${reporterId}`}」のアカウントを削除しますか？`)) return
    try {
      await api.deleteUser(reporterId)
      load()
    } catch (e) { alert(e.message) }
  }

  const typeLabel = { post: 'ポスト', repost: 'リポスト', incident: '事件', review: '評価' }

  return (
    <div>
      <div className="search-bar">
        <select value={filter} onChange={e => { setFilter(e.target.value); setSkip(0) }}>
          <option value="">すべて</option>
          <option value="post">ポスト</option>
          <option value="repost">リポスト</option>
          <option value="incident">事件</option>
          <option value="review">評価</option>
        </select>
      </div>
      {data?.total === 0 && <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>通報はありません</p>}
      {data?.items.map(r => (
        <div key={r.id} className="card" style={{ marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                <span className="badge">{typeLabel[r.target_type] ?? r.target_type}</span>
                <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>ID: {r.target_id}</span>
                <span className="muted" style={{ fontSize: '0.78rem' }}>通報者: {r.reporter_name ?? `#${r.reporter_id}`}</span>
                <span className="muted" style={{ fontSize: '0.78rem', marginLeft: 'auto' }}>{new Date(r.created_at).toLocaleDateString('ja-JP')}</span>
              </div>
              {r.reason && <p style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>理由: {r.reason}</p>}
            </div>
            <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0, flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{ color: 'var(--danger)' }}
                onClick={() => handleDeleteContent(r.target_type, r.target_id)}
              >
                コンテンツ削除
              </button>
              <button
                className="btn btn-secondary btn-sm"
                style={{ color: 'var(--danger)' }}
                onClick={() => handleDeleteReporter(r.reporter_id, r.reporter_name)}
              >
                ユーザー削除
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleDeleteReport(r.id)}
              >
                通報を却下
              </button>
            </div>
          </div>
        </div>
      ))}
      {data && data.total > LIMIT && (
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
          {skip > 0 && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => Math.max(0, s - LIMIT))}>← 前</button>}
          {skip + LIMIT < data.total && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => s + LIMIT)}>次 →</button>}
        </div>
      )}
    </div>
  )
}

// ── ブロックリストタブ ──
function BlockedEmailsTab() {
  const [data, setData] = useState(null)
  const [skip, setSkip] = useState(0)
  const LIMIT = 50

  function load() {
    api.getBlockedEmails({ skip, limit: LIMIT }).then(setData)
  }
  useEffect(() => { load() }, [skip])

  async function handleUnblock(id, email) {
    if (!confirm(`「${email}」のブロックを解除しますか？\nこのメールアドレスで再登録できるようになります。`)) return
    try { await api.unblockEmail(id); load() }
    catch (e) { alert(e.message) }
  }

  return (
    <div>
      <p className="muted" style={{ marginBottom: '1rem', fontSize: '0.875rem' }}>
        アカウント削除時にブロックされたメールアドレスの一覧です。解除すると再登録が可能になります。
      </p>
      {data?.total === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>ブロックされたメールアドレスはありません</p>
      )}
      {data?.items.map(entry => (
        <div key={entry.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>{entry.email}</p>
            <p className="muted" style={{ fontSize: '0.78rem' }}>
              ブロック日時: {new Date(entry.blocked_at).toLocaleString('ja-JP')}
            </p>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleUnblock(entry.id, entry.email)}
          >
            ブロック解除
          </button>
        </div>
      ))}
      {data && data.total > LIMIT && (
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
          {skip > 0 && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => Math.max(0, s - LIMIT))}>← 前</button>}
          {skip + LIMIT < data.total && <button className="btn btn-secondary btn-sm" onClick={() => setSkip(s => s + LIMIT)}>次 →</button>}
        </div>
      )}
      {data && <p className="muted" style={{ textAlign: 'center', fontSize: '0.8rem', marginTop: '0.75rem' }}>合計 {data.total} 件</p>}
    </div>
  )
}

// ── サイト設定タブ ──
function SiteContentEditor({ contentKey, label, placeholder, multiline = true }) {
  const [value, setValue]   = useState('')
  const [original, setOriginal] = useState('')
  const [msg, setMsg]       = useState('')
  const [err, setErr]       = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.getSiteContent(contentKey).then(d => { setValue(d.value || ''); setOriginal(d.value || '') })
  }, [contentKey])

  async function handleSave() {
    setMsg(''); setErr(''); setLoading(true)
    try {
      await api.updateSiteContent(contentKey, value)
      setOriginal(value); setMsg('保存しました')
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>{label}</h3>
      <div className="form-group">
        {multiline ? (
          <textarea
            rows={8}
            value={value}
            onChange={e => setValue(e.target.value)}
            placeholder={placeholder}
            style={{ fontFamily: 'inherit', fontSize: '0.9rem' }}
          />
        ) : (
          <input value={value} onChange={e => setValue(e.target.value)} placeholder={placeholder} />
        )}
      </div>
      {err && <p className="error">{err}</p>}
      {msg && <p className="success-msg">{msg}</p>}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={loading || value === original}>
          {loading ? '保存中...' : '保存する'}
        </button>
        {value !== original && (
          <button className="btn btn-secondary btn-sm" onClick={() => { setValue(original); setMsg('') }}>リセット</button>
        )}
      </div>
    </div>
  )
}

function SiteSettingsTab() {
  return (
    <div>
      <SiteContentEditor
        contentKey="site_name"
        label="サイト名（ブラウザタブに表示）"
        placeholder="ExaMininfo"
        multiline={false}
      />
      <SiteContentEditor
        contentKey="hero_title"
        label="ヒーローセクションのタイトル"
        placeholder="大学について、もっと知ろう。"
        multiline={false}
      />
      <SiteContentEditor
        contentKey="home_description"
        label="ホーム画面の説明文"
        placeholder="トップページに表示される説明文を入力..."
      />
      <SiteContentEditor
        contentKey="about"
        label="このサイトについて（/about ページ）"
        placeholder="サイトの詳細説明を入力..."
      />
      <SiteContentEditor
        contentKey="legal"
        label="法的情報（/legal ページ）— # 見出し、## 小見出し が使えます"
        placeholder="## 利用規約&#10;&#10;ここに利用規約を記載...&#10;&#10;## プライバシーポリシー&#10;&#10;ここにプライバシーポリシーを記載..."
      />
    </div>
  )
}

// ── メイン ──
export default function AdminPage() {
  const { user } = useAuth()
  const [tab, setTab] = useState('users')

  if (!user || user.role !== 'admin') return <Navigate to="/" replace />

  const TABS = [
    { key: 'users',    label: 'ユーザー' },
    { key: 'schools',  label: '大学' },
    { key: 'courses',  label: 'コース' },
    { key: 'incidents',label: '事件' },
    { key: 'reviews',  label: '評価' },
    { key: 'posts',    label: 'ポスト' },
    { key: 'reposts',  label: '引用リポスト' },
    { key: 'reports',  label: '通報' },
    { key: 'blocked',  label: 'ブロックリスト' },
    { key: 'site',     label: 'サイト設定' },
  ]

  return (
    <div className="container">
      <h1 className="page-title">管理画面</h1>
      <div className="tabs">
        {TABS.map(t => (
          <div key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</div>
        ))}
      </div>
      {tab === 'users'     && <UsersTab />}
      {tab === 'schools'   && <SchoolsTab />}
      {tab === 'courses'   && <CoursesTab />}
      {tab === 'incidents' && <IncidentsTab />}
      {tab === 'reviews'   && <ReviewsTab />}
      {tab === 'posts'     && <PostsTab />}
      {tab === 'reposts'   && <RepostsAdminTab />}
      {tab === 'reports'   && <ReportsTab />}
      {tab === 'blocked'   && <BlockedEmailsTab />}
      {tab === 'site'      && <SiteSettingsTab />}
    </div>
  )
}
