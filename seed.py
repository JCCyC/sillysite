"""One-off script to seed the database with 2025 Formula One season data.

Run with: .venv/bin/python seed.py

Note: results for races after the British/Belgian GPs (roughly mid-2025
onward) are left without a winner, since they are outside the data this
was written from.
"""

from datetime import date

import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

TEAMS = [
    {"name": "Red Bull Racing", "country": "Austria", "founded_year": 2005},
    {"name": "Ferrari", "country": "Italy", "founded_year": 1950},
    {"name": "Mercedes", "country": "Germany", "founded_year": 2010},
    {"name": "McLaren", "country": "United Kingdom", "founded_year": 1966},
    {"name": "Aston Martin", "country": "United Kingdom", "founded_year": 2021},
    {"name": "Alpine", "country": "France", "founded_year": 2021},
    {"name": "Williams", "country": "United Kingdom", "founded_year": 1977},
    {"name": "Racing Bulls", "country": "Italy", "founded_year": 2024},
    {"name": "Haas", "country": "United States", "founded_year": 2016},
    {"name": "Kick Sauber", "country": "Switzerland", "founded_year": 1970},
]

# (car_number, nationality, name, date_of_birth, team_name)
DRIVERS = [
    (1, "Netherlands", "Max Verstappen", date(1997, 9, 30), "Red Bull Racing"),
    (22, "Japan", "Yuki Tsunoda", date(2000, 5, 11), "Red Bull Racing"),
    (16, "Monaco", "Charles Leclerc", date(1997, 10, 16), "Ferrari"),
    (44, "United Kingdom", "Lewis Hamilton", date(1985, 1, 7), "Ferrari"),
    (4, "United Kingdom", "Lando Norris", date(1999, 11, 13), "McLaren"),
    (81, "Australia", "Oscar Piastri", date(2001, 4, 6), "McLaren"),
    (63, "United Kingdom", "George Russell", date(1998, 2, 15), "Mercedes"),
    (12, "Italy", "Andrea Kimi Antonelli", date(2006, 8, 25), "Mercedes"),
    (14, "Spain", "Fernando Alonso", date(1981, 7, 29), "Aston Martin"),
    (18, "Canada", "Lance Stroll", date(1998, 10, 29), "Aston Martin"),
    (10, "France", "Pierre Gasly", date(1996, 2, 7), "Alpine"),
    (43, "Argentina", "Franco Colapinto", date(2003, 5, 27), "Alpine"),
    (23, "Thailand", "Alex Albon", date(1996, 3, 23), "Williams"),
    (55, "Spain", "Carlos Sainz", date(1994, 9, 1), "Williams"),
    (30, "New Zealand", "Liam Lawson", date(2002, 2, 11), "Racing Bulls"),
    (6, "France", "Isack Hadjar", date(2004, 9, 28), "Racing Bulls"),
    (31, "France", "Esteban Ocon", date(1996, 9, 17), "Haas"),
    (87, "United Kingdom", "Oliver Bearman", date(2005, 5, 8), "Haas"),
    (27, "Germany", "Nico Hulkenberg", date(1987, 8, 19), "Kick Sauber"),
    (5, "Brazil", "Gabriel Bortoleto", date(2004, 10, 14), "Kick Sauber"),
]

# (sequence_number, name, track_name, winning_driver_name, winning_team_name)
GRANDS_PRIX_2025 = [
    (1, "Australian Grand Prix", "Albert Park Circuit", "Lando Norris", "McLaren"),
    (2, "Chinese Grand Prix", "Shanghai International Circuit", "Oscar Piastri", "McLaren"),
    (3, "Japanese Grand Prix", "Suzuka Circuit", "Max Verstappen", "Red Bull Racing"),
    (4, "Bahrain Grand Prix", "Bahrain International Circuit", "Oscar Piastri", "McLaren"),
    (5, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "Oscar Piastri", "McLaren"),
    (6, "Miami Grand Prix", "Miami International Autodrome", "Oscar Piastri", "McLaren"),
    (7, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", "Max Verstappen", "Red Bull Racing"),
    (8, "Monaco Grand Prix", "Circuit de Monaco", "Lando Norris", "McLaren"),
    (9, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Oscar Piastri", "McLaren"),
    (10, "Canadian Grand Prix", "Circuit Gilles Villeneuve", "George Russell", "Mercedes"),
    (11, "Austrian Grand Prix", "Red Bull Ring", "Lando Norris", "McLaren"),
    (12, "British Grand Prix", "Silverstone Circuit", "Lando Norris", "McLaren"),
    (13, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Oscar Piastri", "McLaren"),
    (14, "Hungarian Grand Prix", "Hungaroring", None, None),
    (15, "Dutch Grand Prix", "Circuit Zandvoort", None, None),
    (16, "Italian Grand Prix", "Autodromo Nazionale Monza", None, None),
    (17, "Azerbaijan Grand Prix", "Baku City Circuit", None, None),
    (18, "Singapore Grand Prix", "Marina Bay Street Circuit", None, None),
    (19, "United States Grand Prix", "Circuit of the Americas", None, None),
    (20, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", None, None),
    (21, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", None, None),
    (22, "Las Vegas Grand Prix", "Las Vegas Strip Circuit", None, None),
    (23, "Qatar Grand Prix", "Lusail International Circuit", None, None),
    (24, "Abu Dhabi Grand Prix", "Yas Marina Circuit", None, None),
]


def main():
    db = SessionLocal()
    try:
        teams_by_name = {}
        for team_data in TEAMS:
            team = models.Team(**team_data)
            db.add(team)
            teams_by_name[team_data["name"]] = team
        db.flush()

        drivers_by_name = {}
        for car_number, nationality, name, date_of_birth, team_name in DRIVERS:
            driver = models.Driver(
                name=name,
                nationality=nationality,
                date_of_birth=date_of_birth,
            )
            db.add(driver)
            drivers_by_name[name] = driver
        db.flush()

        for car_number, _nationality, name, _date_of_birth, _team_name in DRIVERS:
            db.add(
                models.DriverNumber(
                    driver_id=drivers_by_name[name].id,
                    season=2025,
                    number=car_number,
                )
            )

        for sequence_number, name, track_name, winner_name, winner_team_name in GRANDS_PRIX_2025:
            db.add(
                models.GrandPrix(
                    season=2025,
                    sequence_number=sequence_number,
                    name=name,
                    track_name=track_name,
                    winning_driver_id=(
                        drivers_by_name[winner_name].id if winner_name else None
                    ),
                    winning_team_id=(
                        teams_by_name[winner_team_name].id if winner_team_name else None
                    ),
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
