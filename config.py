import os

from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    QR_SECRET_KEY = os.environ["QR_SECRET_KEY"]
    # Requerir estrictamente DATABASE_URL desde el entorno (sin valores por defecto)
    _RAW_DATABASE_URL = os.environ["DATABASE_URL"]
    # Normalizar el esquema para usar el driver psycopg2 con SQLAlchemy
    if _RAW_DATABASE_URL.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = _RAW_DATABASE_URL.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    else:
        SQLALCHEMY_DATABASE_URI = _RAW_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QR_EXPIRATION = int(os.environ.get("QR_EXPIRATION", 60))  # segundos


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Diccionario de configuraciones accesible desde fuera
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

# Log de la URI final para verificación en el arranque
print(f"[Config] SQLALCHEMY_DATABASE_URI = {Config.SQLALCHEMY_DATABASE_URI}")
