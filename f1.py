import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
]


@router.get("/about")
def read_about():
    return {"msg": random.choice(ABOUT_MESSAGES)}


# --- Teams ---


@router.get(
    "/teams",
    response_model=list[schemas.Team],
    dependencies=[Depends(require_user)],
)
def list_teams(db: Session = Depends(get_db)):
    return db.query(models.Team).all()


@router.get(
    "/teams/{team_id}",
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


@router.delete(
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


@router.get(
    "/drivers",
    response_model=list[schemas.Driver],
    dependencies=[Depends(require_user)],
)
def list_drivers(db: Session = Depends(get_db)):
    return db.query(models.Driver).all()


@router.get(
    "/drivers/{driver_id}",
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


@router.delete(
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


@router.get(
    "/driver-numbers",
    response_model=list[schemas.DriverNumber],
    dependencies=[Depends(require_user)],
)
def list_driver_numbers(db: Session = Depends(get_db)):
    return db.query(models.DriverNumber).all()


@router.get(
    "/driver-numbers/{driver_id}/{season}",
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


@router.delete(
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


@router.get(
    "/grands-prix",
    response_model=list[schemas.GrandPrix],
    dependencies=[Depends(require_user)],
)
def list_grands_prix(db: Session = Depends(get_db)):
    return db.query(models.GrandPrix).all()


@router.get(
    "/grands-prix/{season}/{sequence_number}",
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


@router.delete(
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
