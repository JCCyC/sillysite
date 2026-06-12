from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    founded_year = Column(Integer, nullable=False)


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)

    numbers = relationship("DriverNumber", back_populates="driver")


class DriverNumber(Base):
    __tablename__ = "driver_numbers"
    __table_args__ = (UniqueConstraint("season", "number"),)

    driver_id = Column(Integer, ForeignKey("drivers.id"), primary_key=True)
    season = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)

    driver = relationship("Driver", back_populates="numbers")


class GrandPrix(Base):
    __tablename__ = "grands_prix"

    season = Column(Integer, primary_key=True)
    sequence_number = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    track_name = Column(String, nullable=False)
    winning_driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    winning_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    winning_driver = relationship("Driver")
    winning_team = relationship("Team")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    password_iterations = Column(Integer, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    challenge = Column(String, unique=True, nullable=False, index=True)
    token = Column(String, unique=True, nullable=True, index=True)
    source_ip = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)

    user = relationship("User")


class AppConfig(Base):
    __tablename__ = "app_config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
