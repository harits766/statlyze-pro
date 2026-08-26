"""Entry point FastAPI.

Load .env duluan sebelum modul lain (security.py) baca environment
variable-nya -- makanya load_dotenv() ada di paling atas, sebelum
import lain.
"""
import os  # noqa: E402

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.security import OAuth2PasswordRequestForm  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from .auth import get_current_user  # noqa: E402
from .database import Base, engine, get_db  # noqa: E402
from .datasets import router as datasets_router  # noqa: E402
from .limiter import limiter  # noqa: E402
from .models import User  # noqa: E402
from .schemas import Token, UserCreate, UserOut  # noqa: E402
from .security import create_access_token, hash_password, verify_password  # noqa: E402

Base.metadata.create_all(bind=engine)  # auto-bikin tabel kalau belum ada

app = FastAPI(title="Statlyze API")

# Rate limiting: batasin jumlah request per IP per menit, khususnya buat
# endpoint yang rawan disalahgunain (brute-force login, spam register).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: browser nge-block request lintas origin secara default. Frontend
# dan backend dianggap origin beda kalau alamatnya beda, jadi harus
# diizinin manual di sini.
#
# Default-nya alamat dev lokal (Vite). Pas deploy ke hosting, tambahin
# alamat production frontend-nya lewat environment variable ALLOWED_ORIGINS
# (dipisah koma) -- TIDAK PERLU ubah kode ini lagi. Contoh:
#   ALLOWED_ORIGINS=https://statlyze.up.railway.app,https://statlyze.com
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets_router)


@app.get("/")
def root():
    return {"message": "Statlyze API jalan. Buka /docs buat lihat semua endpoint."}


@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.email})
    return Token(access_token=token)


@app.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Contoh endpoint terproteksi -- cuma bisa diakses kalau bawa token valid."""
    return current_user
