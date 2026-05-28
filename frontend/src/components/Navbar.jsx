import { useState, useEffect, useRef } from 'react'
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const AVATAR_COLORS = [
  ['#29B6F6','#0288D1'],['#66BB6A','#2E7D32'],['#AB47BC','#6A1B9A'],
  ['#FF7043','#BF360C'],['#26C6DA','#00838F'],['#EC407A','#880E4F'],
]

function NavAvatar({ user, size = 28 }) {
  const [bg, fg] = AVATAR_COLORS[(user.name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length]
  if (user.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt={user.name}
        style={{
          width: size, height: size, borderRadius: '50%',
          objectFit: 'cover', flexShrink: 0,
          border: '1.5px solid rgba(255,255,255,0.18)',
        }}
      />
    )
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: `linear-gradient(135deg, ${bg}, ${fg})`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.42, fontWeight: 800, color: '#fff', flexShrink: 0,
    }}>
      {user.name?.charAt(0).toUpperCase()}
    </div>
  )
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  // ページ遷移時に閉じる
  useEffect(() => { setMenuOpen(false) }, [location.pathname])

  // 外側クリックで閉じる
  useEffect(() => {
    if (!menuOpen) return
    function handler(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [menuOpen])

  function handleLogout() {
    logout()
    navigate('/')
    setMenuOpen(false)
  }

  return (
    <nav className="navbar" ref={menuRef}>
      <Link to="/" className="navbar-brand">
        <img src="/logo-em.svg" alt="ExaMininfo" />
      </Link>

      {/* PC: 通常ナビ */}
      <div className="navbar-links navbar-links-pc">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>大学</NavLink>
        <NavLink to="/incidents" className={({ isActive }) => isActive ? 'active' : ''}>事件</NavLink>
        <NavLink to="/posts" className={({ isActive }) => isActive ? 'active' : ''}>タイムライン</NavLink>
        {user?.role === 'admin' && (
          <NavLink to="/admin" className={({ isActive }) => isActive ? 'active' : ''}>管理</NavLink>
        )}
      </div>

      <div className="navbar-right navbar-right-pc">
        {user ? (
          <>
            <Link to="/account" className="navbar-user-name">
              <NavAvatar user={user} size={28} />
              {user.name}
            </Link>
            <button className="btn btn-secondary btn-sm" onClick={handleLogout}>ログアウト</button>
          </>
        ) : (
          <Link to="/login">
            <button className="btn btn-primary btn-sm">ログイン</button>
          </Link>
        )}
      </div>

      {/* スマホ: ハンバーガーボタン */}
      <button
        className="navbar-hamburger"
        onClick={() => setMenuOpen(o => !o)}
        aria-label="メニュー"
      >
        <span className={`hamburger-line ${menuOpen ? 'open-1' : ''}`} />
        <span className={`hamburger-line ${menuOpen ? 'open-2' : ''}`} />
        <span className={`hamburger-line ${menuOpen ? 'open-3' : ''}`} />
      </button>

      {/* スマホ: ドロップダウンメニュー */}
      {menuOpen && (
        <div className="navbar-mobile-menu">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'mobile-nav-item active' : 'mobile-nav-item'}>大学</NavLink>
          <NavLink to="/incidents" className={({ isActive }) => isActive ? 'mobile-nav-item active' : 'mobile-nav-item'}>事件</NavLink>
          <NavLink to="/posts" className={({ isActive }) => isActive ? 'mobile-nav-item active' : 'mobile-nav-item'}>タイムライン</NavLink>
          {user?.role === 'admin' && (
            <NavLink to="/admin" className={({ isActive }) => isActive ? 'mobile-nav-item active' : 'mobile-nav-item'}>管理</NavLink>
          )}
          <div className="mobile-nav-divider" />
          {user ? (
            <>
              <Link to="/account" className="mobile-nav-item" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }} onClick={() => setMenuOpen(false)}>
                <NavAvatar user={user} size={24} />
                {user.name}
              </Link>
              <button className="mobile-nav-item mobile-nav-logout" onClick={handleLogout}>
                ログアウト
              </button>
            </>
          ) : (
            <Link to="/login" className="mobile-nav-item" style={{ color: 'var(--primary)', fontWeight: 700 }}>
              ログイン
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}
