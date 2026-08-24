import { useEffect, useState } from "react";
import { getInsights } from "../api";

export default function Insights({ token, datasetId, onBack }) {
  const [insights, setInsights] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getInsights(token, datasetId)
      .then((data) => {
        if (!cancelled) setInsights(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  return (
    <div>
      <button type="button" className="back-button" onClick={onBack}>
        &larr; Kembali ke dataset
      </button>
      <h2>Insight</h2>
      <p className="muted-text">Diurutkan dari yang paling signifikan</p>

      {loading && <p className="empty-text">Memuat insight...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && insights.length === 0 && (
        <p className="empty-text">
          Belum ada insight signifikan yang terdeteksi dari dataset ini.
        </p>
      )}

      <ul className="insight-list">
        {insights.map((ins) => (
          <li key={ins.id} className="insight-card">
            <span className={`category-badge category-${ins.category}`}>
              {ins.category.replace("_", " ")}
            </span>
            <p>{ins.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
