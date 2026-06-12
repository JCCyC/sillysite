import random
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

SESSION_CLEANUP_INTERVAL_SECONDS = 15 * 60
SESSION_CLEANUP_GRACE_SECONDS = 60 * 60


def _cleanup_expired_sessions():
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=SESSION_CLEANUP_GRACE_SECONDS)
        db.query(models.UserSession).filter(models.UserSession.expires_at < cutoff).delete()
        db.commit()
    finally:
        db.close()


def _session_cleanup_loop():
    while True:
        _cleanup_expired_sessions()
        time.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)


threading.Thread(target=_session_cleanup_loop, daemon=True).start()

ABOUT_MESSAGES = [
    "This site is powered by FastAPI and Formula One.",
    "We're a small but mighty pit crew of a project.",
    "About page, fueled by high-octane data.",
    "Built for fun, deployed at race pace.",
    "Tracking grids, grands prix, and glory since lap one.",
    "Every endpoint is a victory lap.",
    "No blue flags here, just smooth racing.",
    "Powered by a hybrid of FastAPI and PostgreSQL.",
    "Strategy: undercut the competition.",
    "From pole position to the chequered flag.",
    "Lights out and away we go!",
    "Welcome to the pit lane.",
    "Box, box, box.",
    "DRS enabled.",
    "It's hammer time.",
    "Gap to the car ahead: closing.",
    "Push push push!",
    "Undercut secured.",
    "Purple sector one.",
    "Checkered flag incoming.",
]


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


@app.get("/about")
def read_about():
    return {"msg": random.choice(ABOUT_MESSAGES)}


# --- Teams ---


@app.get(
    "/teams",
    response_model=list[schemas.Team],
    dependencies=[Depends(require_user)],
)
def list_teams(db: Session = Depends(get_db)):
    return db.query(models.Team).all()


@app.get(
    "/teams/{team_id}",
    response_model=schemas.Team,
    dependencies=[Depends(require_user)],
)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(models.Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.post(
    "/teams",
    response_model=schemas.Team,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@app.put(
    "/teams/{team_id}",
    response_model=schemas.Team,
    dependencies=[Depends(require_admin)],
)
def update_team(team_id: int, team: schemas.TeamUpdate, db: Session = Depends(get_db)):
    db_team = db.get(models.Team, team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    for field, value in team.model_dump(exclude_unset=True).items():
        setattr(db_team, field, value)
    db.commit()
    db.refresh(db_team)
    return db_team


@app.delete(
    "/teams/{team_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    db_team = db.get(models.Team, team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(db_team)
    db.commit()


# --- Drivers ---


@app.get(
    "/drivers",
    response_model=list[schemas.Driver],
    dependencies=[Depends(require_user)],
)
def list_drivers(db: Session = Depends(get_db)):
    return db.query(models.Driver).all()


@app.get(
    "/drivers/{driver_id}",
    response_model=schemas.Driver,
    dependencies=[Depends(require_user)],
)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.get(models.Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@app.post(
    "/drivers",
    response_model=schemas.Driver,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    db_driver = models.Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.put(
    "/drivers/{driver_id}",
    response_model=schemas.Driver,
    dependencies=[Depends(require_admin)],
)
def update_driver(
    driver_id: int, driver: schemas.DriverUpdate, db: Session = Depends(get_db)
):
    db_driver = db.get(models.Driver, driver_id)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in driver.model_dump(exclude_unset=True).items():
        setattr(db_driver, field, value)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.delete(
    "/drivers/{driver_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.get(models.Driver, driver_id)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(db_driver)
    db.commit()


# --- Driver Numbers ---


@app.get(
    "/driver-numbers",
    response_model=list[schemas.DriverNumber],
    dependencies=[Depends(require_user)],
)
def list_driver_numbers(db: Session = Depends(get_db)):
    return db.query(models.DriverNumber).all()


@app.get(
    "/driver-numbers/{driver_id}/{season}",
    response_model=schemas.DriverNumber,
    dependencies=[Depends(require_user)],
)
def get_driver_number(driver_id: int, season: int, db: Session = Depends(get_db)):
    driver_number = db.get(models.DriverNumber, (driver_id, season))
    if driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    return driver_number


@app.post(
    "/driver-numbers",
    response_model=schemas.DriverNumber,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_driver_number(
    driver_number: schemas.DriverNumberCreate, db: Session = Depends(get_db)
):
    db_driver_number = models.DriverNumber(**driver_number.model_dump())
    db.add(db_driver_number)
    db.commit()
    db.refresh(db_driver_number)
    return db_driver_number


@app.put(
    "/driver-numbers/{driver_id}/{season}",
    response_model=schemas.DriverNumber,
    dependencies=[Depends(require_admin)],
)
def update_driver_number(
    driver_id: int,
    season: int,
    driver_number: schemas.DriverNumberUpdate,
    db: Session = Depends(get_db),
):
    db_driver_number = db.get(models.DriverNumber, (driver_id, season))
    if db_driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    for field, value in driver_number.model_dump(exclude_unset=True).items():
        setattr(db_driver_number, field, value)
    db.commit()
    db.refresh(db_driver_number)
    return db_driver_number


@app.delete(
    "/driver-numbers/{driver_id}/{season}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_driver_number(driver_id: int, season: int, db: Session = Depends(get_db)):
    db_driver_number = db.get(models.DriverNumber, (driver_id, season))
    if db_driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    db.delete(db_driver_number)
    db.commit()


# --- Grands Prix ---


@app.get(
    "/grands-prix",
    response_model=list[schemas.GrandPrix],
    dependencies=[Depends(require_user)],
)
def list_grands_prix(db: Session = Depends(get_db)):
    return db.query(models.GrandPrix).all()


@app.get(
    "/grands-prix/{season}/{sequence_number}",
    response_model=schemas.GrandPrix,
    dependencies=[Depends(require_user)],
)
def get_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    gp = db.get(models.GrandPrix, (season, sequence_number))
    if gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    return gp


@app.post(
    "/grands-prix",
    response_model=schemas.GrandPrix,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_grand_prix(gp: schemas.GrandPrixCreate, db: Session = Depends(get_db)):
    db_gp = models.GrandPrix(**gp.model_dump())
    db.add(db_gp)
    db.commit()
    db.refresh(db_gp)
    return db_gp


@app.put(
    "/grands-prix/{season}/{sequence_number}",
    response_model=schemas.GrandPrix,
    dependencies=[Depends(require_admin)],
)
def update_grand_prix(
    season: int,
    sequence_number: int,
    gp: schemas.GrandPrixUpdate,
    db: Session = Depends(get_db),
):
    db_gp = db.get(models.GrandPrix, (season, sequence_number))
    if db_gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    for field, value in gp.model_dump(exclude_unset=True).items():
        setattr(db_gp, field, value)
    db.commit()
    db.refresh(db_gp)
    return db_gp


@app.delete(
    "/grands-prix/{season}/{sequence_number}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    db_gp = db.get(models.GrandPrix, (season, sequence_number))
    if db_gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    db.delete(db_gp)
    db.commit()


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

    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    return {"msg": f"User {user.username} logged out"}


# --- Config ---


@app.get(
    "/config",
    response_model=list[schemas.AppConfig],
    dependencies=[Depends(require_admin)],
)
def list_config(db: Session = Depends(get_db)):
    return db.query(models.AppConfig).all()


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
