import { useState } from "react";
import { loginUser, registerUser } from "../api";

export default function Login({ onLogin }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Email dan password wajib diisi.");
      return;
    }

    setLoading(true);
    try {
      if (isRegisterMode) {
        await registerUser(email, password);
      }
      const { access_token } = await loginUser(email, password);
      onLogin(access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>{isRegisterMode ? "Daftar akun statlyze" : "Masuk ke statlyze"}</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          placeholder="nama@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="********"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="error-text">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Memproses..." : isRegisterMode ? "Daftar" : "Masuk"}
        </button>
      </form>

      <p className="switch-mode">
        {isRegisterMode ? "Sudah punya akun?" : "Belum punya akun?"}{" "}
        <button
          type="button"
          className="link-button"
          onClick={() => {
            setIsRegisterMode(!isRegisterMode);
            setError("");
          }}
        >
          {isRegisterMode ? "Masuk" : "Daftar"}
        </button>
      </p>
    </div>
  );
}
