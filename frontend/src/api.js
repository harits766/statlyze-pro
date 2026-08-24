// Semua fungsi di sini cuma pembungkus fetch() ke backend FastAPI.
// Nggak ada logic bisnis di sini -- itu semua udah ada di backend.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = "Terjadi kesalahan";
    try {
      const data = await res.json();
      if (Array.isArray(data.detail)) {
        // Error validasi dari FastAPI/Pydantic (status 422) bentuknya beda:
        // list of {msg, loc, type}, bukan string biasa kayak error lainnya.
        detail = data.detail
          .map((e) => (e.msg || "").replace(/^Value error,\s*/, ""))
          .filter(Boolean)
          .join(", ") || detail;
      } else if (data.detail) {
        detail = data.detail;
      }
    } catch {
      // response bukan JSON, biarin pesan default
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function registerUser(email, password) {
  const res = await fetch(`${API_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function loginUser(email, password) {
  // endpoint /login pakai format form (bukan JSON), field "username" diisi email
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  return handleResponse(res); // { access_token, token_type }
}

export async function uploadDataset(token, file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/datasets/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  return handleResponse(res);
}

export async function analyzeDataset(token, datasetId) {
  const res = await fetch(`${API_URL}/datasets/${datasetId}/analyze`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function listDatasets(token) {
  const res = await fetch(`${API_URL}/datasets`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function getInsights(token, datasetId) {
  const res = await fetch(`${API_URL}/datasets/${datasetId}/insights`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}
