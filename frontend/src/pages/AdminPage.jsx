import { useEffect, useState, useRef } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Topbar from '../components/Topbar.jsx'

// ── Uniform modal ─────────────────────────────────────────────────────────────
function UniformModal({ uniform, onClose, onSave, authFetch }) {
  const [form, setForm]         = useState(uniform || { uniform_type: '', description: '', image_path: '' })
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef()
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleUpload = async e => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res  = await authFetch('/api/admin/upload', { method: 'POST', body: fd })
      const text = await res.text()
      let d
      try { d = JSON.parse(text) } catch { throw new Error(`Server error (${res.status})`) }
      if (!res.ok) throw new Error(d.error)
      setForm(f => ({ ...f, image_path: d.image_path }))
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleSave = async () => {
    if (!form.uniform_type.trim()) { setError('Uniform type is required'); return }
    setLoading(true)
    try {
      const url    = uniform ? `/api/admin/uniforms/${uniform.uniform_id}` : '/api/admin/uniforms'
      const method = uniform ? 'PUT' : 'POST'
      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const text = await res.text()
        let msg = `Server error (${res.status})`
        try { msg = JSON.parse(text).error || msg } catch {}
        throw new Error(msg)
      }
      onSave()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>{uniform ? 'Edit Uniform' : 'Add Uniform'}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {error && <div className="error-msg">{error}</div>}
        <div className="field">
          <label>Uniform Type</label>
          <input value={form.uniform_type} onChange={set('uniform_type')} placeholder="e.g. Proper Uniform" />
        </div>
        <div className="field">
          <label>Description</label>
          <textarea value={form.description} onChange={set('description')} placeholder="Describe the uniform..." />
        </div>
        <div className="field">
          <label>Image</label>
          <input value={form.image_path} onChange={set('image_path')} placeholder="/static/images/filename.png" />
          <div style={{ marginTop: 8 }}>
            <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleUpload} />
            <button className="btn btn-ghost btn-sm" onClick={() => fileRef.current?.click()} disabled={uploading}>
              {uploading ? 'Uploading…' : '📁 Upload Image'}
            </button>
          </div>
          {form.image_path && (
            <img src={form.image_path} alt="" style={{ marginTop: 12, maxHeight: 120, borderRadius: 4, border: '1px solid var(--border)' }} />
          )}
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={loading} style={{ width: 'auto' }}>
            {loading ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Price modal ───────────────────────────────────────────────────────────────
function PriceModal({ price, uniforms, onClose, onSave, authFetch }) {
  const [form, setForm]     = useState(price || { uniform_id: uniforms[0]?.uniform_id || '', label: 'S', amount: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSave = async () => {
    if (!form.amount) { setError('Amount is required'); return }
    setLoading(true)
    try {
      const url    = price ? `/api/admin/prices/${price.price_id}` : '/api/admin/prices'
      const method = price ? 'PUT' : 'POST'
      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) }),
      })
      if (!res.ok) {
        const text = await res.text()
        let msg = `Server error (${res.status})`
        try { msg = JSON.parse(text).error || msg } catch {}
        throw new Error(msg)
      }
      onSave()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>{price ? 'Edit Price' : 'Add Price'}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {error && <div className="error-msg">{error}</div>}
        {!price && (
          <div className="field">
            <label>Uniform</label>
            <select value={form.uniform_id} onChange={set('uniform_id')}>
              {uniforms.map(u => <option key={u.uniform_id} value={u.uniform_id}>{u.uniform_type}</option>)}
            </select>
          </div>
        )}
        <div className="field">
          <label>Size / Label</label>
          <input value={form.label} onChange={set('label')} placeholder="XS, S, M, L, XL, XXL..." />
        </div>
        <div className="field">
          <label>Amount (PHP)</label>
          <input type="number" min="0" step="0.01" value={form.amount} onChange={set('amount')} placeholder="450.00" />
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={loading} style={{ width: 'auto' }}>
            {loading ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Mobile card components ────────────────────────────────────────────────────
function UniformCard({ u, onEdit, onDelete }) {
  return (
    <div className="admin-card">
      <div className="admin-card-row">
        {u.image_path
          ? <img src={u.image_path} alt="" className="admin-card-img" onError={e => e.target.style.display = 'none'} />
          : <div className="admin-card-img-placeholder">👔</div>
        }
        <div className="admin-card-body">
          <div className="admin-card-id">#{u.uniform_id}</div>
          <div className="admin-card-title">{u.uniform_type}</div>
          <p className="admin-card-desc">{u.description}</p>
        </div>
      </div>
      <div className="admin-card-actions">
        <button className="btn btn-ghost btn-sm" onClick={() => onEdit(u)}>Edit</button>
        <button className="btn btn-danger btn-sm" onClick={() => onDelete(u.uniform_id)}>Delete</button>
      </div>
    </div>
  )
}

function PriceCard({ p, onEdit, onDelete }) {
  return (
    <div className="admin-card">
      <div className="admin-card-price-row">
        <div>
          <div className="admin-card-id">#{p.price_id}</div>
          <div className="admin-card-title">{p.uniform_type}</div>
          <div className="admin-card-size">Size: <strong>{p.label}</strong></div>
        </div>
        <div className="admin-card-amount">₱ {parseFloat(p.amount).toFixed(2)}</div>
      </div>
      <div className="admin-card-actions">
        <button className="btn btn-ghost btn-sm" onClick={() => onEdit(p)}>Edit</button>
        <button className="btn btn-danger btn-sm" onClick={() => onDelete(p.price_id)}>Delete</button>
      </div>
    </div>
  )
}

function StudentCard({ s }) {
  return (
    <div className="admin-card">
      <div className="admin-card-student-row">
        <div className="admin-card-avatar">{s.student_name?.[0]?.toUpperCase() || '?'}</div>
        <div>
          <div className="admin-card-title">{s.student_name}</div>
          <div className="admin-card-email">{s.email}</div>
          <div className="admin-card-date">
            Registered {new Date(s.created_at).toLocaleDateString('en-PH', { year: 'numeric', month: 'short', day: 'numeric' })}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main AdminPage ────────────────────────────────────────────────────────────
export default function AdminPage() {
  const { authFetch } = useAuth()
  const [tab, setTab]           = useState('uniforms')
  const [uniforms, setUniforms] = useState([])
  const [allPrices, setAllPrices] = useState([])
  const [students, setStudents] = useState([])
  const [uModal, setUModal]     = useState(null)
  const [pModal, setPModal]     = useState(null)
  const [msg, setMsg]           = useState('')

  const loadUniforms = () => {
    authFetch('/api/uniforms').then(r => r.json()).then(d => {
      setUniforms(d.uniforms || [])
      setAllPrices((d.uniforms || []).flatMap(u =>
        (u.prices || []).map(p => ({ ...p, uniform_type: u.uniform_type }))
      ))
    })
  }

  const loadStudents = () => {
    authFetch('/api/admin/students').then(r => r.json()).then(d => setStudents(d.students || []))
  }

  useEffect(() => { loadUniforms(); loadStudents() }, [])

  const deleteUniform = async id => {
    if (!confirm('Delete this uniform and all its prices?')) return
    await authFetch(`/api/admin/uniforms/${id}`, { method: 'DELETE' })
    setMsg('Uniform deleted.')
    loadUniforms()
  }

  const deletePrice = async id => {
    if (!confirm('Delete this price entry?')) return
    await authFetch(`/api/admin/prices/${id}`, { method: 'DELETE' })
    setMsg('Price deleted.')
    loadUniforms()
  }

  const onSave = () => {
    setUModal(null); setPModal(null)
    setMsg('Saved successfully.')
    loadUniforms()
  }

  const EMPTY = (cols, msg) => (
    <tr><td colSpan={cols} style={{ textAlign: 'center', color: 'var(--ink-soft)', padding: '32px' }}>{msg}</td></tr>
  )

  return (
    <div className="app-shell">
      <Topbar />
      <div className="page-content">
        <header className="page-header fade-up">
          <div className="eyebrow">Admin</div>
          <h1>Management Panel</h1>
          <p>Manage uniforms, prices, and student accounts.</p>
        </header>

        {msg && <div className="success-msg fade-up">{msg}</div>}

        <div className="admin-tabs">
          {['uniforms', 'prices', 'students'].map(t => (
            <button key={t} className={`admin-tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* ── UNIFORMS ── */}
        {tab === 'uniforms' && (
          <div className="fade-up">
            <div className="admin-section-header">
              <h2>Uniforms</h2>
              <button className="btn btn-primary btn-sm" style={{ width: 'auto' }} onClick={() => setUModal('new')}>
                + Add Uniform
              </button>
            </div>

            {/* Desktop table */}
            <div className="admin-table-wrap">
              <table className="data-table">
                <thead><tr><th>ID</th><th>Type</th><th>Description</th><th>Image</th><th>Actions</th></tr></thead>
                <tbody>
                  {uniforms.map(u => (
                    <tr key={u.uniform_id}>
                      <td>{u.uniform_id}</td>
                      <td><strong>{u.uniform_type}</strong></td>
                      <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{u.description}</td>
                      <td>
                        {u.image_path
                          ? <img src={u.image_path} alt="" style={{ height: 40, borderRadius: 3 }} onError={e => e.target.style.display = 'none'} />
                          : <span style={{ color: 'var(--ink-soft)', fontSize: '0.8rem' }}>None</span>}
                      </td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-ghost btn-sm" onClick={() => setUModal(u)}>Edit</button>
                          <button className="btn btn-danger btn-sm" onClick={() => deleteUniform(u.uniform_id)}>Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {uniforms.length === 0 && EMPTY(5, 'No uniforms yet.')}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="admin-cards">
              {uniforms.map(u => (
                <UniformCard key={u.uniform_id} u={u} onEdit={setUModal} onDelete={deleteUniform} />
              ))}
              {uniforms.length === 0 && <p className="admin-empty">No uniforms yet.</p>}
            </div>
          </div>
        )}

        {/* ── PRICES ── */}
        {tab === 'prices' && (
          <div className="fade-up">
            <div className="admin-section-header">
              <h2>Prices</h2>
              <button className="btn btn-primary btn-sm" style={{ width: 'auto' }} onClick={() => setPModal('new')} disabled={uniforms.length === 0}>
                + Add Price
              </button>
            </div>

            {/* Desktop table */}
            <div className="admin-table-wrap">
              <table className="data-table">
                <thead><tr><th>ID</th><th>Uniform</th><th>Size</th><th>Amount</th><th>Actions</th></tr></thead>
                <tbody>
                  {allPrices.map(p => (
                    <tr key={p.price_id}>
                      <td>{p.price_id}</td>
                      <td>{p.uniform_type}</td>
                      <td><strong>{p.label}</strong></td>
                      <td style={{ color: 'var(--accent)', fontWeight: 700 }}>₱ {parseFloat(p.amount).toFixed(2)}</td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-ghost btn-sm" onClick={() => setPModal(p)}>Edit</button>
                          <button className="btn btn-danger btn-sm" onClick={() => deletePrice(p.price_id)}>Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {allPrices.length === 0 && EMPTY(5, 'No prices yet.')}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="admin-cards">
              {allPrices.map(p => (
                <PriceCard key={p.price_id} p={p} onEdit={setPModal} onDelete={deletePrice} />
              ))}
              {allPrices.length === 0 && <p className="admin-empty">No prices yet.</p>}
            </div>
          </div>
        )}

        {/* ── STUDENTS ── */}
        {tab === 'students' && (
          <div className="fade-up">
            <div className="admin-section-header">
              <h2>Registered Students</h2>
              <span style={{ color: 'var(--ink-soft)', fontSize: '0.88rem' }}>{students.length} total</span>
            </div>

            {/* Desktop table */}
            <div className="admin-table-wrap">
              <table className="data-table">
                <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Registered</th></tr></thead>
                <tbody>
                  {students.map(s => (
                    <tr key={s.student_id}>
                      <td>{s.student_id}</td>
                      <td><strong>{s.student_name}</strong></td>
                      <td>{s.email}</td>
                      <td>{new Date(s.created_at).toLocaleDateString('en-PH', { year: 'numeric', month: 'short', day: 'numeric' })}</td>
                    </tr>
                  ))}
                  {students.length === 0 && EMPTY(4, 'No students registered yet.')}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="admin-cards">
              {students.map(s => <StudentCard key={s.student_id} s={s} />)}
              {students.length === 0 && <p className="admin-empty">No students registered yet.</p>}
            </div>
          </div>
        )}
      </div>

      {uModal && (
        <UniformModal
          uniform={uModal === 'new' ? null : uModal}
          onClose={() => setUModal(null)}
          onSave={onSave}
          authFetch={authFetch}
        />
      )}
      {pModal && (
        <PriceModal
          price={pModal === 'new' ? null : pModal}
          uniforms={uniforms}
          onClose={() => setPModal(null)}
          onSave={onSave}
          authFetch={authFetch}
        />
      )}
    </div>
  )
}
