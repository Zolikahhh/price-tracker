import asyncio
from src.db.session import init_db

async def main():
    print("PostgreSQL táblák létrehozása...")
    await init_db()
    print("Sikeresen létrejöttek a táblák a PostgreSQL adatbázisban!")

if __name__ == "__main__":
    asyncio.run(main())