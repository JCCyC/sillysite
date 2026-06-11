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


@app.get("/drivers/{car_number}", response_model=schemas.Driver)
def get_driver(car_number: int, db: Session = Depends(get_db)):
    driver = db.get(models.Driver, car_number)
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


@app.put("/drivers/{car_number}", response_model=schemas.Driver)
def update_driver(
    car_number: int, driver: schemas.DriverCreate, db: Session = Depends(get_db)
):
    db_driver = db.get(models.Driver, car_number)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in driver.model_dump().items():
        setattr(db_driver, field, value)
    db.commit()
    db.refresh(db_driver)
    return db_driver


@app.delete("/drivers/{car_number}", status_code=204)
def delete_driver(car_number: int, db: Session = Depends(get_db)):
    db_driver = db.get(models.Driver, car_number)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(db_driver)
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
