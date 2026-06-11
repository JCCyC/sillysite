from datetime import date

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    country: str
    founded_year: int


class TeamCreate(TeamBase):
    pass


class Team(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DriverBase(BaseModel):
    name: str
    nationality: str
    date_of_birth: date


class DriverCreate(DriverBase):
    pass


class Driver(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DriverNumberBase(BaseModel):
    driver_id: int
    season: int
    number: int


class DriverNumberCreate(DriverNumberBase):
    pass


class DriverNumber(DriverNumberBase):
    model_config = ConfigDict(from_attributes=True)


class GrandPrixBase(BaseModel):
    season: int
    sequence_number: int
    name: str
    track_name: str
    winning_driver_id: int | None = None
    winning_team_id: int | None = None


class GrandPrixCreate(GrandPrixBase):
    pass


class GrandPrix(GrandPrixBase):
    model_config = ConfigDict(from_attributes=True)
