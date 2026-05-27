import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
    setMenuOpen(false);
  };

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "?";

  return (
    <nav className="topbar">
      <Link
        to="/dashboard"
        className="topbar-brand"
        onClick={() => setMenuOpen(false)}
      >
        🎓 Uniform <span>Gallery</span>
      </Link>

      {/* Desktop nav */}
      <div className="topbar-nav desktop-nav">
        {user && (
          <div className="user-chip">
            <div className="avatar">{initials}</div>
            <span className="user-name">{user.name}</span>
            {user.is_admin && <span className="tag-admin">Admin</span>}
          </div>
        )}
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/gallery">Gallery</NavLink>
        {user?.is_admin && <NavLink to="/admin">Manage</NavLink>}
        <button className="nav-logout" onClick={handleLogout}>
          Sign Out
        </button>
      </div>

      {/* Mobile: avatar + hamburger */}
      <div className="mobile-controls">
        {user && <div className="avatar mobile-avatar">{initials}</div>}
        <button
          className="hamburger"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
        >
          <span className={`ham-line ${menuOpen ? "open" : ""}`} />
          <span className={`ham-line ${menuOpen ? "open" : ""}`} />
          <span className={`ham-line ${menuOpen ? "open" : ""}`} />
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="mobile-menu">
          {user && (
            <div className="mobile-user-info">
              <div className="avatar">{initials}</div>
              <div>
                <div className="mobile-user-name">{user.name}</div>
                {user.is_admin && <span className="tag-admin">Admin</span>}
              </div>
            </div>
          )}
          <NavLink to="/dashboard" onClick={() => setMenuOpen(false)}>
            Dashboard
          </NavLink>
          <NavLink to="/gallery" onClick={() => setMenuOpen(false)}>
            Gallery
          </NavLink>
          {user?.is_admin && (
            <NavLink to="/admin" onClick={() => setMenuOpen(false)}>
              Manage
            </NavLink>
          )}
          <button className="nav-logout mobile-logout" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      )}
    </nav>
  );
}
