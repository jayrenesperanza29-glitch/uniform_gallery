import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import Topbar from "../components/Topbar.jsx";

export default function Dashboard() {
  const { user } = useAuth();

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="app-shell">
      <Topbar />
      <div className="page-content">
        <header className="page-header fade-up">
          <div className="eyebrow">Dashboard</div>
          <h1>
            {greeting()}, {user?.name?.split(" ")[0]}.
          </h1>
          <p>
            Browse the official DLSP uniform gallery and check current prices.
          </p>
        </header>

        <div className="dash-grid">
          <Link to="/gallery" className="dash-card fade-up fade-up-1">
            <div className="dash-card-icon">👔</div>
            <h3>View Gallery & Price List</h3>
            <p>
              Browse all approved DLSP uniforms with images and prices per size.
            </p>
          </Link>

          {user?.is_admin && (
            <Link
              to="/admin"
              className="dash-card fade-up fade-up-2"
              style={{ borderColor: "var(--gold)" }}
            >
              <div className="dash-card-icon">⚙️</div>
              <h3>Admin Panel</h3>
              <p>
                Manage uniforms, prices, images, and view registered students.
              </p>
            </Link>
          )}
        </div>

        <footer
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: 24,
            color: "var(--ink-soft)",
            fontSize: "0.82rem",
          }}
        >
          <p>
            DLSP Uniform Gallery · Official Reference System ·{" "}
            {new Date().getFullYear()}
          </p>
        </footer>
      </div>
    </div>
  );
}
