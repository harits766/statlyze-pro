import { useState } from "react";
import Login from "./pages/Login";
import Datasets from "./pages/Datasets";
import Insights from "./pages/Insights";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("statlyze_token"));
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);

  function handleLogin(newToken) {
    localStorage.setItem("statlyze_token", newToken);
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem("statlyze_token");
    setToken(null);
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
        <button type="button" className="link-button" onClick={handleLogout}>
          Keluar
        </button>
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
