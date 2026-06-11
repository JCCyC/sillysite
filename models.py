from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    founded_year = Column(Integer, nullable=False)

    drivers = relationship("Driver", back_populates="team")


class Driver(Base):
    __tablename__ = "drivers"

    car_number = Column(Integer, primary_key=True)
    country = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String, nullable=False)

    team = relationship("Team", back_populates="drivers")


class GrandPrix(Base):
    __tablename__ = "grands_prix"

    season = Column(Integer, primary_key=True)
    sequence_number = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    track_name = Column(String, nullable=False)
    winning_driver_car_number = Column(
        Integer, ForeignKey("drivers.car_number"), nullable=True
    )

    winning_driver = relationship("Driver")
