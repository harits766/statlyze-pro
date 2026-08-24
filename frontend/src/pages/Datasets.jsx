import { useEffect, useState } from "react";
import { analyzeDataset, listDatasets, uploadDataset } from "../api";

const STATUS_LABEL = {
  uploaded: "terupload",
  processing: "diproses",
  done: "selesai",
  failed: "gagal",
};

export default function Datasets({ token, onSelectDataset }) {
  const [datasets, setDatasets] = useState([]);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [analyzingId, setAnalyzingId] = useState(null);

  async function refresh() {
    try {
      const data = await listDatasets(token);
      setDatasets(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;

    setError("");
    setUploading(true);
    try {
      await uploadDataset(token, file);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = ""; // biar bisa upload file yang sama lagi kalau perlu
    }
  }

  async function handleAnalyze(datasetId) {
    setError("");
    setAnalyzingId(datasetId);
    try {
      await analyzeDataset(token, datasetId);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzingId(null);
    }
  }

  return (
    <div>
      <h2>Dataset saya</h2>

      <label className="upload-zone">
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
          disabled={uploading}
          hidden
        />
        <span>
          {uploading ? "Mengupload..." : "Klik untuk pilih file CSV atau Excel"}
        </span>
      </label>

      {error && <p className="error-text">{error}</p>}

      {datasets.length === 0 ? (
        <p className="empty-text">Belum ada dataset yang diupload.</p>
      ) : (
        <ul className="dataset-list">
          {datasets.map((ds) => (
            <li key={ds.id} className="dataset-row">
              <button
                type="button"
                className="dataset-name"
                onClick={() => onSelectDataset(ds.id)}
                disabled={ds.status !== "done"}
                title={ds.status !== "done" ? "Analisis dulu buat lihat insight" : "Lihat insight"}
              >
                {ds.filename}
              </button>
              <span className={`status-badge status-${ds.status}`}>
                {STATUS_LABEL[ds.status] || ds.status}
              </span>
              {(ds.status === "uploaded" || ds.status === "failed") && (
                <button
                  type="button"
                  className="analyze-button"
                  onClick={() => handleAnalyze(ds.id)}
                  disabled={analyzingId === ds.id}
                >
                  {analyzingId === ds.id ? "Menganalisis..." : "Analisis"}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
