import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alumnos_api:alumnos_api_2026*@127.0.0.1:5432/alumnos")