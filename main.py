import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import f1
import models
import schemas
from auth import require_admin, require_user
from database import SessionLocal, engine, get_db

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


DEFAULT_CONFIG = {
    "session_ttl_seconds": auth.DEFAULT_SESSION_TTL_SECONDS,
    "login_timeout_seconds": auth.DEFAULT_LOGIN_TIMEOUT_SECONDS,
    "change_pw_timeout_seconds": auth.DEFAULT_CHANGE_PW_TIMEOUT_SECONDS,
    "session_cleanup_interval_seconds": auth.DEFAULT_SESSION_CLEANUP_INTERVAL_SECONDS,
    "session_cleanup_grace_seconds": auth.DEFAULT_SESSION_CLEANUP_GRACE_SECONDS,
}


def _ensure_default_config():
    db = SessionLocal()
    try:
        for key, default_value in DEFAULT_CONFIG.items():
            if db.get(models.AppConfig, key) is None:
                db.add(models.AppConfig(key=key, value=str(default_value)))
        db.commit()
    finally:
        db.close()


def _get_config_int(db: Session, key: str) -> int:
    config_row = db.get(models.AppConfig, key)
    return int(config_row.value) if config_row else DEFAULT_CONFIG[key]


def _ensure_admin_user():
    with engine.connect() as conn:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE")
        )
        conn.execute(
            text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS authenticated_at TIMESTAMPTZ")
        )
        conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR NOT NULL DEFAULT ''")
        )
        conn.commit()

    db = SessionLocal()
    try:
        admin = db.get(models.User, auth.ADMIN_USER_ID)
        if admin is None:
            salt, password_hash, iterations = auth.hash_password(secrets.token_hex(32))
            admin = models.User(
                id=auth.ADMIN_USER_ID,
                username=auth.ADMIN_USERNAME,
                full_name=auth.ADMIN_FULL_NAME,
                password_salt=salt,
                password_hash=password_hash,
                password_iterations=iterations,
                is_admin=True,
            )
            db.add(admin)
        else:
            admin.full_name = auth.ADMIN_FULL_NAME
        db.commit()
    finally:
        db.close()


_ensure_default_config()
_ensure_admin_user()

def _cleanup_expired_sessions():
    db = SessionLocal()
    try:
        grace_seconds = _get_config_int(db, "session_cleanup_grace_seconds")
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)
        db.query(models.UserSession).filter(models.UserSession.expires_at < cutoff).delete()
        db.commit()
    finally:
        db.close()


def _session_cleanup_loop():
    while True:
        _cleanup_expired_sessions()
        db = SessionLocal()
        try:
            interval_seconds = _get_config_int(db, "session_cleanup_interval_seconds")
        finally:
            db.close()
        time.sleep(interval_seconds)


threading.Thread(target=_session_cleanup_loop, daemon=True).start()

app.include_router(f1.router)


@app.get("/", include_in_schema=False)
def read_root(api_key: str | None = Depends(auth.resolve_api_key)):
    if api_key is not None:
        return RedirectResponse(f"/login.html?apikey={quote(api_key)}")
    return RedirectResponse("/login.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/login.html", include_in_schema=False)
def login_html(
    user: models.User | None = Depends(auth.get_current_user),
    api_key: str | None = Depends(auth.resolve_api_key),
):
    if user is not None:
        return RedirectResponse(f"/whoami.html?apikey={quote(api_key)}")
    return FileResponse("static/login.html")


@app.get("/whoami.html", include_in_schema=False)
def whoami_html(user: models.User | None = Depends(auth.get_current_user)):
    if user is None:
        return RedirectResponse("/login.html")
    return FileResponse("static/whoami.html")


@app.get("/changepw.html", include_in_schema=False)
def changepw_html(user: models.User | None = Depends(auth.get_current_user)):
    if user is None:
        return RedirectResponse("/login.html")
    return FileResponse("static/changepw.html")


# --- Users ---


@app.get(
    "/users",
    response_model=list[schemas.User],
    dependencies=[Depends(require_admin)],
)
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.post(
    "/users",
    response_model=schemas.User,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    salt, password_hash, iterations = auth.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        full_name=user.full_name,
        password_salt=salt,
        password_hash=password_hash,
        password_iterations=iterations,
        is_admin=user.is_admin,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put(
    "/users/{username}",
    response_model=schemas.User,
    dependencies=[Depends(require_admin)],
)
def update_user(username: str, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    fields = user.model_dump(exclude_unset=True)
    if "password" in fields:
        password = fields.pop("password")
        salt, password_hash, iterations = auth.hash_password(password)
        db_user.password_salt = salt
        db_user.password_hash = password_hash
        db_user.password_iterations = iterations
    if db_user.id == auth.ADMIN_USER_ID and fields.get("is_admin") is False:
        raise HTTPException(status_code=400, detail="Cannot remove admin privileges from the admin user")
    for field, value in fields.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete(
    "/users/{username}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.id == auth.ADMIN_USER_ID:
        raise HTTPException(status_code=400, detail="Cannot delete the admin user")
    db.delete(db_user)
    db.commit()


# --- Whoami ---


def _whoami(user: models.User, session: models.UserSession | None) -> schemas.WhoAmI:
    return schemas.WhoAmI(
        **schemas.User.model_validate(user).model_dump(),
        login_at=session.authenticated_at if session is not None else None,
        session_expires_at=session.expires_at if session is not None else None,
    )


@app.get("/whoami", response_model=schemas.WhoAmI)
def whoami(
    user: models.User = Depends(require_user),
    session: models.UserSession | None = Depends(auth.get_current_session),
):
    return _whoami(user, session)


# --- Logout ---


@app.get("/logout")
def logout(
    user: models.User = Depends(require_user),
    session: models.UserSession | None = Depends(auth.get_current_session),
    db: Session = Depends(get_db),
):
    if session is None:
        raise HTTPException(status_code=400, detail="Cannot log out the static API key")

    session.expires_at = datetime.now(timezone.utc) - timedelta(milliseconds=1)
    db.commit()
    return {"msg": f"User {user.username} logged out"}


# --- Config ---


@app.get(
    "/config",
    response_model=dict[str, str],
    dependencies=[Depends(require_admin)],
)
def list_config(db: Session = Depends(get_db)):
    return {row.key: row.value for row in db.query(models.AppConfig).all()}


# --- Active Users ---


@app.get(
    "/activeusers",
    response_model=list[schemas.ActiveUser],
    dependencies=[Depends(require_admin)],
)
def list_active_users(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(models.UserSession)
        .filter(models.UserSession.token.isnot(None), models.UserSession.expires_at > now)
        .all()
    )
    return [
        schemas.ActiveUser(
            username=session.user.username,
            source_ip=session.source_ip,
            login_at=session.authenticated_at,
            expires_at=session.expires_at,
        )
        for session in sessions
    ]


# --- Login ---


@app.post("/login/challenge", response_model=schemas.LoginChallengeResponse)
def login_challenge(
    body: schemas.LoginChallengeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == body.username).first()

    if user is not None:
        salt, iterations = user.password_salt, user.password_iterations
    else:
        # Keep the response shape consistent for unknown usernames.
        salt = secrets.token_hex(auth.SALT_BYTES)
        iterations = auth.PBKDF2_ITERATIONS

    now = datetime.now(timezone.utc)
    login_timeout_seconds = _get_config_int(db, "login_timeout_seconds")
    session = models.UserSession(
        user_id=user.id if user is not None else None,
        challenge=auth.generate_challenge(),
        source_ip=auth.client_ip(request),
        created_at=now,
        expires_at=now + timedelta(seconds=login_timeout_seconds),
    )
    db.add(session)
    db.commit()

    return schemas.LoginChallengeResponse(
        challenge=session.challenge, salt=salt, iterations=iterations
    )


@app.post("/login/response", response_model=schemas.LoginResponseResponse)
def login_response(
    body: schemas.LoginResponseRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    session = (
        db.query(models.UserSession)
        .filter(models.UserSession.challenge == body.challenge, models.UserSession.used == False)
        .first()
    )

    invalid = HTTPException(status_code=403, detail="Invalid username or password")

    if session is None:
        raise invalid

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        session.used = True
        db.commit()
        raise HTTPException(status_code=403, detail="Login timeout")

    session.used = True

    user = session.user
    if user is None or user.username != body.username:
        db.commit()
        raise invalid

    expected = auth.compute_challenge_response(user.password_hash, body.challenge)
    if not secrets.compare_digest(expected, body.response):
        db.commit()
        raise invalid

    ttl_seconds = _get_config_int(db, "session_ttl_seconds")

    session.token = auth.generate_token()
    session.source_ip = auth.client_ip(request)
    session.expires_at = now + timedelta(seconds=ttl_seconds)
    session.authenticated_at = now
    db.commit()

    return schemas.LoginResponseResponse(token=session.token, expires_at=session.expires_at)


# --- Change Password ---


@app.post(
    "/change-password",
    status_code=204,
)
def change_password(
    body: schemas.ChangePasswordRequest,
    user: models.User = Depends(require_user),
    session: models.UserSession | None = Depends(auth.get_current_session),
    db: Session = Depends(get_db),
):
    try:
        if session is not None:
            now = datetime.now(timezone.utc)
            authenticated_at = session.authenticated_at
            if authenticated_at is None:
                raise HTTPException(status_code=403, detail="Change password timeout")
            if authenticated_at.tzinfo is None:
                authenticated_at = authenticated_at.replace(tzinfo=timezone.utc)
            timeout_seconds = _get_config_int(db, "change_pw_timeout_seconds")
            if now - authenticated_at > timedelta(seconds=timeout_seconds):
                raise HTTPException(status_code=403, detail="Change password timeout")

        user.password_salt = body.new_salt
        user.password_hash = body.new_password_hash
        user.password_iterations = body.new_iterations
        db.commit()
    finally:
        if session is not None:
            session.expires_at = datetime.now(timezone.utc) - timedelta(milliseconds=1)
            db.commit()
