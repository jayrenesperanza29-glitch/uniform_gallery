import { createContext, useContext, useState, useEffect } from "react";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("ug_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((data) => setUser(data.user))
        .catch(() => {
          setToken(null);
          localStorage.removeItem("ug_token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    localStorage.setItem("ug_token", data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  const register = async (student_name, email, password) => {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    return data;
  };

  const logout = () => {
    localStorage.removeItem("ug_token");
    setToken(null);
    setUser(null);
  };

  // authFetch: authenticated wrapper used by all protected pages / AdminPage
  const authFetch = (path, opts = {}) => {
    const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
    return fetch(url, {
      ...opts,
      headers: { ...opts.headers, Authorization: `Bearer ${token}` },
    });
  };

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
