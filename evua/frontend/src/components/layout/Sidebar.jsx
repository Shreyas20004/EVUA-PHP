import { Link, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '⬡' },
  { to: '/migrate', label: 'Migrate', icon: '⇄' },
]

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <nav style={{
      width: 'var(--sidebar-width)',
      background: 'var(--color-surface)',
      borderRight: '1px solid var(--color-border)',
      padding: '16px 0',
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      flexShrink: 0,
    }}>
      {NAV.map(({ to, label, icon }) => {
        const active = pathname.startsWith(to)
        return (
          <Link
            key={to}
            to={to}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 20px',
              borderRadius: 6,
              margin: '0 8px',
              color: active ? '#fff' : 'var(--color-text-muted)',
              background: active ? 'rgba(124,106,247,0.15)' : 'transparent',
              fontWeight: active ? 600 : 400,
              textDecoration: 'none',
              transition: 'background 0.15s, color 0.15s',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>{icon}</span>
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
