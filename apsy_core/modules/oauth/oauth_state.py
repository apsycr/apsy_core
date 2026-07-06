import base64
import json


class OAuthState:

    @staticmethod
    def encode(data: dict) -> str:

        payload = json.dumps(data).encode()

        return base64.urlsafe_b64encode(
            payload
        ).decode()

    @staticmethod
    def decode(state: str) -> dict:

        try:

            payload = base64.urlsafe_b64decode(
                state.encode()
            )

            return json.loads(payload)

        except Exception:

            return {
                "idsucursal": 0,
                "uso": "SEND"
            }