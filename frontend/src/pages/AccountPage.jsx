import { useState, useEffect, useCallback, useRef } from 'react'
import { Navigate, Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'
import CourseSelect from '../components/CourseSelect'
import Pagination from '../components/Pagination'

function avatarColor(name) {
  const colors = [
    ['#29B6F6','#0288D1'],['#66BB6A','#2E7D32'],['#AB47BC','#6A1B9A'],
    ['#FF7043','#BF360C'],['#26C6DA','#00838F'],['#EC407A','#880E4F'],
  ]
  const i = (name?.charCodeAt(0) ?? 0) % colors.length
  return colors[i]
}

function Avatar({ name, avatarUrl, positionX = 50, positionY = 50, size = 40 }) {
  const [bg, fg] = avatarColor(name)
  const [imgError, setImgError] = useState(false)
  if (avatarUrl && !imgError) {
    return (
      <img src={avatarUrl} alt={name} onError={() => setImgError(true)} style={{
        width: size, height: size, borderRadius: '50%', objectFit: 'cover',
        objectPosition: `${positionX}% ${positionY}%`,
        border: '2px solid var(--border)', flexShrink: 0,
      }} />
    )
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: `linear-gradient(135deg, ${bg}, ${fg})`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 700, fontSize: size * 0.4, color: '#fff', flexShrink: 0,
    }}>
      {name?.charAt(0).toUpperCase()}
    </div>
  )
}

const LIMIT = 10

// ── X風アバタークロップエディタ ──
function AvatarCropEditor({ avatarUrl, posX, posY, onChange, onSave }) {
  const SIZE = 128
  const dragRef = useRef(null)

  function startDrag(clientX, clientY) {
    dragRef.current = { startX: clientX, startY: clientY, posX, posY }
  }

  function moveDrag(clientX, clientY) {
    if (!dragRef.current) return
    const { startX, startY, posX: ox, posY: oy } = dragRef.current
    const dx = clientX - startX
    const dy = clientY - startY
    const SENS = SIZE * 1.5
    const nx = Math.max(0, Math.min(100, ox + (dx / SENS) * 100))
    const ny = Math.max(0, Math.min(100, oy + (dy / SENS) * 100))
    onChange(Math.round(nx), Math.round(ny))
  }

  function endDrag() { dragRef.current = null }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.6rem', marginTop: '0.5rem' }}>
      <div
        style={{
          width: SIZE, height: SIZE, borderRadius: '50%', overflow: 'hidden',
          cursor: 'grab', border: '2px solid var(--border)',
          userSelect: 'none', flexShrink: 0,
          boxShadow: '0 0 0 4px var(--bg)',
        }}
        onMouseDown={e => { e.preventDefault(); startDrag(e.clientX, e.clientY) }}
        onMouseMove={e => { if (e.buttons === 1) moveDrag(e.clientX, e.clientY) }}
        onMouseUp={endDrag}
        onMouseLeave={endDrag}
        onTouchStart={e => { const t = e.touches[0]; startDrag(t.clientX, t.clientY) }}
        onTouchMove={e => { e.preventDefault(); const t = e.touches[0]; moveDrag(t.clientX, t.clientY) }}
        onTouchEnd={endDrag}
      >
        <img
          src={avatarUrl}
          alt="avatar crop"
          draggable={false}
          style={{
            width: '100%', height: '100%', objectFit: 'cover',
            objectPosition: `${posX}% ${posY}%`,
            pointerEvents: 'none',
          }}
        />
      </div>
      <p style={{ fontSize: '0.76rem', color: 'var(--muted)', margin: 0 }}>ドラッグして表示位置を調整</p>
      <button className="btn btn-secondary btn-sm" onClick={onSave}>この位置で保存</button>
    </div>
  )
}

function fmt(d) { return new Date(d).toLocaleDateString('ja-JP') }

// ── プロフィールタブ ──
function ProfileTab({ user }) {
  const navigate = useNavigate()
  const [name, setName]   = useState('')
  const [email, setEmail] = useState('')
  const [bio, setBio]     = useState(user.bio ?? '')
  const [msg, setMsg]     = useState('')
  const [err, setErr]     = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setMsg(''); setErr('')
    const updates = {}
    if (name.trim()  && name.trim()  !== user.name)  updates.name  = name.trim()
    if (email.trim() && email.trim() !== user.email) updates.email = email.trim()
    if (bio !== (user.bio ?? '')) updates.bio = bio
    if (!Object.keys(updates).length) { setErr('変更がありません'); return }
    setLoading(true)
    try {
      await api.updateProfile(updates)
      setMsg('更新しました'); setName(''); setEmail('')
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="card">
      {/* アバター */}
      <div style={{ marginBottom: '1.25rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{ position: 'relative', cursor: 'pointer', flexShrink: 0 }}
            onClick={() => navigate('/account/avatar')}
            title="アイコンを変更"
          >
            {user.avatar_url ? (
              <img src={user.avatar_url} alt="avatar" style={{
                width: 64, height: 64, borderRadius: '50%', objectFit: 'cover',
                objectPosition: `${user.avatar_position_x ?? 50}% ${user.avatar_position_y ?? 50}%`,
                border: '2px solid var(--border)',
              }} />
            ) : (
              <Avatar name={user.name} size={64} />
            )}
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              opacity: 0, transition: 'opacity 0.15s',
              fontSize: '0.7rem', color: '#fff', fontWeight: 600,
            }}
              onMouseEnter={e => e.currentTarget.style.opacity = 1}
              onMouseLeave={e => e.currentTarget.style.opacity = 0}
            >
              📷
            </div>
          </div>
          <div>
            <p style={{ fontWeight: 700, fontSize: '1.05rem' }}>{user.name}</p>
            <p className="muted" style={{ fontSize: '0.875rem' }}>{user.email}</p>
            <span className="badge" style={{ marginTop: '0.25rem', background: user.role === 'admin' ? 'rgba(255,102,0,0.25)' : undefined }}>
              {user.role}
            </span>
            <button
              className="btn btn-ghost btn-sm"
              style={{ marginTop: '0.4rem', fontSize: '0.8rem' }}
              onClick={() => navigate('/account/avatar')}
            >
              アイコンを変更 →
            </button>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>名前</label>
          <input value={name} onChange={e => setName(e.target.value)} placeholder={user.name} />
        </div>
        <div className="form-group">
          <label>メールアドレス</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={user.email} />
        </div>
        <div className="form-group">
          <label>自己紹介文（任意）</label>
          <textarea
            rows={3}
            value={bio}
            onChange={e => setBio(e.target.value)}
            placeholder={user.bio || '自己紹介を入力...'}
          />
        </div>
        {err && <p className="error">{err}</p>}
        {msg && <p className="success-msg">{msg}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? '更新中...' : '更新する'}
        </button>
      </form>
    </div>
  )
}

// ── パスワードタブ ──
function PasswordTab() {
  const [oldPw, setOldPw]   = useState('')
  const [newPw, setNewPw]   = useState('')
  const [newPw2, setNewPw2] = useState('')
  const [msg, setMsg]       = useState('')
  const [err, setErr]       = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setMsg(''); setErr('')
    if (!oldPw || !newPw) { setErr('すべて入力してください'); return }
    if (newPw !== newPw2)  { setErr('新しいパスワードが一致しません'); return }
    if (newPw.length < 6)  { setErr('6文字以上にしてください'); return }
    setLoading(true)
    try {
      await api.changePassword({ old_password: oldPw, new_password: newPw })
      setMsg('パスワードを変更しました')
      setOldPw(''); setNewPw(''); setNewPw2('')
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="card">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>現在のパスワード</label>
          <input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)} />
        </div>
        <div className="form-group">
          <label>新しいパスワード</label>
          <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} />
        </div>
        <div className="form-group">
          <label>新しいパスワード（確認）</label>
          <input type="password" value={newPw2} onChange={e => setNewPw2(e.target.value)} />
        </div>
        {err && <p className="error">{err}</p>}
        {msg && <p className="success-msg">{msg}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? '変更中...' : '変更する'}
        </button>
      </form>
    </div>
  )
}

// ── 自分の事件タブ ──
function MyIncidentsTab({ userId }) {
  const [data, setData] = useState(null)
  const [skip, setSkip] = useState(0)
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc]   = useState('')
  const [editCourse, setEditCourse] = useState('')
  const [editY, setEditY] = useState('')
  const [editM, setEditM] = useState('')
  const [editD, setEditD] = useState('')

  const load = useCallback(() => {
    api.getIncidents({ user_id: userId, sort_by: 'created_at', order: 'desc', skip, limit: LIMIT }).then(setData)
  }, [userId, skip])
  useEffect(load, [load])

  function startEdit(inc) {
    setEditingId(inc.id)
    setEditTitle(inc.title)
    setEditDesc(inc.description || '')
    setEditCourse(inc.course_name || '')
    setEditY(inc.occurred_year  != null ? String(inc.occurred_year)  : '')
    setEditM(inc.occurred_month != null ? String(inc.occurred_month) : '')
    setEditD(inc.occurred_day   != null ? String(inc.occurred_day)   : '')
  }

  async function saveEdit(inc) {
    await api.updateIncident(inc.id, {
      title: editTitle, description: editDesc || null,
      school_id: inc.school_id, course_name: editCourse || null,
      occurred_year: editY ? Number(editY) : null,
      occurred_month: editM ? Number(editM) : null,
      occurred_day: editD ? Number(editD) : null,
    })
    setEditingId(null); load()
  }

  async function handleDelete(id) {
    if (!confirm('この事件を削除しますか？')) return
    await api.deleteIncident(id); load()
  }

  return (
    <div>
      {data?.items.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '3rem' }}>投稿した事件がありません</p>
      )}
      {data?.items.map(inc => (
        <div key={inc.id} className="card">
          {editingId === inc.id ? (
            <div>
              <div className="form-group"><label>タイトル</label><input value={editTitle} onChange={e => setEditTitle(e.target.value)} /></div>
              <div className="form-group"><label>内容（任意）</label><textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} rows={3} /></div>
              <div className="form-group"><label>コース名（任意）</label><input value={editCourse} onChange={e => setEditCourse(e.target.value)} /></div>
              <div className="form-group">
                <label>発生日（わからない部分は空欄）</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input type="number" placeholder="年"  value={editY} onChange={e => setEditY(e.target.value)} style={{ flex: 2 }} />
                  <input type="number" placeholder="月" min="1" max="12" value={editM} onChange={e => setEditM(e.target.value)} style={{ flex: 1 }} />
                  <input type="number" placeholder="日" min="1" max="31" value={editD} onChange={e => setEditD(e.target.value)} style={{ flex: 1 }} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => saveEdit(inc)}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <>
              <p style={{ fontWeight: 700, marginBottom: '0.3rem' }}>{inc.title}</p>
              {inc.school_name && <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.15rem' }}>🏫 {inc.school_name}</p>}
              {inc.course_name && <p style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.2rem' }}>📚 {inc.course_name}</p>}
              {inc.description && <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>{inc.description}</p>}
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="muted" style={{ fontSize: '0.8rem', marginRight: 'auto' }}>{fmt(inc.created_at)}</span>
                <button className="btn btn-secondary btn-sm" onClick={() => startEdit(inc)}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(inc.id)}>削除</button>
              </div>
            </>
          )}
        </div>
      ))}
      {data && <Pagination skip={skip} limit={LIMIT} total={data.total} onChange={setSkip} />}
    </div>
  )
}

// ── 自分の評価タブ ──
function MyReviewsTab({ userId }) {
  const [data, setData] = useState(null)
  const [skip, setSkip] = useState(0)

  const load = useCallback(() => {
    api.getUserReviews(userId, { skip, limit: LIMIT }).then(setData)
  }, [userId, skip])
  useEffect(load, [load])

  async function handleDelete(id) {
    if (!confirm('この評価を削除しますか？')) return
    await api.deleteReview(id); load()
  }

  function Stars({ n }) {
    return <span style={{ color: '#fbbf24' }}>{'★'.repeat(n)}{'☆'.repeat(5 - n)}</span>
  }

  return (
    <div>
      {data?.items.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '3rem' }}>評価がありません</p>
      )}
      {data?.items.map(rv => (
        <div key={rv.id} className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
            <Stars n={rv.rating} />
            {rv.school_name && <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>🏫 {rv.school_name}</span>}
            <span className="muted" style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>{fmt(rv.created_at)}</span>
          </div>
          {rv.course_name && <p style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.2rem' }}>📚 {rv.course_name}</p>}
          {rv.comment && <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{rv.comment}</p>}
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(rv.id)}>削除</button>
          </div>
        </div>
      ))}
      {data && <Pagination skip={skip} limit={LIMIT} total={data.total} onChange={setSkip} />}
    </div>
  )
}

// ── 自分のポストタブ ──
function MyPostsTab({ userId }) {
  const [data, setData]         = useState(null)
  const [skip, setSkip]         = useState(0)
  const [editingId, setEditingId] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [editCourse, setEditCourse]   = useState('')

  const load = useCallback(() => {
    api.getPosts({ user_id: userId, sort_by: 'created_at', order: 'desc', skip, limit: LIMIT }).then(setData)
  }, [userId, skip])
  useEffect(load, [load])

  function startEdit(post) {
    setEditingId(post.id)
    setEditContent(post.content)
    setEditCourse(post.course_name || '')
  }

  async function saveEdit(post) {
    await api.updatePost(post.id, { content: editContent, course_name: editCourse || null })
    setEditingId(null)
    load()
  }

  async function handleDelete(id) {
    if (!confirm('この投稿を削除しますか？')) return
    await api.deletePost(id); load()
  }

  return (
    <div>
      {data?.items.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '3rem' }}>投稿がありません</p>
      )}
      {data?.items.map(post => (
        <div key={post.id} className="card">
          {editingId === post.id ? (
            <div>
              <div className="form-group">
                <label>内容</label>
                <textarea value={editContent} onChange={e => setEditContent(e.target.value)} rows={3} />
              </div>
              <CourseSelect schoolId={post.school_id} value={editCourse} onChange={setEditCourse} />
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => saveEdit(post)}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <>
              {post.school_name && (
                <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.2rem' }}>🏫 {post.school_name}</p>
              )}
              {post.course_name && (
                <p style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.4rem' }}>📚 {post.course_name}</p>
              )}
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>{post.content}</p>
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="muted" style={{ fontSize: '0.8rem' }}>👍 {post.like_count}　👎 {post.dislike_count}</span>
                <span className="muted" style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>{fmt(post.created_at)}</span>
                <button className="btn btn-secondary btn-sm" onClick={() => startEdit(post)}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(post.id)}>削除</button>
              </div>
            </>
          )}
        </div>
      ))}
      {data && <Pagination skip={skip} limit={LIMIT} total={data.total} onChange={setSkip} />}
    </div>
  )
}

// ── 自分のリポストタブ ──
function MyRepostsTab({ userId }) {
  const [data, setData]   = useState(null)
  const [skip, setSkip]   = useState(0)
  const [editingId, setEditingId]   = useState(null)
  const [editComment, setEditComment] = useState('')

  const load = useCallback(() => {
    api.getAllReposts({ user_id: userId, sort_by: 'created_at', order: 'desc', skip, limit: LIMIT }).then(setData)
  }, [userId, skip])
  useEffect(load, [load])

  async function saveEdit(id) {
    await api.updateRepost(id, { comment: editComment || null })
    setEditingId(null); load()
  }

  async function handleDelete(id) {
    if (!confirm('このリポストを削除しますか？')) return
    await api.deleteRepost(id); load()
  }

  return (
    <div>
      {data?.items.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '3rem' }}>リポストがありません</p>
      )}
      {data?.items.map(rp => (
        <div key={rp.id} className="card">
          {editingId === rp.id ? (
            <div>
              <div className="form-group">
                <label>コメント</label>
                <textarea value={editComment} onChange={e => setEditComment(e.target.value)} rows={2} placeholder="コメント（任意）" />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => saveEdit(rp.id)}>保存</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>キャンセル</button>
              </div>
            </div>
          ) : (
            <>
              {rp.comment ? (
                <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{rp.comment}</p>
              ) : (
                <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>🔁 リポスト（コメントなし）</p>
              )}
              {rp.original_post && (
                <div style={{ borderLeft: '2px solid var(--border)', paddingLeft: '0.6rem', marginBottom: '0.5rem' }}>
                  {rp.original_post.school_name && <p style={{ fontSize: '0.78rem', color: 'var(--muted)', marginBottom: '0.1rem' }}>🏫 {rp.original_post.school_name}</p>}
                  {rp.original_post.course_name && <p style={{ fontSize: '0.78rem', color: 'var(--primary)', marginBottom: '0.1rem' }}>📚 {rp.original_post.course_name}</p>}
                  <p className="muted" style={{ fontSize: '0.8rem' }}>
                    {rp.original_post.content?.slice(0, 80)}{(rp.original_post.content?.length ?? 0) > 80 ? '…' : ''}
                  </p>
                </div>
              )}
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="muted" style={{ fontSize: '0.8rem' }}>👍 {rp.like_count}　👎 {rp.dislike_count}</span>
                <span className="muted" style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>{fmt(rp.created_at)}</span>
                <button className="btn btn-secondary btn-sm" onClick={() => { setEditingId(rp.id); setEditComment(rp.comment || '') }}>編集</button>
                <button className="btn btn-secondary btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(rp.id)}>削除</button>
              </div>
            </>
          )}
        </div>
      ))}
      {data && <Pagination skip={skip} limit={LIMIT} total={data.total} onChange={setSkip} />}
    </div>
  )
}

// ── 公開プロフィールプレビュータブ ──
function PublicPreviewTab({ user }) {
  const [profile, setProfile] = useState(null)
  const [posts, setPosts]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.getUserProfile(user.id),
      api.getPosts({ user_id: user.id, sort_by: 'created_at', order: 'desc', skip: 0, limit: 5 }),
    ]).then(([p, po]) => { setProfile(p); setPosts(po) })
      .finally(() => setLoading(false))
  }, [user.id])

  if (loading) return <div className="loading" style={{ padding: '3rem' }}>読み込み中...</div>

  return (
    <div>
      <p className="muted" style={{ fontSize: '0.8rem', marginBottom: '1rem', textAlign: 'center' }}>
        他のユーザーにはこのように表示されます
      </p>
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
          <Avatar name={user.name} avatarUrl={profile?.avatar_url} positionX={profile?.avatar_position_x} positionY={profile?.avatar_position_y} size={64} />
          <div style={{ flex: 1 }}>
            <p style={{ fontWeight: 700, fontSize: '1.15rem', marginBottom: '0.2rem' }}>{user.name}</p>
            {user.bio ? (
              <p style={{ fontSize: '0.9rem', color: 'var(--text)', marginBottom: '0.6rem', whiteSpace: 'pre-wrap' }}>
                {user.bio}
              </p>
            ) : (
              <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                自己紹介文がまだありません
              </p>
            )}
            <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
              <span><strong style={{ color: 'var(--text)' }}>{profile?.follower_count ?? 0}</strong> フォロワー</span>
              <span><strong style={{ color: 'var(--text)' }}>{profile?.following_count ?? 0}</strong> フォロー中</span>
            </div>
          </div>
        </div>
      </div>

      <p style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.6rem', color: 'var(--muted)' }}>最近の投稿（最大5件）</p>
      {posts?.items.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '1.5rem' }}>投稿がありません</p>
      )}
      {posts?.items.map(post => (
        <div key={post.id} className="card" style={{ marginBottom: '0.6rem' }}>
          <p style={{ fontSize: '0.88rem', marginBottom: '0.4rem' }}>{post.content}</p>
          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'flex', gap: '0.5rem' }}>
            {post.school_name && <span>🏫 {post.school_name}</span>}
            {post.course_name && <span>📚 {post.course_name}</span>}
            <span style={{ marginLeft: 'auto' }}>{fmt(post.created_at)}</span>
          </div>
        </div>
      ))}

      <div style={{ textAlign: 'center', marginTop: '1rem' }}>
        <Link to={`/users/${user.id}`} className="btn btn-secondary btn-sm">
          公開プロフィールページを開く
        </Link>
      </div>
    </div>
  )
}

// ── アカウント削除タブ ──
function DeleteAccountTab({ user }) {
  const [password, setPassword] = useState('')
  const [confirm1, setConfirm1] = useState('')
  const [err, setErr]           = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()
  const { logout } = useAuth()

  async function handleDelete(e) {
    e.preventDefault()
    setErr('')
    if (confirm1 !== 'DELETE') { setErr('確認テキストが正しくありません'); return }
    if (!password) { setErr('パスワードを入力してください'); return }
    if (!confirm(`「${user.name}」のアカウントを完全に削除しますか？\nこの操作は取り消せません。`)) return
    setLoading(true)
    try {
      await api.deleteMyAccount({ password })
      logout()
      navigate('/')
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="card" style={{ borderColor: 'var(--danger)', borderWidth: 1, borderStyle: 'solid' }}>
      <h3 style={{ color: 'var(--danger)', fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>アカウントを削除</h3>
      <p className="muted" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
        アカウントを削除すると、投稿・リポスト・評価・フォロー情報など、すべてのデータが完全に削除されます。この操作は取り消せません。
      </p>
      <form onSubmit={handleDelete}>
        <div className="form-group">
          <label>パスワード</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="現在のパスワード" />
        </div>
        <div className="form-group">
          <label>確認のため「DELETE」と入力</label>
          <input value={confirm1} onChange={e => setConfirm1(e.target.value)} placeholder="DELETE" />
        </div>
        {err && <p className="error">{err}</p>}
        <button
          className="btn btn-primary"
          type="submit"
          disabled={loading || confirm1 !== 'DELETE' || !password}
          style={{ background: 'var(--danger)', borderColor: 'var(--danger)' }}
        >
          {loading ? '削除中...' : 'アカウントを完全に削除'}
        </button>
      </form>
    </div>
  )
}

// ── メイン ──
export default function AccountPage() {
  const { user, refreshUser, logout } = useAuth()
  const [tab, setTab] = useState('profile')

  if (!user) return <Navigate to="/login" replace />

  const TABS = [
    { key: 'profile',   label: 'プロフィール' },
    { key: 'preview',   label: '公開プレビュー' },
    { key: 'password',  label: 'パスワード' },
    { key: 'posts',     label: 'ポスト' },
    { key: 'reposts',   label: 'リポスト' },
    { key: 'incidents', label: '事件' },
    { key: 'reviews',   label: '評価' },
    { key: 'delete',    label: 'アカウント削除' },
  ]

  return (
    <div className="container" style={{ maxWidth: 640 }}>
      <h1 className="page-title">アカウント</h1>
      <div className="tabs">
        {TABS.map(t => (
          <div key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </div>
        ))}
      </div>
      {tab === 'profile'   && <ProfileTab      user={user} />}
      {tab === 'preview'   && <PublicPreviewTab user={user} />}
      {tab === 'password'  && <PasswordTab />}
      {tab === 'posts'     && <MyPostsTab      userId={user.id} />}
      {tab === 'reposts'   && <MyRepostsTab    userId={user.id} />}
      {tab === 'incidents' && <MyIncidentsTab  userId={user.id} />}
      {tab === 'reviews'   && <MyReviewsTab    userId={user.id} />}
      {tab === 'delete'    && <DeleteAccountTab    user={user} />}
    </div>
  )
}
