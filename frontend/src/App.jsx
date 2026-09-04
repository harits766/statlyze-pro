import { useEffect, useState } from "react";
import { getMe } from "./api";
import Login from "./pages/Login";
import Datasets from "./pages/Datasets";
import Insights from "./pages/Insights";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("statlyze_token"));
  const [user, setUser] = useState(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);

  // Token disimpan di localStorage, jadi bisa aja isinya token lama yang udah
  // kedaluwarsa pas halaman dibuka lagi. Panggil /me sekali buat mastiin
  // token-nya masih kepakai -- sekalian dapat username buat ditampilin.
  useEffect(() => {
    // Nggak perlu ngosongin user di sini -- handleLogout udah ngurus itu.
    if (!token) return;

    let cancelled = false;
    getMe(token)
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch((err) => {
        // Cuma logout kalau tokennya emang ditolak. Kalau backend lagi mati
        // atau internet putus, biarin user tetap di dalam.
        if (!cancelled && err.status === 401) handleLogout();
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  function handleLogin(newToken) {
    localStorage.setItem("statlyze_token", newToken);
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem("statlyze_token");
    setToken(null);
    setUser(null);
    setSelectedDatasetId(null);
  }

  if (!token) {
    return (
      <div className="page-center">
        <Login onLogin={handleLogin} />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">statlyze</span>
        <span className="header-right">
          {user && <span className="current-user">@{user.username}</span>}
          <button type="button" className="link-button" onClick={handleLogout}>
            Keluar
          </button>
        </span>
      </header>

      <main className="app-main">
        {selectedDatasetId === null ? (
          <Datasets token={token} onSelectDataset={setSelectedDatasetId} />
        ) : (
          <Insights
            token={token}
            datasetId={selectedDatasetId}
            onBack={() => setSelectedDatasetId(null)}
          />
        )}
      </main>
    </div>
  );
}
