from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import config

DATABASE_URL = (
    f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": f"-csearch_path={config.DB_SCHEMA}"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
