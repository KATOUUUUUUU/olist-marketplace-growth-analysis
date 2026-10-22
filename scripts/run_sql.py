from pathlib import Path
import sys

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "olist.duckdb"


def main() -> None:
    sql_path = PROJECT_ROOT / (sys.argv[1] if len(sys.argv) > 1 else "sql/01_market_overview.sql")

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    query = sql_path.read_text(encoding="utf-8")

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        result = con.sql(query).fetchdf()

    print(f"\nSQL file: {sql_path.relative_to(PROJECT_ROOT)}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
