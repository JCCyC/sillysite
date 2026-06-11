"""One-off script to seed the database with 2025 Formula One season data.

Run with: .venv/bin/python seed.py

Note: results for races after the British/Belgian GPs (roughly mid-2025
onward) are left without a winner, since they are outside the data this
was written from.
"""

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

# (car_number, country, name, team_name)
DRIVERS = [
    (1, "Netherlands", "Max Verstappen", "Red Bull Racing"),
    (22, "Japan", "Yuki Tsunoda", "Red Bull Racing"),
    (16, "Monaco", "Charles Leclerc", "Ferrari"),
    (44, "United Kingdom", "Lewis Hamilton", "Ferrari"),
    (4, "United Kingdom", "Lando Norris", "McLaren"),
    (81, "Australia", "Oscar Piastri", "McLaren"),
    (63, "United Kingdom", "George Russell", "Mercedes"),
    (12, "Italy", "Andrea Kimi Antonelli", "Mercedes"),
    (14, "Spain", "Fernando Alonso", "Aston Martin"),
    (18, "Canada", "Lance Stroll", "Aston Martin"),
    (10, "France", "Pierre Gasly", "Alpine"),
    (43, "Argentina", "Franco Colapinto", "Alpine"),
    (23, "Thailand", "Alex Albon", "Williams"),
    (55, "Spain", "Carlos Sainz", "Williams"),
    (30, "New Zealand", "Liam Lawson", "Racing Bulls"),
    (6, "France", "Isack Hadjar", "Racing Bulls"),
    (31, "France", "Esteban Ocon", "Haas"),
    (87, "United Kingdom", "Oliver Bearman", "Haas"),
    (27, "Germany", "Nico Hulkenberg", "Kick Sauber"),
    (5, "Brazil", "Gabriel Bortoleto", "Kick Sauber"),
]

# (sequence_number, name, track_name, winning_car_number)
GRANDS_PRIX_2025 = [
    (1, "Australian Grand Prix", "Albert Park Circuit", 4),
    (2, "Chinese Grand Prix", "Shanghai International Circuit", 81),
    (3, "Japanese Grand Prix", "Suzuka Circuit", 1),
    (4, "Bahrain Grand Prix", "Bahrain International Circuit", 81),
    (5, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", 81),
    (6, "Miami Grand Prix", "Miami International Autodrome", 81),
    (7, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", 1),
    (8, "Monaco Grand Prix", "Circuit de Monaco", 4),
    (9, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", 81),
    (10, "Canadian Grand Prix", "Circuit Gilles Villeneuve", 63),
    (11, "Austrian Grand Prix", "Red Bull Ring", 4),
    (12, "British Grand Prix", "Silverstone Circuit", 4),
    (13, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", 81),
    (14, "Hungarian Grand Prix", "Hungaroring", None),
    (15, "Dutch Grand Prix", "Circuit Zandvoort", None),
    (16, "Italian Grand Prix", "Autodromo Nazionale Monza", None),
    (17, "Azerbaijan Grand Prix", "Baku City Circuit", None),
    (18, "Singapore Grand Prix", "Marina Bay Street Circuit", None),
    (19, "United States Grand Prix", "Circuit of the Americas", None),
    (20, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", None),
    (21, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", None),
    (22, "Las Vegas Grand Prix", "Las Vegas Strip Circuit", None),
    (23, "Qatar Grand Prix", "Lusail International Circuit", None),
    (24, "Abu Dhabi Grand Prix", "Yas Marina Circuit", None),
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

        for car_number, country, name, team_name in DRIVERS:
            db.add(
                models.Driver(
                    car_number=car_number,
                    country=country,
                    name=name,
                    team_id=teams_by_name[team_name].id,
                )
            )
        db.flush()

        for sequence_number, name, track_name, winner in GRANDS_PRIX_2025:
            db.add(
                models.GrandPrix(
                    season=2025,
                    sequence_number=sequence_number,
                    name=name,
                    track_name=track_name,
                    winning_driver_car_number=winner,
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
