import { useState } from "react";
import { loginUser, registerUser } from "../api";

// Aturannya disamain persis sama backend (backend/app/schemas.py). Dicek di
// sini cuma biar user dapat respons instan tanpa nunggu request -- backend
// tetap jadi penentu akhir, jadi kalau ada yang lolos dari sini pun tetap
// ditolak di server.
const USERNAME_MIN = 3;
const USERNAME_MAX = 20;
const PASSWORD_MIN = 8;
const USERNAME_PATTERN = /^[a-z][a-z0-9_]*$/;

function validateRegister({ username, email, password, confirmPassword }) {
  if (!username || !email || !password) {
    return "Username, email, dan password wajib diisi.";
  }
  if (username.length < USERNAME_MIN) {
    return `Username minimal ${USERNAME_MIN} karakter.`;
  }
  if (username.length > USERNAME_MAX) {
    return `Username maksimal ${USERNAME_MAX} karakter.`;
  }
  if (!USERNAME_PATTERN.test(username)) {
    return "Username harus diawali huruf dan cuma boleh berisi huruf, angka, atau underscore (_).";
  }
  if (password.length < PASSWORD_MIN) {
    return `Password minimal ${PASSWORD_MIN} karakter.`;
  }
  if (password !== confirmPassword) {
    return "Konfirmasi password nggak cocok.";
  }
  return "";
}

export default function Login({ onLogin }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  // Di mode masuk, field ini boleh diisi email ATAU username.
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (isRegisterMode) {
      const message = validateRegister({ username, email, password, confirmPassword });
      if (message) {
        setError(message);
        return;
      }
    } else if (!identifier || !password) {
      setError("Email/username dan password wajib diisi.");
      return;
    }

    setLoading(true);
    try {
      if (isRegisterMode) {
        await registerUser(username, email, password);
        // Habis daftar langsung dilogin-in pakai email yang barusan didaftarin,
        // biar user nggak perlu ngisi form dua kali.
        const { access_token } = await loginUser(email, password);
        onLogin(access_token);
      } else {
        const { access_token } = await loginUser(identifier, password);
        onLogin(access_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setIsRegisterMode(!isRegisterMode);
    setError("");
    setPassword("");
    setConfirmPassword("");
  }

  return (
    <div className="auth-card">
      <h1>{isRegisterMode ? "Daftar akun statlyze" : "Masuk ke statlyze"}</h1>
      <form onSubmit={handleSubmit}>
        {isRegisterMode ? (
          <>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              placeholder="budi_analis"
              value={username}
              // Backend nyimpen username huruf kecil semua, jadi input-nya
              // langsung dikecilin biar yang dilihat user sama persis sama
              // yang bakal kesimpan.
              onChange={(e) => setUsername(e.target.value.trim().toLowerCase())}
            />
            <p className="field-hint">
              {USERNAME_MIN}-{USERNAME_MAX} karakter, diawali huruf. Boleh huruf, angka, dan
              underscore. Harus unik.
            </p>

            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="nama@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="minimal 8 karakter"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <label htmlFor="confirm-password">Ulangi password</label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              placeholder="********"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </>
        ) : (
          <>
            <label htmlFor="identifier">Email atau username</label>
            <input
              id="identifier"
              type="text"
              autoComplete="username"
              placeholder="nama@email.com atau budi_analis"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="********"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </>
        )}

        {error && <p className="error-text">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Memproses..." : isRegisterMode ? "Daftar" : "Masuk"}
        </button>
      </form>

      <p className="switch-mode">
        {isRegisterMode ? "Sudah punya akun?" : "Belum punya akun?"}{" "}
        <button type="button" className="link-button" onClick={switchMode}>
          {isRegisterMode ? "Masuk" : "Daftar"}
        </button>
      </p>
    </div>
  );
}
