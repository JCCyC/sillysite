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
    car_number: int
    country: str
    team_id: int
    name: str


class DriverCreate(DriverBase):
    pass


class Driver(DriverBase):
    model_config = ConfigDict(from_attributes=True)


class GrandPrixBase(BaseModel):
    season: int
    sequence_number: int
    name: str
    track_name: str
    winning_driver_car_number: int | None = None


class GrandPrixCreate(GrandPrixBase):
    pass


class GrandPrix(GrandPrixBase):
    model_config = ConfigDict(from_attributes=True)
