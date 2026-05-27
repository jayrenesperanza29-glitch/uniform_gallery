import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import Topbar from "../components/Topbar.jsx";

export default function UniformDetail() {
  const { id } = useParams();
  const { authFetch } = useAuth();
  const [uniform, setUniform] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    authFetch(`/api/uniforms/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setUniform)
      .catch(() => setError("Uniform not found"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading)
    return (
      <div className="app-shell">
        <Topbar />
        <div className="splash">
          <div className="spinner" />
        </div>
      </div>
    );

  if (error || !uniform)
    return (
      <div className="app-shell">
        <Topbar />
        <div className="page-content">
          <div className="error-msg">{error || "Not found"}</div>
          <Link to="/gallery" className="back-link">
            ← Back to Gallery
          </Link>
        </div>
      </div>
    );

  const icon = uniform.uniform_type?.includes("PE") ? "🏃" : "👔";

  return (
    <div className="app-shell">
      <Topbar />
      <div className="page-content">
        <Link to="/gallery" className="back-link fade-up">
          ← Back to Gallery
        </Link>

        <div className="detail-grid">
          {/* Image */}
          <div className="fade-up fade-up-1">
            {uniform.image_path ? (
              <img
                src={uniform.image_path}
                alt={uniform.uniform_type}
                className="detail-img"
                onError={(e) => {
                  e.target.style.display = "none";
                  e.target.nextSibling.style.display = "flex";
                }}
              />
            ) : null}
            <div
              className="detail-img-placeholder"
              style={{ display: uniform.image_path ? "none" : "flex" }}
            >
              {icon}
            </div>
          </div>

          {/* Info */}
          <div className="detail-info fade-up fade-up-2">
            <div className="badge">{uniform.uniform_type}</div>
            <h1>{uniform.uniform_type}</h1>
            <p className="desc">{uniform.description}</p>

            {/* Price table */}
            {uniform.prices?.length > 0 && (
              <>
                <h3
                  style={{
                    fontFamily: "var(--font-head)",
                    fontSize: "1.15rem",
                    marginBottom: 14,
                  }}
                >
                  Price List by Size
                </h3>
                <table className="price-table">
                  <thead>
                    <tr>
                      <th>Size</th>
                      <th>Price (PHP)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uniform.prices.map((p) => (
                      <tr key={p.price_id}>
                        <td>
                          <strong>{p.label}</strong>
                        </td>
                        <td className="amt">
                          ₱ {parseFloat(p.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            <Link
              to="/dashboard"
              className="btn btn-secondary"
              style={{ display: "inline-flex", textDecoration: "none" }}
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
