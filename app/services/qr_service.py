import time

from flask import current_app

from app.utils.qr_generator import (
    generate_qr_image,
    generate_qr_token,
    validate_qr_token,
)


class QRService:
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def create_qr_data(self, user_id):
        """Genera el token para el QR del usuario."""
        token = generate_qr_token(user_id, self.secret_key)
        return {"token": token, "image": generate_qr_image(token)}

    def validate_qr_data(self, token):
        """Valida el token del QR escaneado."""
        tolerance = int(current_app.config.get("QR_EXPIRATION", 60))
        return validate_qr_token(token, self.secret_key, tolerance=tolerance)
