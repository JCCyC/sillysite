import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from auth import require_admin, require_user
from database import get_db

router = APIRouter()

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
    "Leave me alone, I know what I'm doing.",
]


@router.get("/about")
def read_about():
    return {"msg": random.choice(ABOUT_MESSAGES)}


# --- Season ---


@router.get(
    "/season/{year:int}",
    response_model=list[schemas.SeasonGrandPrix],
    dependencies=[Depends(require_user)],
)
def get_season(year: int, db: Session = Depends(get_db)):
    gps = (
        db.query(models.GrandPrix)
        .options(
            joinedload(models.GrandPrix.winning_driver),
            joinedload(models.GrandPrix.winning_team),
        )
        .filter(models.GrandPrix.season == year)
        .order_by(models.GrandPrix.sequence_number)
        .all()
    )
    if not gps:
        raise HTTPException(status_code=404, detail="Season not found")
    return [
        schemas.SeasonGrandPrix(
            sequence_number=gp.sequence_number,
            name=gp.name,
            track_name=gp.track_name,
            winning_driver=gp.winning_driver.name if gp.winning_driver else None,
            winning_team=gp.winning_team.name if gp.winning_team else None,
        )
        for gp in gps
    ]


# --- Teams ---


@router.get(
    "/teams",
    response_model=list[schemas.Team],
    dependencies=[Depends(require_user)],
)
def list_teams(db: Session = Depends(get_db)):
    return db.query(models.Team).all()


@router.get(
    "/teams/winners",
    response_model=list[schemas.WinnerCount],
    dependencies=[Depends(require_user)],
)
def get_team_winners(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Team.id,
            models.Team.name,
            func.count(models.GrandPrix.winning_team_id).label("wins"),
        )
        .join(models.GrandPrix, models.GrandPrix.winning_team_id == models.Team.id)
        .group_by(models.Team.id, models.Team.name)
        .order_by(func.count(models.GrandPrix.winning_team_id).desc(), models.Team.name)
        .all()
    )
    return [schemas.WinnerCount(id=row.id, name=row.name, wins=row.wins) for row in rows]


@router.get(
    "/teams/{team_id:int}",
    response_model=schemas.Team,
    dependencies=[Depends(require_user)],
)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(models.Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post(
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


@router.put(
    "/teams/{team_id:int}",
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


@router.delete(
    "/teams/{team_id:int}",
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


@router.get(
    "/drivers",
    response_model=list[schemas.Driver],
    dependencies=[Depends(require_user)],
)
def list_drivers(db: Session = Depends(get_db)):
    return db.query(models.Driver).all()


@router.get(
    "/drivers/winners",
    response_model=list[schemas.WinnerCount],
    dependencies=[Depends(require_user)],
)
def get_driver_winners(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Driver.id,
            models.Driver.name,
            func.count(models.GrandPrix.winning_driver_id).label("wins"),
        )
        .join(models.GrandPrix, models.GrandPrix.winning_driver_id == models.Driver.id)
        .group_by(models.Driver.id, models.Driver.name)
        .order_by(func.count(models.GrandPrix.winning_driver_id).desc(), models.Driver.name)
        .all()
    )
    return [schemas.WinnerCount(id=row.id, name=row.name, wins=row.wins) for row in rows]


@router.get(
    "/drivers/{driver_id:int}",
    response_model=schemas.Driver,
    dependencies=[Depends(require_user)],
)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.get(models.Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post(
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


@router.put(
    "/drivers/{driver_id:int}",
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


@router.delete(
    "/drivers/{driver_id:int}",
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


@router.get(
    "/driver-numbers",
    response_model=list[schemas.DriverNumber],
    dependencies=[Depends(require_user)],
)
def list_driver_numbers(db: Session = Depends(get_db)):
    return db.query(models.DriverNumber).all()


@router.get(
    "/driver-numbers/{driver_id:int}/{season:int}",
    response_model=schemas.DriverNumber,
    dependencies=[Depends(require_user)],
)
def get_driver_number(driver_id: int, season: int, db: Session = Depends(get_db)):
    driver_number = db.get(models.DriverNumber, (driver_id, season))
    if driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    return driver_number


@router.post(
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


@router.put(
    "/driver-numbers/{driver_id:int}/{season:int}",
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


@router.delete(
    "/driver-numbers/{driver_id:int}/{season:int}",
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


@router.get(
    "/grands-prix",
    response_model=list[schemas.GrandPrix],
    dependencies=[Depends(require_user)],
)
def list_grands_prix(db: Session = Depends(get_db)):
    return db.query(models.GrandPrix).all()


@router.get(
    "/grands-prix/{season:int}/{sequence_number:int}",
    response_model=schemas.GrandPrix,
    dependencies=[Depends(require_user)],
)
def get_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    gp = db.get(models.GrandPrix, (season, sequence_number))
    if gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    return gp


@router.post(
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


@router.put(
    "/grands-prix/{season:int}/{sequence_number:int}",
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


@router.delete(
    "/grands-prix/{season:int}/{sequence_number:int}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    db_gp = db.get(models.GrandPrix, (season, sequence_number))
    if db_gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    db.delete(db_gp)
    db.commit()
