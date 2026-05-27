import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import Topbar from '../components/Topbar.jsx'

function UniformCard({ u }) {
  const minPrice = u.prices
    ?.filter(p => p.price_id)
    .reduce((min, p) => Math.min(min, parseFloat(p.amount)), Infinity)

  return (
    <Link to={`/gallery/${u.uniform_id}`} className="uniform-card">
      {u.image_path
        ? <img
            src={u.image_path}
            alt={u.uniform_type}
            className="uniform-card-img"
            onError={e => {
              e.target.style.display = 'none'
              e.target.nextSibling.style.display = 'flex'
            }}
          />
        : null}
      <div
        className="uniform-card-img-placeholder"
        style={{ display: u.image_path ? 'none' : 'flex' }}
      >
        {u.uniform_type?.includes('PE') ? '🏃' : '👔'}
      </div>
      <div className="uniform-card-body">
        <div className="uniform-card-name">{u.uniform_type}</div>
        <p className="uniform-card-desc">{u.description}</p>
        {isFinite(minPrice) && (
          <span className="price-tag">
            <span className="peso">₱</span>
            {minPrice.toFixed(2)}{' '}
            <span style={{ color: 'var(--ink-soft)', fontWeight: 400 }}>& up</span>
          </span>
        )}
      </div>
    </Link>
  )
}

export default function GalleryPage() {
  const { authFetch } = useAuth()
  const [uniforms, setUniforms] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  useEffect(() => {
    authFetch('/api/uniforms')
      .then(r => r.json())
      .then(d => setUniforms(d.uniforms || []))
      .catch(() => setError('Failed to load uniforms.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="app-shell">
      <Topbar />
      <div className="page-content">
        <header className="page-header fade-up">
          <div className="eyebrow">Gallery</div>
          <h1>Uniform Gallery & Price List</h1>
          <p>Official school-approved attire with current prices per size.</p>
        </header>

        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div className="spinner" style={{ margin: '0 auto' }} />
          </div>
        )}

        {error && <div className="error-msg">{error}</div>}

        {!loading && !error && uniforms.length === 0 && (
          <div className="empty-state">
            <div className="icon">👗</div>
            <h3>No uniforms found</h3>
            <p>Check back later or ask your administrator to add uniform entries.</p>
          </div>
        )}

        {!loading && !error && uniforms.length > 0 && (
          <div className="gallery-grid fade-up">
            {uniforms.map(u => <UniformCard key={u.uniform_id} u={u} />)}
          </div>
        )}

        <div style={{ marginTop: 40 }}>
          <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
        </div>
      </div>
    </div>
  )
}
