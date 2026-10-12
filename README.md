# Price Tracker API

Egy automatizált termékárazás-követő és értesítő rendszer, amely **FastAPI**, **PostgreSQL** és **APScheduler** alapokon nyújt valóidejű web scraping funkciókat az **Amazon** és az **Alza** felületéről.

---

## Főbb funkciók

- **Felhasználói hitelesítés:** Secure JWT (JSON Web Token) alapú regisztráció és bejelentkezés.
- **Intelligens Scraping:**
  - **Amazon:** ASIN kinyerés tiszta URL-ekhez, felülbírált valuta- és nyelvi beállítások (`currency=EUR`, `language=en_GB`) a pontos árképzésért, tizedeshely-kezelés (HUF/EUR).
  - **Alza:** Robusztus scraping botvédelem-elkerüléssel (Custom Headers, Re-try logika).
- **Automata időzítő (APScheduler):** Rendszeres háttérbeli ellenőrzés konfigurálható intervallumokkal és lekérdezési szünetekkel.
- **E-mailes értesítés:** Automatikus, elegáns HTML formátumú e-mail küldés SMTP-n (`aiosmtplib`) keresztül, ha a termék ára eléri a felhasználó által beállított célárat (`target_price`).
- **Értesítési duplikáció elleni védelem:** `last_notified_at` állapotkezelés az adatbázisban, hogy minden árcsökkenési mérföldkőnél csak egyszer küldjön e-mailt a rendszer.

---

## Technológiai Stack

- **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
- **Adatbázis & ORM:** PostgreSQL 15, [SQLAlchemy](https://www.sqlalchemy.org/) (Async Engine), [Asyncpg](https://github.com/MagicStack/asyncpg)
- **Scraping Engine:** `curl_cffi` (Chrome impersonation) & `BeautifulSoup4`
- **Időzítő:** [APScheduler](https://apscheduler.readthedocs.io/)
- **E-mail küldő:** `aiosmtplib` & Python `email.mime`
- **Konténerizáció:** Docker & Docker Compose

---

## Projekt Struktúra

price-tracker/
├── .env                    # Sensitiv adatok (Gitignore-ban legyen!)
├── .env.example            # Minta környezeti változók a repository-hoz
├── .gitignore              # Git által figyelmen kívül hagyott fájlok
├── Dockerfile              # Python web konténer image leírása
├── docker-compose.yml      # Docker szervizek (web API, PostgreSQL db)
├── README.md               # Projekt dokumentáció (ez jelenik meg GitHubon)
├── requirements.txt        # Python függőségek listája
│
├── alembic.ini             # Alembic konfigurációs fájl
├── alembic/                # Adatbázis migrációs mappa (Gitbe való!)
│   ├── env.py              # Alembic futtatási környezet setup
│   ├── script.py.mako      # Migrációs szkript sablon
│   └── versions/           # A konkrét generált migrációs fájlok (.py)
│
└── src/                    # Az alkalmazás forráskódja
    ├── __init__.py
    ├── main.py             # FastAPI belépési pont (app, CORS, routerek, scheduler indítás)
    │
    ├── api/                # API útvonalak és végpontok
    │   ├── __init__.py
    │   ├── deps.py
    │   ├── schemas.py
    │   └── v1/
    │       ├── __init__.py
    │       ├── auth.py
    │       ├── router.py
    │       └── endpoints/
    │           ├── health.py
    │           ├── price_history.py
    │           ├── products.py
    │           ├── subscriptions.py
    │           └── users.py
    │
    ├── config/
    │   ├──  __init__.py
    │   └── settings.py
    │
    ├── core/               # Konfiguráció és biztonság
    │   └── security.py     # Jelszó hashelés (bcrypt) & JWT token generálás
    │
    ├── db/                 # Adatbázis réteg
    │   ├── __init__.py
    │   ├── session.py      # AsyncSessionLocal & SQLAlchemy engine
    │   └── models.py       # SQLAlchemy adatbázis modellek (User, Product, etc.)
    │
    ├── schemas/            # Pydantic adatkérési / válasz modellek (DTO-k)
    │   ├── __init__.py
    │   └── product.py
    │
    └── services/           # Üzleti logika & külső integrációk
        ├── __init__.py
        ├── scraper.py      # Web scraping logika (Amazon, Alza - curl_cffi)
        ├── scheduler.py    # APScheduler háttérfeladatok & árellenőrzés
        ├── email.py        # aiosmtplib e-mail küldő szerviz
        └── notifier.py


---

## Telepítés és Indítás

### 1. Előkövetelmények

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) telepítve a rendszeren.
- Git (opcionális).

### 2. Környezeti változók konfigurálása

Hozz létre egy `.env` fájlt a projekt gyökerében a `.env.example` alapján:

```bash
cp .env.example .env
```

Töltsd ki az adatokat a saját értékeiddel (különösen a Google Alkalmazásjelszót):

```env
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=
EMAILS_FROM_NAME=
```

### 3. Konténerek indítása

Futtasd a Docker Compose parancsot a háttérben történő indításhoz:

```bash
docker-compose up -d --build
```

A szolgáltatások elindulnak:
- **FastAPI API:** `http://localhost:8000`
- **PostgreSQL Adatbázis:** `localhost:5432`

---

## API Dokumentáció & Tesztelés

Az alkalmazás elindítása után az interaktív Swagger UI dokumentáció az alábbi címen érhető el:

**[http://localhost:8000/docs](http://localhost:8000/docs)**

### Fő végpontok áttekintése:

| Metódus | Végpont | Leírás |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Új felhasználó regisztrációja |
| `POST` | `/api/v1/auth/login` | Bejelentkezés & OAuth2 JWT token beszerzés |
| `GET` | `/api/v1/products` | Nyomon követett termékek listája |
| `POST` | `/api/v1/products` | Új termék hozzáadása (URL alapján) |
| `DELETE`| `/api/v1/products/{id}` | Termék törlése |
| `GET` | `/api/v1/subscriptions` | Saját feliratkozások lekérése |
| `POST` | `/api/v1/subscriptions` | Célár beállítása egy adott termékhez |

---

## Logok és Diagnosztika

A folyamatban lévő árellenőrzések, scraping műveletek és e-mail küldések logjait a következő paranccsal tudod valós időben követni:

```bash
docker-compose logs -f web
```

---