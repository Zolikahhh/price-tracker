# Hivatalos Python 3.11 slim image
FROM python:3.11-slim

# Munkakönyvtár beállítása
WORKDIR /app

# Rendszerfüggőségek telepítése
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Requirements másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# A teljes forráskód másolása
COPY . .

# Megnyitjuk a 8000-es portot
EXPOSE 8000

# Indítás Uvicorn-nal
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]