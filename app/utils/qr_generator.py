import base64
import hashlib
import hmac
import io
import time

import qrcode


class QRGenerator:
    """
    - secret_key: clave secreta usada para firmar tokens.
    - expiration: ventana de expiración recomendada del token (segundos). Se mantiene como configuración interna.
    - tolerance: tolerancia de tiempo (segundos) para la validación de tokens.
    """

    def __init__(
        self, secret_key: str, expiration: int = 60, tolerance: int = 90
    ) -> None:

        self._secret_key: str = ""
        self._expiration: int = 0
        self._tolerance: int = 0

        self.secret_key = secret_key
        self.expiration = expiration
        self.tolerance = tolerance

    @property
    def secret_key(self) -> str:
        return self._secret_key

    @secret_key.setter
    def secret_key(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("secret_key debe ser un string no vacío")
        self._secret_key = value

    @property
    def expiration(self) -> int:
        return self._expiration

    @expiration.setter
    def expiration(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("expiration debe ser un entero positivo (segundos)")
        self._expiration = value

    @property
    def tolerance(self) -> int:
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("tolerance debe ser un entero positivo (segundos)")
        self._tolerance = value

    def generate_token(self, user_id: int) -> str:
        """
        Genera un token firmado para el usuario con el formato:
        'user_id:timestamp:signature'
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id debe ser un entero positivo")

        timestamp = int(time.time())
        payload = f"{user_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return f"{payload}:{signature}"

    def validate_token(self, token: str) -> int | None:
        """
        Valida el token firmado y retorna el user_id si es válido, de lo contrario None.
        La validación verifica:
        - Formato correcto
        - No exceder la tolerancia temporal
        - Firma HMAC SHA-256 válida
        """
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return None
            user_id_str, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
        except (ValueError, IndexError):
            return None

        if time.time() - timestamp > self.tolerance:
            return None

        expected_sig = hmac.new(
            self.secret_key.encode(),
            f"{user_id_str}:{timestamp_str}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            return None

        try:
            return int(user_id_str)
        except ValueError:
            return None

    def generate_image(self, token: str) -> str:
        """
        Genera una imagen QR en base64 a partir de un token.
        Retorna el PNG codificado en base64.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64

def generate_qr_token(user_id, secret_key, expiration=60):
    """
    Compatibilidad: genera token usando QRGenerator.
    """
    generator = QRGenerator(secret_key=secret_key, expiration=expiration)
    return generator.generate_token(user_id)

def validate_qr_token(token, secret_key, tolerance=90):
    """
    Compatibilidad: valida token usando QRGenerator con la tolerancia indicada.
    """
    generator = QRGenerator(secret_key=secret_key, tolerance=tolerance)
    return generator.validate_token(token)

def generate_qr_image(token):
    """
    Compatibilidad: genera imagen QR en base64 usando QRGenerator.
    """

    generator = QRGenerator(secret_key="__unused__", tolerance=90, expiration=60)
    return generator.generate_image(token)

