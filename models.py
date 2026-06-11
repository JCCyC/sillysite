from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
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
