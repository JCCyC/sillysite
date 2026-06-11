"""One-off script to seed the database with Formula One season data (2014-2025).

Run with: .venv/bin/python seed.py

Note: results for 2025 races after the British/Belgian GPs (roughly mid-2025
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

# (name, nationality, date_of_birth)
DRIVERS = [
    ("Max Verstappen", "Netherlands", date(1997, 9, 30)),
    ("Yuki Tsunoda", "Japan", date(2000, 5, 11)),
    ("Charles Leclerc", "Monaco", date(1997, 10, 16)),
    ("Lewis Hamilton", "United Kingdom", date(1985, 1, 7)),
    ("Lando Norris", "United Kingdom", date(1999, 11, 13)),
    ("Oscar Piastri", "Australia", date(2001, 4, 6)),
    ("George Russell", "United Kingdom", date(1998, 2, 15)),
    ("Andrea Kimi Antonelli", "Italy", date(2006, 8, 25)),
    ("Fernando Alonso", "Spain", date(1981, 7, 29)),
    ("Lance Stroll", "Canada", date(1998, 10, 29)),
    ("Pierre Gasly", "France", date(1996, 2, 7)),
    ("Franco Colapinto", "Argentina", date(2003, 5, 27)),
    ("Alex Albon", "Thailand", date(1996, 3, 23)),
    ("Carlos Sainz", "Spain", date(1994, 9, 1)),
    ("Liam Lawson", "New Zealand", date(2002, 2, 11)),
    ("Isack Hadjar", "France", date(2004, 9, 28)),
    ("Esteban Ocon", "France", date(1996, 9, 17)),
    ("Oliver Bearman", "United Kingdom", date(2005, 5, 8)),
    ("Nico Hulkenberg", "Germany", date(1987, 8, 19)),
    ("Gabriel Bortoleto", "Brazil", date(2004, 10, 14)),
    ("Sergio Perez", "Mexico", date(1990, 1, 26)),
    ("Logan Sargeant", "United States", date(2000, 12, 31)),
    ("Daniel Ricciardo", "Australia", date(1989, 7, 1)),
    ("Kevin Magnussen", "Denmark", date(1992, 10, 5)),
    ("Valtteri Bottas", "Finland", date(1989, 8, 28)),
    ("Zhou Guanyu", "China", date(1999, 5, 30)),
]

# (driver_name, season, number)
DRIVER_NUMBERS = [
    # 2025
    ("Max Verstappen", 2025, 1),
    ("Yuki Tsunoda", 2025, 22),
    ("Charles Leclerc", 2025, 16),
    ("Lewis Hamilton", 2025, 44),
    ("Lando Norris", 2025, 4),
    ("Oscar Piastri", 2025, 81),
    ("George Russell", 2025, 63),
    ("Andrea Kimi Antonelli", 2025, 12),
    ("Fernando Alonso", 2025, 14),
    ("Lance Stroll", 2025, 18),
    ("Pierre Gasly", 2025, 10),
    ("Franco Colapinto", 2025, 43),
    ("Alex Albon", 2025, 23),
    ("Carlos Sainz", 2025, 55),
    ("Liam Lawson", 2025, 30),
    ("Isack Hadjar", 2025, 6),
    ("Esteban Ocon", 2025, 31),
    ("Oliver Bearman", 2025, 87),
    ("Nico Hulkenberg", 2025, 27),
    ("Gabriel Bortoleto", 2025, 5),
    # 2024
    ("Max Verstappen", 2024, 1),
    ("Sergio Perez", 2024, 11),
    ("Charles Leclerc", 2024, 16),
    ("Carlos Sainz", 2024, 55),
    ("Lewis Hamilton", 2024, 44),
    ("George Russell", 2024, 63),
    ("Lando Norris", 2024, 4),
    ("Oscar Piastri", 2024, 81),
    ("Fernando Alonso", 2024, 14),
    ("Lance Stroll", 2024, 18),
    ("Pierre Gasly", 2024, 10),
    ("Esteban Ocon", 2024, 31),
    ("Alex Albon", 2024, 23),
    ("Logan Sargeant", 2024, 2),
    ("Franco Colapinto", 2024, 43),
    ("Yuki Tsunoda", 2024, 22),
    ("Daniel Ricciardo", 2024, 3),
    ("Liam Lawson", 2024, 30),
    ("Nico Hulkenberg", 2024, 27),
    ("Kevin Magnussen", 2024, 20),
    ("Valtteri Bottas", 2024, 77),
    ("Zhou Guanyu", 2024, 24),
]

# season -> list of (sequence_number, name, track_name, winning_driver_name, winning_team_name)
GRANDS_PRIX = {
    2025: [
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
    ],
    2024: [
        (1, "Bahrain Grand Prix", "Bahrain International Circuit", "Max Verstappen", "Red Bull Racing"),
        (2, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "Max Verstappen", "Red Bull Racing"),
        (3, "Australian Grand Prix", "Albert Park Circuit", "Carlos Sainz", "Ferrari"),
        (4, "Japanese Grand Prix", "Suzuka Circuit", "Max Verstappen", "Red Bull Racing"),
        (5, "Chinese Grand Prix", "Shanghai International Circuit", "Max Verstappen", "Red Bull Racing"),
        (6, "Miami Grand Prix", "Miami International Autodrome", "Lando Norris", "McLaren"),
        (7, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", "Max Verstappen", "Red Bull Racing"),
        (8, "Monaco Grand Prix", "Circuit de Monaco", "Charles Leclerc", "Ferrari"),
        (9, "Canadian Grand Prix", "Circuit Gilles Villeneuve", "Max Verstappen", "Red Bull Racing"),
        (10, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Max Verstappen", "Red Bull Racing"),
        (11, "Austrian Grand Prix", "Red Bull Ring", "George Russell", "Mercedes"),
        (12, "British Grand Prix", "Silverstone Circuit", "Lewis Hamilton", "Mercedes"),
        (13, "Hungarian Grand Prix", "Hungaroring", "Oscar Piastri", "McLaren"),
        (14, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Lewis Hamilton", "Mercedes"),
        (15, "Dutch Grand Prix", "Circuit Zandvoort", "Lando Norris", "McLaren"),
        (16, "Italian Grand Prix", "Autodromo Nazionale Monza", "Charles Leclerc", "Ferrari"),
        (17, "Azerbaijan Grand Prix", "Baku City Circuit", "Oscar Piastri", "McLaren"),
        (18, "Singapore Grand Prix", "Marina Bay Street Circuit", "Lando Norris", "McLaren"),
        (19, "United States Grand Prix", "Circuit of the Americas", "Charles Leclerc", "Ferrari"),
        (20, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", "Carlos Sainz", "Ferrari"),
        (21, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", "Max Verstappen", "Red Bull Racing"),
        (22, "Las Vegas Grand Prix", "Las Vegas Strip Circuit", "George Russell", "Mercedes"),
        (23, "Qatar Grand Prix", "Lusail International Circuit", "Max Verstappen", "Red Bull Racing"),
        (24, "Abu Dhabi Grand Prix", "Yas Marina Circuit", "Lando Norris", "McLaren"),
    ],
}


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
        for name, nationality, date_of_birth in DRIVERS:
            driver = models.Driver(
                name=name,
                nationality=nationality,
                date_of_birth=date_of_birth,
            )
            db.add(driver)
            drivers_by_name[name] = driver
        db.flush()

        for driver_name, season, number in DRIVER_NUMBERS:
            db.add(
                models.DriverNumber(
                    driver_id=drivers_by_name[driver_name].id,
                    season=season,
                    number=number,
                )
            )

        for season, races in GRANDS_PRIX.items():
            for sequence_number, name, track_name, winner_name, winner_team_name in races:
                db.add(
                    models.GrandPrix(
                        season=season,
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
