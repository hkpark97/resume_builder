from sqlalchemy import text
from app.db import engine


def column_exists(table_name: str, column_name: str) -> bool:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return any(row[1] == column_name for row in rows)


def add_column_if_missing(table_name: str, column_name: str, column_sql: str):
    if column_exists(table_name, column_name):
        print(f"{table_name}.{column_name} already exists")
        return

    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))
        print(f"Added {table_name}.{column_name}")


if __name__ == "__main__":
    add_column_if_missing(
        "users",
        "reset_token_hash",
        "reset_token_hash VARCHAR(255)",
    )

    add_column_if_missing(
        "users",
        "reset_token_expires_at",
        "reset_token_expires_at DATETIME",
    )

    print("Password reset migration complete.")