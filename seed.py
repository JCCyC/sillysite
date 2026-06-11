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
    {"name": "AlphaTauri", "country": "Italy", "founded_year": 2020},
    {"name": "Alfa Romeo", "country": "Switzerland", "founded_year": 2019},
    {"name": "Renault", "country": "France", "founded_year": 2016},
    {"name": "Racing Point", "country": "United Kingdom", "founded_year": 2018},
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
    ("Nyck de Vries", "Netherlands", date(1995, 2, 6)),
    ("Sebastian Vettel", "Germany", date(1987, 7, 3)),
    ("Nicholas Latifi", "Canada", date(1995, 6, 29)),
    ("Mick Schumacher", "Germany", date(1999, 3, 22)),
    ("Kimi Raikkonen", "Finland", date(1979, 10, 17)),
    ("Antonio Giovinazzi", "Italy", date(1993, 12, 14)),
    ("Nikita Mazepin", "Russia", date(1999, 3, 2)),
    ("Daniil Kvyat", "Russia", date(1994, 4, 26)),
    ("Romain Grosjean", "France", date(1986, 4, 17)),
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
    # 2023
    ("Max Verstappen", 2023, 1),
    ("Sergio Perez", 2023, 11),
    ("Charles Leclerc", 2023, 16),
    ("Carlos Sainz", 2023, 55),
    ("Lewis Hamilton", 2023, 44),
    ("George Russell", 2023, 63),
    ("Lando Norris", 2023, 4),
    ("Oscar Piastri", 2023, 81),
    ("Fernando Alonso", 2023, 14),
    ("Lance Stroll", 2023, 18),
    ("Pierre Gasly", 2023, 10),
    ("Esteban Ocon", 2023, 31),
    ("Alex Albon", 2023, 23),
    ("Logan Sargeant", 2023, 2),
    ("Yuki Tsunoda", 2023, 22),
    ("Nyck de Vries", 2023, 21),
    ("Daniel Ricciardo", 2023, 3),
    ("Liam Lawson", 2023, 30),
    ("Nico Hulkenberg", 2023, 27),
    ("Kevin Magnussen", 2023, 20),
    ("Valtteri Bottas", 2023, 77),
    ("Zhou Guanyu", 2023, 24),
    # 2022
    ("Max Verstappen", 2022, 1),
    ("Sergio Perez", 2022, 11),
    ("Charles Leclerc", 2022, 16),
    ("Carlos Sainz", 2022, 55),
    ("Lewis Hamilton", 2022, 44),
    ("George Russell", 2022, 63),
    ("Lando Norris", 2022, 4),
    ("Daniel Ricciardo", 2022, 3),
    ("Fernando Alonso", 2022, 14),
    ("Esteban Ocon", 2022, 31),
    ("Sebastian Vettel", 2022, 5),
    ("Lance Stroll", 2022, 18),
    ("Alex Albon", 2022, 23),
    ("Nicholas Latifi", 2022, 6),
    ("Pierre Gasly", 2022, 10),
    ("Yuki Tsunoda", 2022, 22),
    ("Kevin Magnussen", 2022, 20),
    ("Mick Schumacher", 2022, 47),
    ("Valtteri Bottas", 2022, 77),
    ("Zhou Guanyu", 2022, 24),
    ("Nico Hulkenberg", 2022, 27),
    # 2021
    ("Lewis Hamilton", 2021, 44),
    ("Valtteri Bottas", 2021, 77),
    ("Max Verstappen", 2021, 1),
    ("Sergio Perez", 2021, 11),
    ("Charles Leclerc", 2021, 16),
    ("Carlos Sainz", 2021, 55),
    ("Lando Norris", 2021, 4),
    ("Daniel Ricciardo", 2021, 3),
    ("Fernando Alonso", 2021, 14),
    ("Esteban Ocon", 2021, 31),
    ("Pierre Gasly", 2021, 10),
    ("Yuki Tsunoda", 2021, 22),
    ("Sebastian Vettel", 2021, 5),
    ("Lance Stroll", 2021, 18),
    ("George Russell", 2021, 63),
    ("Nicholas Latifi", 2021, 6),
    ("Kimi Raikkonen", 2021, 7),
    ("Antonio Giovinazzi", 2021, 99),
    ("Mick Schumacher", 2021, 47),
    ("Nikita Mazepin", 2021, 9),
    # 2020
    ("Lewis Hamilton", 2020, 44),
    ("Valtteri Bottas", 2020, 77),
    ("Max Verstappen", 2020, 1),
    ("Alex Albon", 2020, 23),
    ("Charles Leclerc", 2020, 16),
    ("Sebastian Vettel", 2020, 5),
    ("Lando Norris", 2020, 4),
    ("Carlos Sainz", 2020, 55),
    ("Daniel Ricciardo", 2020, 3),
    ("Esteban Ocon", 2020, 31),
    ("Sergio Perez", 2020, 11),
    ("Lance Stroll", 2020, 18),
    ("Pierre Gasly", 2020, 10),
    ("Daniil Kvyat", 2020, 26),
    ("Kimi Raikkonen", 2020, 7),
    ("Antonio Giovinazzi", 2020, 99),
    ("Kevin Magnussen", 2020, 20),
    ("Romain Grosjean", 2020, 8),
    ("George Russell", 2020, 63),
    ("Nicholas Latifi", 2020, 6),
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
    2023: [
        (1, "Bahrain Grand Prix", "Bahrain International Circuit", "Max Verstappen", "Red Bull Racing"),
        (2, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "Sergio Perez", "Red Bull Racing"),
        (3, "Australian Grand Prix", "Albert Park Circuit", "Max Verstappen", "Red Bull Racing"),
        (4, "Azerbaijan Grand Prix", "Baku City Circuit", "Sergio Perez", "Red Bull Racing"),
        (5, "Miami Grand Prix", "Miami International Autodrome", "Max Verstappen", "Red Bull Racing"),
        (6, "Monaco Grand Prix", "Circuit de Monaco", "Max Verstappen", "Red Bull Racing"),
        (7, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Max Verstappen", "Red Bull Racing"),
        (8, "Canadian Grand Prix", "Circuit Gilles Villeneuve", "Max Verstappen", "Red Bull Racing"),
        (9, "Austrian Grand Prix", "Red Bull Ring", "Max Verstappen", "Red Bull Racing"),
        (10, "British Grand Prix", "Silverstone Circuit", "Max Verstappen", "Red Bull Racing"),
        (11, "Hungarian Grand Prix", "Hungaroring", "Max Verstappen", "Red Bull Racing"),
        (12, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Max Verstappen", "Red Bull Racing"),
        (13, "Dutch Grand Prix", "Circuit Zandvoort", "Max Verstappen", "Red Bull Racing"),
        (14, "Italian Grand Prix", "Autodromo Nazionale Monza", "Max Verstappen", "Red Bull Racing"),
        (15, "Singapore Grand Prix", "Marina Bay Street Circuit", "Carlos Sainz", "Ferrari"),
        (16, "Japanese Grand Prix", "Suzuka Circuit", "Max Verstappen", "Red Bull Racing"),
        (17, "Qatar Grand Prix", "Lusail International Circuit", "Max Verstappen", "Red Bull Racing"),
        (18, "United States Grand Prix", "Circuit of the Americas", "Max Verstappen", "Red Bull Racing"),
        (19, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", "Max Verstappen", "Red Bull Racing"),
        (20, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", "Max Verstappen", "Red Bull Racing"),
        (21, "Las Vegas Grand Prix", "Las Vegas Strip Circuit", "Max Verstappen", "Red Bull Racing"),
        (22, "Abu Dhabi Grand Prix", "Yas Marina Circuit", "Max Verstappen", "Red Bull Racing"),
    ],
    2022: [
        (1, "Bahrain Grand Prix", "Bahrain International Circuit", "Charles Leclerc", "Ferrari"),
        (2, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "Max Verstappen", "Red Bull Racing"),
        (3, "Australian Grand Prix", "Albert Park Circuit", "Charles Leclerc", "Ferrari"),
        (4, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", "Max Verstappen", "Red Bull Racing"),
        (5, "Miami Grand Prix", "Miami International Autodrome", "Max Verstappen", "Red Bull Racing"),
        (6, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Max Verstappen", "Red Bull Racing"),
        (7, "Monaco Grand Prix", "Circuit de Monaco", "Sergio Perez", "Red Bull Racing"),
        (8, "Azerbaijan Grand Prix", "Baku City Circuit", "Max Verstappen", "Red Bull Racing"),
        (9, "Canadian Grand Prix", "Circuit Gilles Villeneuve", "Max Verstappen", "Red Bull Racing"),
        (10, "British Grand Prix", "Silverstone Circuit", "Carlos Sainz", "Ferrari"),
        (11, "Austrian Grand Prix", "Red Bull Ring", "Max Verstappen", "Red Bull Racing"),
        (12, "French Grand Prix", "Circuit Paul Ricard", "Max Verstappen", "Red Bull Racing"),
        (13, "Hungarian Grand Prix", "Hungaroring", "Max Verstappen", "Red Bull Racing"),
        (14, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Max Verstappen", "Red Bull Racing"),
        (15, "Dutch Grand Prix", "Circuit Zandvoort", "Max Verstappen", "Red Bull Racing"),
        (16, "Italian Grand Prix", "Autodromo Nazionale Monza", "Max Verstappen", "Red Bull Racing"),
        (17, "Singapore Grand Prix", "Marina Bay Street Circuit", "Sergio Perez", "Red Bull Racing"),
        (18, "Japanese Grand Prix", "Suzuka Circuit", "Max Verstappen", "Red Bull Racing"),
        (19, "United States Grand Prix", "Circuit of the Americas", "Max Verstappen", "Red Bull Racing"),
        (20, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", "Max Verstappen", "Red Bull Racing"),
        (21, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", "George Russell", "Mercedes"),
        (22, "Abu Dhabi Grand Prix", "Yas Marina Circuit", "Max Verstappen", "Red Bull Racing"),
    ],
    2021: [
        (1, "Bahrain Grand Prix", "Bahrain International Circuit", "Lewis Hamilton", "Mercedes"),
        (2, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", "Max Verstappen", "Red Bull Racing"),
        (3, "Portuguese Grand Prix", "Autodromo Internacional do Algarve", "Lewis Hamilton", "Mercedes"),
        (4, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Lewis Hamilton", "Mercedes"),
        (5, "Monaco Grand Prix", "Circuit de Monaco", "Max Verstappen", "Red Bull Racing"),
        (6, "Azerbaijan Grand Prix", "Baku City Circuit", "Sergio Perez", "Red Bull Racing"),
        (7, "French Grand Prix", "Circuit Paul Ricard", "Max Verstappen", "Red Bull Racing"),
        (8, "Styrian Grand Prix", "Red Bull Ring", "Max Verstappen", "Red Bull Racing"),
        (9, "Austrian Grand Prix", "Red Bull Ring", "Max Verstappen", "Red Bull Racing"),
        (10, "British Grand Prix", "Silverstone Circuit", "Lewis Hamilton", "Mercedes"),
        (11, "Hungarian Grand Prix", "Hungaroring", "Esteban Ocon", "Alpine"),
        (12, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Max Verstappen", "Red Bull Racing"),
        (13, "Dutch Grand Prix", "Circuit Zandvoort", "Max Verstappen", "Red Bull Racing"),
        (14, "Italian Grand Prix", "Autodromo Nazionale Monza", "Daniel Ricciardo", "McLaren"),
        (15, "Russian Grand Prix", "Sochi Autodrom", "Lewis Hamilton", "Mercedes"),
        (16, "Turkish Grand Prix", "Istanbul Park", "Valtteri Bottas", "Mercedes"),
        (17, "United States Grand Prix", "Circuit of the Americas", "Max Verstappen", "Red Bull Racing"),
        (18, "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", "Max Verstappen", "Red Bull Racing"),
        (19, "Sao Paulo Grand Prix", "Autodromo Jose Carlos Pace", "Lewis Hamilton", "Mercedes"),
        (20, "Qatar Grand Prix", "Lusail International Circuit", "Lewis Hamilton", "Mercedes"),
        (21, "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "Lewis Hamilton", "Mercedes"),
        (22, "Abu Dhabi Grand Prix", "Yas Marina Circuit", "Max Verstappen", "Red Bull Racing"),
    ],
    2020: [
        (1, "Austrian Grand Prix", "Red Bull Ring", "Valtteri Bottas", "Mercedes"),
        (2, "Styrian Grand Prix", "Red Bull Ring", "Lewis Hamilton", "Mercedes"),
        (3, "Hungarian Grand Prix", "Hungaroring", "Lewis Hamilton", "Mercedes"),
        (4, "British Grand Prix", "Silverstone Circuit", "Lewis Hamilton", "Mercedes"),
        (5, "70th Anniversary Grand Prix", "Silverstone Circuit", "Max Verstappen", "Red Bull Racing"),
        (6, "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "Lewis Hamilton", "Mercedes"),
        (7, "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "Lewis Hamilton", "Mercedes"),
        (8, "Italian Grand Prix", "Autodromo Nazionale Monza", "Pierre Gasly", "AlphaTauri"),
        (9, "Tuscan Grand Prix", "Mugello Circuit", "Lewis Hamilton", "Mercedes"),
        (10, "Russian Grand Prix", "Sochi Autodrom", "Valtteri Bottas", "Mercedes"),
        (11, "Eifel Grand Prix", "Nurburgring", "Lewis Hamilton", "Mercedes"),
        (12, "Portuguese Grand Prix", "Autodromo Internacional do Algarve", "Lewis Hamilton", "Mercedes"),
        (13, "Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari", "Lewis Hamilton", "Mercedes"),
        (14, "Turkish Grand Prix", "Istanbul Park", "Lewis Hamilton", "Mercedes"),
        (15, "Bahrain Grand Prix", "Bahrain International Circuit", "Lewis Hamilton", "Mercedes"),
        (16, "Sakhir Grand Prix", "Bahrain International Circuit", "Sergio Perez", "Racing Point"),
        (17, "Abu Dhabi Grand Prix", "Yas Marina Circuit", "Max Verstappen", "Red Bull Racing"),
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
