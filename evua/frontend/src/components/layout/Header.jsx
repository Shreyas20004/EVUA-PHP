export default function Header() {
  return (
    <header style={{
      height: 'var(--header-height)',
      background: 'var(--color-surface)',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: 12,
      flexShrink: 0,
    }}>
      <span style={{ color: 'var(--color-primary)', fontWeight: 800, fontSize: '1.2rem' }}>
        evua
      </span>
      <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
        PHP Migration Tool
      </span>
    </header>
  )
}
