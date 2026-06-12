from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    country: str
    founded_year: int


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    founded_year: int | None = None


class Team(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DriverBase(BaseModel):
    name: str
    nationality: str
    date_of_birth: date


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: str | None = None
    nationality: str | None = None
    date_of_birth: date | None = None


class Driver(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DriverNumberBase(BaseModel):
    driver_id: int
    season: int
    number: int


class DriverNumberCreate(DriverNumberBase):
    pass


class DriverNumberUpdate(BaseModel):
    driver_id: int | None = None
    season: int | None = None
    number: int | None = None


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


class GrandPrixUpdate(BaseModel):
    season: int | None = None
    sequence_number: int | None = None
    name: str | None = None
    track_name: str | None = None
    winning_driver_id: int | None = None
    winning_team_id: int | None = None


class GrandPrix(GrandPrixBase):
    model_config = ConfigDict(from_attributes=True)


class AppConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str


class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_admin: bool | None = None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    is_admin: bool
    created_at: datetime


class LoginChallengeRequest(BaseModel):
    username: str


class LoginChallengeResponse(BaseModel):
    challenge: str
    salt: str
    iterations: int


class LoginResponseRequest(BaseModel):
    username: str
    challenge: str
    response: str


class LoginResponseResponse(BaseModel):
    token: str
    expires_at: datetime


class ChangePasswordRequest(BaseModel):
    new_salt: str
    new_password_hash: str
    new_iterations: int
