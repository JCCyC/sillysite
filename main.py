import random

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

HOME_MESSAGES = [
    "Welcome to the silly site!",
    "Hello, world!",
    "You found the home page.",
    "Glad you're here.",
]

ABOUT_MESSAGES = [
    "This site is powered by FastAPI.",
    "We're a small but mighty test project.",
    "About page, at your service.",
    "Built for fun, deployed for science.",
]


@app.get("/")
def read_root():
    return {"msg": random.choice(HOME_MESSAGES)}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/about")
def read_about():
    return {"msg": random.choice(ABOUT_MESSAGES)}


# --- Teams ---


@app.get("/teams", response_model=list[schemas.Team])
def list_teams(db: Session = Depends(get_db)):
    return db.query(models.Team).all()


@app.get("/teams/{team_id}", response_model=schemas.Team)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(models.Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.post("/teams", response_model=schemas.Team, status_code=201)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@app.put("/teams/{team_id}", response_model=schemas.Team)
def update_team(team_id: int, team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = db.get(models.Team, team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    for field, value in team.model_dump().items():
        setattr(db_team, field, value)
    db.commit()
    db.refresh(db_team)
    return db_team


@app.delete("/teams/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    db_team = db.get(models.Team, team_id)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(db_team)
    db.commit()


# --- Drivers ---


@app.get("/drivers", response_model=list[schemas.Driver])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(models.Driver).all()


@app.get("/drivers/{driver_id}", response_model=schemas.Driver)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.get(models.Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@app.post("/drivers", response_model=schemas.Driver, status_code=201)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    db_driver = models.Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.put("/drivers/{driver_id}", response_model=schemas.Driver)
def update_driver(
    driver_id: int, driver: schemas.DriverCreate, db: Session = Depends(get_db)
):
    db_driver = db.get(models.Driver, driver_id)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in driver.model_dump().items():
        setattr(db_driver, field, value)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.delete("/drivers/{driver_id}", status_code=204)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.get(models.Driver, driver_id)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(db_driver)
    db.commit()


# --- Driver Numbers ---


@app.get("/driver-numbers", response_model=list[schemas.DriverNumber])
def list_driver_numbers(db: Session = Depends(get_db)):
    return db.query(models.DriverNumber).all()


@app.get(
    "/driver-numbers/{driver_id}/{season}", response_model=schemas.DriverNumber
)
def get_driver_number(driver_id: int, season: int, db: Session = Depends(get_db)):
    driver_number = db.get(models.DriverNumber, (driver_id, season))
    if driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    return driver_number


@app.post("/driver-numbers", response_model=schemas.DriverNumber, status_code=201)
def create_driver_number(
    driver_number: schemas.DriverNumberCreate, db: Session = Depends(get_db)
):
    db_driver_number = models.DriverNumber(**driver_number.model_dump())
    db.add(db_driver_number)
    db.commit()
    db.refresh(db_driver_number)
    return db_driver_number


@app.put(
    "/driver-numbers/{driver_id}/{season}", response_model=schemas.DriverNumber
)
def update_driver_number(
    driver_id: int,
    season: int,
    driver_number: schemas.DriverNumberCreate,
    db: Session = Depends(get_db),
):
    db_driver_number = db.get(models.DriverNumber, (driver_id, season))
    if db_driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    for field, value in driver_number.model_dump().items():
        setattr(db_driver_number, field, value)
    db.commit()
    db.refresh(db_driver_number)
    return db_driver_number


@app.delete("/driver-numbers/{driver_id}/{season}", status_code=204)
def delete_driver_number(driver_id: int, season: int, db: Session = Depends(get_db)):
    db_driver_number = db.get(models.DriverNumber, (driver_id, season))
    if db_driver_number is None:
        raise HTTPException(status_code=404, detail="Driver number not found")
    db.delete(db_driver_number)
    db.commit()


# --- Grands Prix ---


@app.get("/grands-prix", response_model=list[schemas.GrandPrix])
def list_grands_prix(db: Session = Depends(get_db)):
    return db.query(models.GrandPrix).all()


@app.get("/grands-prix/{season}/{sequence_number}", response_model=schemas.GrandPrix)
def get_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    gp = db.get(models.GrandPrix, (season, sequence_number))
    if gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    return gp


@app.post("/grands-prix", response_model=schemas.GrandPrix, status_code=201)
def create_grand_prix(gp: schemas.GrandPrixCreate, db: Session = Depends(get_db)):
    db_gp = models.GrandPrix(**gp.model_dump())
    db.add(db_gp)
    db.commit()
    db.refresh(db_gp)
    return db_gp


@app.put("/grands-prix/{season}/{sequence_number}", response_model=schemas.GrandPrix)
def update_grand_prix(
    season: int,
    sequence_number: int,
    gp: schemas.GrandPrixCreate,
    db: Session = Depends(get_db),
):
    db_gp = db.get(models.GrandPrix, (season, sequence_number))
    if db_gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    for field, value in gp.model_dump().items():
        setattr(db_gp, field, value)
    db.commit()
    db.refresh(db_gp)
    return db_gp


@app.delete("/grands-prix/{season}/{sequence_number}", status_code=204)
def delete_grand_prix(season: int, sequence_number: int, db: Session = Depends(get_db)):
    db_gp = db.get(models.GrandPrix, (season, sequence_number))
    if db_gp is None:
        raise HTTPException(status_code=404, detail="Grand Prix not found")
    db.delete(db_gp)
    db.commit()
