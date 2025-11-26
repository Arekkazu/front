"""
WSGI entrypoint para Vercel.

Este archivo expone la variable `app` que Vercel (y otros entornos WSGI)
detectan automáticamente. Usa la factoría `create_app` ya definida en
`app/__init__.py`.

Notas:
- Se requieren las variables de entorno: SECRET_KEY, QR_SECRET_KEY, DATABASE_URL.
- Si no están definidas, se colocan valores por defecto mínimos para evitar falla en el build.
- En producción debes definirlas desde el panel de Vercel (Project Settings -> Environment Variables).
"""

import os

# Valores por defecto SOLO para evitar que el build falle si faltan variables.
# En producción reemplázalos desde las variables de entorno de Vercel.
_REQUIRED_ENV_DEFAULTS = {
    "SECRET_KEY": "change-this-secret",
    "QR_SECRET_KEY": "change-this-qr-secret",
    "DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/qr_flask",
}

for _k, _v in _REQUIRED_ENV_DEFAULTS.items():
    # No sobrescribe si ya existe en el entorno.
    os.environ.setdefault(_k, _v)


# Selección de configuración según FLASK_ENV
def _resolve_config_name() -> str:
    env = os.environ.get("FLASK_ENV", "").lower()
    if env in ("development", "production"):
        return env
    return "default"


from app import create_app  # Import tardío para que las variables estén listas

app = create_app(_resolve_config_name())


# Ruta opcional de health-check (si quieres usarla en Vercel)
@app.route("/api/health")
def health():
    return {"status": "ok"}, 200


# Permite ejecución local (python app.py) además del despliegue WSGI.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    print(f"[Entrypoint] Running local server on http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
