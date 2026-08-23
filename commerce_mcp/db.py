from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from commerce_mcp.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine: Engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)


def test_connection() -> bool:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        return result.scalar_one() == 1

if __name__ == "__main__":
    print("DB connected:", test_connection())