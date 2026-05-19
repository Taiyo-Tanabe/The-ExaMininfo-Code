import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'
import Pagination from '../components/Pagination'
import PostCard, { Avatar, MentionTextarea, ComposeArea } from '../components/PostCard'

const INC_LIMIT      = 10
const REVIEW_LIMIT   = 20
const TIMELINE_LIMIT = 20

const INC_SORT_OPTIONS = [
  { value: 'created_at-desc',    label: '投稿日（新しい順）',  sort_by: 'created_at',    order: 'desc' },
  { value: 'created_at-asc',     label: '投稿日（古い順）',    sort_by: 'created_at',    order: 'asc'  },
  { value: 'occurred_date-desc', label: '発生日（新しい順）',  sort_by: 'occurred_date', order: 'desc' },
  { value: 'occurred_date-asc',  label: '発生日（古い順）',    sort_by: 'occurred_date', order: 'asc'  },
  { value: 'title-asc',          label: 'タイトル（昇順）',    sort_by: 'title',         order: 'asc'  },
]

function fmt(dateStr) {
  return new Date(dateStr).toLocaleDateString('ja-JP')
}

function fmtPartialDate(inc) {
  const y = inc.occurred_year, m = inc.occurred_month, d = inc.occurred_day
  if (y == null && m == null && d == null) return null
  const yStr = y != null ? `${y}年` : '不明年'
  const mStr = m != null ? `${m}月` : '不明月'
  const dStr = d != null ? `${d}日` : '不明日'
  return yStr + mStr + dStr
}

function StarRating({ value, onChange, readOnly = false }) {
  const [hover, setHover] = useState(0)
  return (
    <div style={{ display: 'flex', gap: '0.1rem' }}>
      {[1, 2, 3, 4, 5].map(n => (
        <span
          key={n}
          style={{
            fontSize: '1.4rem',
            cursor: readOnly ? 'default' : 'pointer',
            color: n <= (hover || value) ? '#fbbf24' : 'var(--border)',
            transition: 'color 0.1s',
            userSelect: 'none',
          }}
          onClick={() => !readOnly && onChange?.(n)}
          onMouseEnter={() => !readOnly && setHover(n)}
          onMouseLeave={() => !readOnly && setHover(0)}
        >
          ★
        </span>
      ))}
    </div>
  )
}

// 評価・事件両方に使える汎用コメントセクション
function CommentSection({ parentType, parentId, schoolId, user }) {
  const [posts, setPosts]           = useState(null)
  const [content, setContent]       = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]           = useState('')

  const filterKey = parentType === 'review' ? 'review_id' : 'incident_id'

  const loadPosts = useCallback(() => {
    api.getPosts({ [filterKey]: parentId, top_level_only: true, sort_by: 'created_at', order: 'asc', limit: 30 })
      .then(d => setPosts(d.items))
  }, [parentId, filterKey])

  useEffect(() => { loadPosts() }, [loadPosts])

  async function handleComment() {
    if (!content.trim()) { setError('内容を入力してください'); return }
    setSubmitting(true); setError('')
    try {
      await api.createPost({ school_id: schoolId, content: content.trim(), [filterKey]: parentId })
      setContent('')
      loadPosts()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  async function handleReact(postId, reaction) {
    if (!user) return alert('ログインが必要です')
    await api.reactToPost(postId, { reaction })
    loadPosts()
  }

  async function handleReactRepost(repostId, reaction) {
    if (!user) return alert('ログインが必要です')
    try { await api.reactToRepost(repostId, { reaction }); loadPosts() } catch (e) { alert(e.message) }
  }

  async function handleDelete(id, type = 'post') {
    if (!confirm('削除しますか？')) return
    if (type === 'repost') await api.deleteRepost(id)
    else await api.deletePost(id)
    loadPosts()
  }

  const placeholder = parentType === 'review' ? '返信を入力... (@でメンション)' : 'コメントを入力... (@でメンション)'
  const btnLabel    = parentType === 'review' ? '返信する' : 'コメントする'
  const emptyLabel  = parentType === 'review' ? '返信はまだありません' : 'コメントはまだありません'

  return (
    <div style={{ borderTop: '1px solid var(--border-soft)', padding: '0.75rem 1rem 0.25rem' }}>
      {user && (
        <div style={{ marginBottom: '0.75rem' }}>
          <MentionTextarea
            value={content}
            onChange={setContent}
            placeholder={placeholder}
            rows={2}
            style={{
              width: '100%', background: 'var(--input-bg)', border: '1px solid var(--border)',
              borderRadius: 'var(--r-md)', outline: 'none', color: 'var(--text)',
              fontFamily: 'inherit', fontSize: '0.875rem', resize: 'none',
              padding: '0.5rem 0.75rem', boxSizing: 'border-box',
            }}
          />
          {error && <p className="error" style={{ margin: '0.25rem 0 0', fontSize: '0.8rem' }}>{error}</p>}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.35rem' }}>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleComment}
              disabled={submitting || !content.trim()}
            >
              {submitting ? '送信中...' : btnLabel}
            </button>
          </div>
        </div>
      )}
      {posts === null ? (
        <div className="loading" style={{ padding: '0.5rem 0', fontSize: '0.85rem' }}>読み込み中...</div>
      ) : posts.length === 0 ? (
        <p className="muted" style={{ fontSize: '0.85rem', textAlign: 'center', padding: '0.5rem 0 0.75rem' }}>
          {emptyLabel}
        </p>
      ) : (
        posts.map(post => (
          <PostCard
            key={post.id}
            post={post}
            user={user}
            onReact={handleReact}
            onReactRepost={handleReactRepost}
            onDelete={handleDelete}
            onReplied={loadPosts}
          />
        ))
      )}
    </div>
  )
}

function ReviewComposeForm({ schoolId, courses = [], onSubmitted }) {
  const [rating, setRating]         = useState(0)
  const [comment, setComment]       = useState('')
  const [courseName, setCourseName] = useState('')
  const [error, setError]           = useState('')
  const [submitting, setSubmitting] = useState(false)

  const selectStyle = {
    marginTop: '0.5rem', width: '100%', background: 'var(--card-2)',
    border: '1px solid var(--border)', borderRadius: 'var(--r-md)',
    color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.875rem',
    padding: '0.5rem 0.75rem', outline: 'none', boxSizing: 'border-box',
  }

  async function handleSubmit() {
    if (!rating) { setError('星評価を選択してください'); return }
    setSubmitting(true); setError('')
    try {
      await api.createReview(schoolId, { rating, comment: comment.trim() || null, course_name: courseName || null })
      setRating(0); setComment(''); setCourseName('')
      onSubmitted?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <p style={{ fontWeight: 700, marginBottom: '0.6rem' }}>この大学を評価する</p>
      <StarRating value={rating} onChange={setRating} />
      {courses.length > 0 && (
        <select value={courseName} onChange={e => setCourseName(e.target.value)} style={selectStyle}>
          <option value="">学科・コース（任意）</option>
          {courses.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
        </select>
      )}
      <textarea
        style={{
          marginTop: '0.5rem', width: '100%', background: 'var(--card-2)',
          border: '1px solid var(--border)', borderRadius: 'var(--r-md)',
          color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.875rem',
          padding: '0.6rem 0.75rem', resize: 'vertical', minHeight: 70,
          outline: 'none', boxSizing: 'border-box',
        }}
        placeholder="コメント（任意）"
        value={comment}
        onChange={e => setComment(e.target.value)}
        rows={3}
      />
      {error && <p className="error" style={{ margin: '0.25rem 0 0' }}>{error}</p>}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
        <button
          className="btn btn-primary btn-sm"
          onClick={handleSubmit}
          disabled={submitting || !rating}
        >
          {submitting ? '投稿中...' : '評価を投稿する'}
        </button>
      </div>
    </div>
  )
}

function InlineReportButton({ user, targetType, targetId }) {
  const [open, setOpen]     = useState(false)
  const [reason, setReason] = useState('')
  const [sending, setSending] = useState(false)
  if (!user) return null
  async function handleReport() {
    setSending(true)
    try {
      await api.createReport({ target_type: targetType, target_id: targetId, reason: reason || null })
      setOpen(false); setReason('')
      alert('通報しました。ご協力ありがとうございます。')
    } catch (e) { alert(e.message) }
    finally { setSending(false) }
  }
  return (
    <>
      <button
        className="post-action-btn"
        style={{ fontSize: '0.76rem', color: 'var(--muted)', marginLeft: 'auto' }}
        onClick={() => setOpen(o => !o)}
        title="通報"
      >🚩</button>
      {open && (
        <div style={{
          position: 'absolute', right: 0, top: '100%', zIndex: 200,
          background: 'var(--card)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-md)', padding: '0.75rem', width: 220,
          boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        }}>
          <p style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.4rem' }}>この投稿を通報</p>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="理由（任意）"
            rows={2}
            style={{
              width: '100%', fontSize: '0.82rem', resize: 'none',
              background: 'var(--bg)', border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)', padding: '0.3rem 0.4rem',
              color: 'var(--text)', fontFamily: 'inherit',
            }}
          />
          <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem' }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>キャンセル</button>
            <button className="btn btn-primary btn-sm" onClick={handleReport} disabled={sending}>
              {sending ? '送信中...' : '送信'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}

function ReviewReportButton({ user, reviewId }) {
  return <InlineReportButton user={user} targetType="review" targetId={reviewId} />
}

function IncidentReportButton({ user, incidentId }) {
  return <InlineReportButton user={user} targetType="incident" targetId={incidentId} />
}

function ReviewCard({ review, user, schoolId, onDeleted }) {
  const isOwn   = user && user.id === review.user_id
  const isAdmin = user && user.role === 'admin'
  const [showComments, setShowComments] = useState(false)

  async function handleDelete() {
    if (!confirm('この評価を削除しますか？')) return
    await api.deleteReview(review.id)
    onDeleted?.()
  }

  return (
    <div className="card" style={{ padding: 0, marginBottom: '0.5rem', overflow: 'visible' }}>
      <div style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <Link to={`/users/${review.user_id}`} style={{ flexShrink: 0 }}>
            <Avatar name={review.user_name} avatarUrl={review.user_avatar_url} positionX={review.user_avatar_position_x} positionY={review.user_avatar_position_y} size={36} />
          </Link>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.2rem' }}>
              <Link to={`/users/${review.user_id}`} style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text)', textDecoration: 'none' }}>
                {review.user_name ?? `#${review.user_id}`}
              </Link>
              <StarRating value={review.rating} readOnly />
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', marginLeft: 'auto' }}>
                {fmt(review.created_at)}
              </span>
            </div>
            {review.course_name && (
              <p style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '0.2rem' }}>📚 {review.course_name}</p>
            )}
            {review.comment && (
              <p style={{ fontSize: '0.875rem', color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {review.comment}
              </p>
            )}
          </div>
          {(isOwn || isAdmin) && (
            <button className="post-action-btn delete-btn" style={{ flexShrink: 0 }} onClick={handleDelete}>
              🗑
            </button>
          )}
        </div>
        <div className="post-actions" style={{ marginTop: '0.5rem', paddingTop: '0.4rem', borderTop: '1px solid var(--border-soft)', position: 'relative' }}>
          <button className="post-action-btn reply-btn" onClick={() => setShowComments(v => !v)}>
            💬 {showComments ? '返信を閉じる' : '返信する'}
          </button>
          {user && !isOwn && <ReviewReportButton user={user} reviewId={review.id} />}
        </div>
      </div>
      {showComments && (
        <CommentSection
          parentType="review"
          parentId={review.id}
          schoolId={schoolId}
          user={user}
        />
      )}
    </div>
  )
}

function IncidentEditForm({ inc, onSaved, onCancel }) {
  const [title, setTitle]               = useState(inc.title)
  const [description, setDescription]   = useState(inc.description || '')
  const [courseName, setCourseName]     = useState(inc.course_name || '')
  const [year, setYear]                 = useState(inc.occurred_year  ?? '')
  const [month, setMonth]               = useState(inc.occurred_month ?? '')
  const [day, setDay]                   = useState(inc.occurred_day   ?? '')
  const [error, setError]               = useState('')
  const [submitting, setSubmitting]     = useState(false)

  async function handleSave() {
    if (!title.trim()) { setError('タイトルを入力してください'); return }
    setSubmitting(true); setError('')
    try {
      await api.updateIncident(inc.id, {
        title: title.trim(),
        description: description.trim() || null,
        school_id: inc.school_id,
        course_name: courseName.trim() || null,
        occurred_year:  year  ? Number(year)  : null,
        occurred_month: month ? Number(month) : null,
        occurred_day:   day   ? Number(day)   : null,
      })
      onSaved?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  const inputStyle = {
    width: '100%', padding: '0.45rem 0.7rem', background: 'var(--input-bg)',
    border: '1px solid var(--border)', borderRadius: 'var(--r-md)',
    color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.875rem',
    boxSizing: 'border-box',
  }

  return (
    <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <input style={inputStyle} placeholder="タイトル" value={title} onChange={e => setTitle(e.target.value)} />
      <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 60 }} placeholder="詳細（任意）" value={description} onChange={e => setDescription(e.target.value)} rows={2} />
      <input style={inputStyle} placeholder="コース名（任意）" value={courseName} onChange={e => setCourseName(e.target.value)} />
      <div style={{ display: 'flex', gap: '0.4rem' }}>
        <input style={{ ...inputStyle, flex: 1 }} placeholder="年" type="number" value={year}  onChange={e => setYear(e.target.value)} />
        <input style={{ ...inputStyle, flex: 1 }} placeholder="月" type="number" value={month} onChange={e => setMonth(e.target.value)} />
        <input style={{ ...inputStyle, flex: 1 }} placeholder="日" type="number" value={day}   onChange={e => setDay(e.target.value)} />
      </div>
      {error && <p className="error" style={{ margin: 0, fontSize: '0.8rem' }}>{error}</p>}
      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>キャンセル</button>
        <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={submitting}>
          {submitting ? '保存中...' : '保存'}
        </button>
      </div>
    </div>
  )
}

function IncidentComposeForm({ schoolId, onCreated, onCancel }) {
  const [title, setTitle]               = useState('')
  const [description, setDescription]   = useState('')
  const [courseName, setCourseName]     = useState('')
  const [year, setYear]                 = useState('')
  const [month, setMonth]               = useState('')
  const [day, setDay]                   = useState('')
  const [error, setError]               = useState('')
  const [submitting, setSubmitting]     = useState(false)

  async function handleSubmit() {
    if (!title.trim()) { setError('タイトルを入力してください'); return }
    setSubmitting(true); setError('')
    try {
      await api.createIncident({
        title: title.trim(),
        description: description.trim() || null,
        school_id: schoolId,
        course_name: courseName.trim() || null,
        occurred_year:  year  ? Number(year)  : null,
        occurred_month: month ? Number(month) : null,
        occurred_day:   day   ? Number(day)   : null,
      })
      onCreated?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  const inputStyle = {
    width: '100%', padding: '0.5rem 0.75rem', background: 'var(--input-bg)',
    border: '1px solid var(--border)', borderRadius: 'var(--r-md)',
    color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.9rem',
    boxSizing: 'border-box',
  }

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <h3 style={{ fontWeight: 600, marginBottom: '0.75rem' }}>事件を投稿</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <input style={inputStyle} placeholder="タイトル *" value={title} onChange={e => setTitle(e.target.value)} />
        <textarea
          style={{ ...inputStyle, resize: 'vertical', minHeight: 70 }}
          placeholder="詳細（任意）"
          value={description}
          onChange={e => setDescription(e.target.value)}
          rows={3}
        />
        <input style={inputStyle} placeholder="コース名（任意）" value={courseName} onChange={e => setCourseName(e.target.value)} />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input style={{ ...inputStyle, flex: 1 }} placeholder="年" type="number" min="1900" max="2100" value={year}  onChange={e => setYear(e.target.value)} />
          <input style={{ ...inputStyle, flex: 1 }} placeholder="月" type="number" min="1"    max="12"   value={month} onChange={e => setMonth(e.target.value)} />
          <input style={{ ...inputStyle, flex: 1 }} placeholder="日" type="number" min="1"    max="31"   value={day}   onChange={e => setDay(e.target.value)} />
        </div>
        {error && <p className="error" style={{ margin: 0 }}>{error}</p>}
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          {onCancel && <button className="btn btn-ghost btn-sm" onClick={onCancel}>キャンセル</button>}
          <button className="btn btn-primary btn-sm" onClick={handleSubmit} disabled={submitting}>
            {submitting ? '投稿中...' : '投稿する'}
          </button>
        </div>
      </div>
    </div>
  )
}

function IncidentCard({ inc, user, schoolId, onReact, onDelete, onUpdated }) {
  const [showComments, setShowComments] = useState(false)
  const [editing, setEditing]           = useState(false)
  const isOwn   = user && user.id === inc.user_id
  const isAdmin = user && user.role === 'admin'
  const canEdit = isOwn || isAdmin

  return (
    <div className="card" style={{ padding: 0, marginBottom: '0.75rem', overflow: 'visible' }}>
      <div style={{ padding: '1rem 1rem 0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>{inc.title}</h2>
          {fmtPartialDate(inc) && (
            <span className="badge badge-sakura" style={{ whiteSpace: 'nowrap' }}>📅 発生日 {fmtPartialDate(inc)}</span>
          )}
        </div>
        {editing ? (
          <IncidentEditForm
            inc={inc}
            onSaved={() => { setEditing(false); onUpdated?.() }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <>
            {inc.course_name && (
              <p style={{ marginTop: '0.3rem', fontSize: '0.8rem', color: 'var(--primary)' }}>📚 {inc.course_name}</p>
            )}
            {inc.description && (
              <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--muted)', whiteSpace: 'pre-wrap' }}>{inc.description}</p>
            )}
          </>
        )}
        <div style={{ marginTop: '0.6rem', fontSize: '0.8rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {inc.user_name && (
            <Link to={`/users/${inc.user_id}`} style={{ color: 'var(--muted)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Avatar name={inc.user_name} avatarUrl={inc.user_avatar_url} positionX={inc.user_avatar_position_x} positionY={inc.user_avatar_position_y} size={18} />
              {inc.user_name}
            </Link>
          )}
          <span>投稿日 {fmt(inc.created_at)}</span>
        </div>
        <div className="post-actions" style={{ marginTop: '0.5rem', paddingTop: '0.4rem', borderTop: '1px solid var(--border-soft)', position: 'relative' }}>
          {user && !isOwn && (
            <>
              <button className="post-action-btn like-btn" onClick={() => onReact(inc.id, 'like')}>
                👍 {inc.like_count || ''}
              </button>
              <button className="post-action-btn dislike-btn" onClick={() => onReact(inc.id, 'dislike')}>
                👎 {inc.dislike_count || ''}
              </button>
            </>
          )}
          {(!user || isOwn) && (
            <>
              <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>👍 {inc.like_count || 0}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--muted)', marginLeft: '0.4rem' }}>👎 {inc.dislike_count || 0}</span>
            </>
          )}
          <button className="post-action-btn reply-btn" onClick={() => setShowComments(v => !v)}>
            💬 {inc.comment_count > 0 ? inc.comment_count : ''} {showComments ? '閉じる' : 'コメント'}
          </button>
          {canEdit && !editing && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.25rem' }}>
              {isOwn && (
                <button className="post-action-btn" style={{ fontSize: '0.76rem' }} onClick={() => setEditing(true)}>✏️</button>
              )}
              <button className="post-action-btn delete-btn" onClick={() => onDelete?.(inc.id)}>🗑</button>
            </div>
          )}
          {user && !isOwn && <IncidentReportButton user={user} incidentId={inc.id} />}
        </div>
      </div>
      {showComments && (
        <CommentSection
          parentType="incident"
          parentId={inc.id}
          schoolId={schoolId}
          user={user}
        />
      )}
    </div>
  )
}

export default function SchoolDetailPage() {
  const { id }   = useParams()
  const { user } = useAuth()
  const [school, setSchool]         = useState(null)
  const [tab, setTab]               = useState('courses')

  const [incData, setIncData]               = useState(null)
  const [incSkip, setIncSkip]               = useState(0)
  const [incLoading, setIncLoading]         = useState(false)
  const [showIncCompose, setShowIncCompose] = useState(false)
  const [incSort, setIncSort]               = useState('created_at-desc')
  const [incQ, setIncQ]                     = useState('')

  const [reviewData, setReviewData]       = useState(null)
  const [reviewSkip, setReviewSkip]       = useState(0)
  const [reviewLoading, setReviewLoading] = useState(false)

  const [tlData, setTlData]       = useState(null)
  const [tlSkip, setTlSkip]       = useState(0)
  const [tlOrder, setTlOrder]     = useState('desc')
  const [tlLoading, setTlLoading] = useState(false)

  function loadSchool() {
    api.getSchool(id).then(setSchool)
  }

  useEffect(() => { loadSchool() }, [id])

  const fetchIncidents = useCallback(() => {
    setIncLoading(true)
    const { sort_by, order } = INC_SORT_OPTIONS.find(o => o.value === incSort)
    api.getIncidents({ school_id: id, q: incQ || undefined, sort_by, order, skip: incSkip, limit: INC_LIMIT })
      .then(setIncData)
      .finally(() => setIncLoading(false))
  }, [id, incSkip, incSort, incQ])

  useEffect(() => {
    if (tab === 'incidents') fetchIncidents()
  }, [tab, fetchIncidents])

  const fetchReviews = useCallback(() => {
    setReviewLoading(true)
    api.getReviews(id, { skip: reviewSkip, limit: REVIEW_LIMIT })
      .then(setReviewData)
      .finally(() => setReviewLoading(false))
  }, [id, reviewSkip])

  useEffect(() => {
    if (tab === 'reviews') fetchReviews()
  }, [tab, fetchReviews])

  const fetchTimeline = useCallback(() => {
    setTlLoading(true)
    api.getPosts({ school_id: id, sort_by: 'created_at', order: tlOrder, skip: tlSkip, limit: TIMELINE_LIMIT, top_level_only: true })
      .then(setTlData)
      .finally(() => setTlLoading(false))
  }, [id, tlOrder, tlSkip])

  useEffect(() => {
    if (tab === 'timeline') fetchTimeline()
  }, [tab, fetchTimeline])

  async function handleTlReact(postId, reaction) {
    if (!user) return alert('ログインが必要です')
    try { await api.reactToPost(postId, { reaction }); fetchTimeline() } catch (e) { alert(e.message) }
  }

  async function handleTlReactRepost(repostId, reaction) {
    if (!user) return alert('ログインが必要です')
    try { await api.reactToRepost(repostId, { reaction }); fetchTimeline() } catch (e) { alert(e.message) }
  }

  async function handleTlDelete(id, type = 'post') {
    if (!confirm('削除しますか？')) return
    if (type === 'repost') await api.deleteRepost(id)
    else await api.deletePost(id)
    fetchTimeline()
  }

  async function reactSchool(reaction) {
    if (!user) return alert('ログインが必要です')
    await api.reactToSchool(id, { reaction })
    loadSchool()
  }

  async function reactCourse(courseId, reaction) {
    if (!user) return alert('ログインが必要です')
    await api.reactToCourse(courseId, { reaction })
    loadSchool()
  }

  async function reactIncident(incId, reaction) {
    if (!user) return alert('ログインが必要です')
    await api.reactToIncident(incId, { reaction })
    fetchIncidents()
  }

  async function handleDeleteIncident(incId) {
    if (!confirm('この事件を削除しますか？')) return
    await api.deleteIncident(incId)
    fetchIncidents()
  }

  if (!school) return <div className="loading">読み込み中...</div>

  const maxDev = Math.max(...school.courses.map(c => c.deviation), 0)

  return (
    <div className="container">
      <Link to="/" className="muted" style={{ fontSize: '0.875rem', textDecoration: 'none' }}>
        ← 大学一覧に戻る
      </Link>

      <div style={{ margin: '1.25rem 0 1rem' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>{school.name}</h1>
        <p className="muted">{school.prefecture}</p>
        <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.75rem' }}>
          <button className="react-btn" onClick={() => reactSchool('like')}>
            👍 {school.like_count}
          </button>
          <button className="react-btn" onClick={() => reactSchool('dislike')}>
            👎 {school.dislike_count}
          </button>
        </div>
      </div>

      <div className="tabs">
        <div className={`tab ${tab === 'courses'   ? 'active' : ''}`} onClick={() => setTab('courses')}>コース</div>
        <div className={`tab ${tab === 'timeline'  ? 'active' : ''}`} onClick={() => setTab('timeline')}>タイムライン</div>
        <div className={`tab ${tab === 'reviews'   ? 'active' : ''}`} onClick={() => setTab('reviews')}>評価</div>
        <div className={`tab ${tab === 'incidents' ? 'active' : ''}`} onClick={() => setTab('incidents')}>事件</div>
      </div>

      {/* コース一覧 */}
      {tab === 'courses' && (
        school.courses.length === 0 ? (
          <p className="muted">登録されているコースはありません</p>
        ) : (
          <div className="grid">
            {school.courses
              .sort((a, b) => b.deviation - a.deviation)
              .map(c => (
                <div key={c.id} className="card">
                  <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>コース</p>
                  <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>{c.name}</h3>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.4rem', marginBottom: '0.75rem' }}>
                    <span style={{
                      fontSize: '2.2rem', fontWeight: 700,
                      color: c.deviation === maxDev ? 'var(--primary)' : 'var(--text)',
                    }}>
                      {c.deviation}
                    </span>
                    <span className="muted" style={{ paddingBottom: '0.35rem', fontSize: '0.85rem' }}>偏差値</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button className="react-btn" style={{ fontSize: '0.8rem' }} onClick={() => reactCourse(c.id, 'like')}>
                      👍 {c.like_count}
                    </button>
                    <button className="react-btn" style={{ fontSize: '0.8rem' }} onClick={() => reactCourse(c.id, 'dislike')}>
                      👎 {c.dislike_count}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )
      )}

      {/* タイムラインタブ */}
      {tab === 'timeline' && (
        <>
          {user && (
            <ComposeArea
              user={user}
              fixedSchoolId={Number(id)}
              fixedSchoolName={school.name}
              onPosted={fetchTimeline}
            />
          )}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
            <select
              value={tlOrder}
              onChange={e => { setTlOrder(e.target.value); setTlSkip(0) }}
              style={{
                padding: '0.4rem 0.8rem', border: '1px solid var(--border)',
                borderRadius: 'var(--r-pill)', background: 'var(--card)',
                color: 'var(--text)', fontSize: '0.85rem', fontFamily: 'inherit',
              }}
            >
              <option value="desc">新しい順</option>
              <option value="asc">古い順</option>
            </select>
          </div>
          {tlLoading ? (
            <div className="loading">読み込み中...</div>
          ) : (
            <>
              {tlData?.items.length === 0 && (
                <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                  この大学の投稿はまだありません
                </p>
              )}
              {tlData?.items.map(post => (
                <PostCard
                  key={post.id}
                  post={post}
                  user={user}
                  onReact={handleTlReact}
                  onReactRepost={handleTlReactRepost}
                  onDelete={handleTlDelete}
                  onReplied={fetchTimeline}
                />
              ))}
              {tlData && (
                <Pagination skip={tlSkip} limit={TIMELINE_LIMIT} total={tlData.total} onChange={setTlSkip} />
              )}
            </>
          )}
        </>
      )}

      {/* 評価タブ */}
      {tab === 'reviews' && (
        <>
          {user && (
            <ReviewComposeForm
              schoolId={Number(id)}
              courses={school.courses}
              onSubmitted={() => { fetchReviews(); loadSchool() }}
            />
          )}
          {reviewLoading ? (
            <div className="loading">読み込み中...</div>
          ) : (
            <>
              {reviewData?.items.length === 0 && (
                <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                  まだ評価がありません。最初に評価しませんか？
                </p>
              )}
              {reviewData?.items.map(rv => (
                <ReviewCard
                  key={rv.id}
                  review={rv}
                  user={user}
                  schoolId={Number(id)}
                  onDeleted={fetchReviews}
                />
              ))}
              {reviewData && (
                <Pagination skip={reviewSkip} limit={REVIEW_LIMIT} total={reviewData.total} onChange={setReviewSkip} />
              )}
            </>
          )}
        </>
      )}

      {/* 事件一覧 */}
      {tab === 'incidents' && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
            <input
              placeholder="🔍 タイトル・内容で検索..."
              value={incQ}
              onChange={e => { setIncQ(e.target.value); setIncSkip(0) }}
              style={{
                flex: 1, minWidth: 160, padding: '0.4rem 0.75rem',
                border: '1px solid var(--border)', borderRadius: 'var(--r-pill)',
                background: 'var(--card)', color: 'var(--text)',
                fontSize: '0.85rem', fontFamily: 'inherit', outline: 'none',
              }}
            />
            <select
              value={incSort}
              onChange={e => { setIncSort(e.target.value); setIncSkip(0) }}
              style={{
                padding: '0.4rem 0.8rem', border: '1px solid var(--border)',
                borderRadius: 'var(--r-pill)', background: 'var(--card)',
                color: 'var(--text)', fontSize: '0.85rem', fontFamily: 'inherit',
              }}
            >
              {INC_SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            {user && (
              <button className="btn btn-primary btn-sm" onClick={() => setShowIncCompose(v => !v)}>
                {showIncCompose ? '✕ 閉じる' : '＋ 事件を投稿'}
              </button>
            )}
          </div>
          {user && showIncCompose && (
            <IncidentComposeForm
              schoolId={Number(id)}
              onCreated={() => { setShowIncCompose(false); fetchIncidents() }}
              onCancel={() => setShowIncCompose(false)}
            />
          )}
          {incLoading ? (
            <div className="loading">読み込み中...</div>
          ) : (
            <>
              {incData?.items.length === 0 && (
                <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                  この大学の事件はありません
                </p>
              )}
              {incData?.items.map(inc => (
                <IncidentCard
                  key={inc.id}
                  inc={inc}
                  user={user}
                  schoolId={Number(id)}
                  onReact={reactIncident}
                  onDelete={handleDeleteIncident}
                  onUpdated={fetchIncidents}
                />
              ))}
              {incData && (
                <Pagination skip={incSkip} limit={INC_LIMIT} total={incData.total} onChange={setIncSkip} />
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
