import asyncio
import uuid
from modules.db import ejecutar

class MirrorManager:

    def __init__(self):

        # ==========================================
        # WS ACTIVOS
        # ws_server_id -> websocket
        # ==========================================

        self.connections = {}

        # ==========================================
        # REQUESTS PENDIENTES
        # request_id -> Future
        # ==========================================

        self.pending = {}

    def validar_mirror(self,mirror):

        if mirror == "":

            return {
                "ok": False,
                "msg": "Mirror requerido"
            }

        row_mirror = ejecutar("""

            SELECT
                id,
                ws_server_id,
                activo
            FROM ws_sucursales
            WHERE alias = %s
            LIMIT 1

        """, (mirror,), "one")

        if not row_mirror:

            return {
                "ok": False,
                "msg": "Mirror no existe"
            }

        if row_mirror["activo"] != 1:

            return {
                "ok": False,
                "msg": "Mirror inactivo"
            }

        if not mirror_manager.exists(
            row_mirror["ws_server_id"]
        ):

            return {
                "ok": False,
                "msg": "Mirror offline"
            }

        return {
                "ok": True,
                "ws_server_id": row_mirror["ws_server_id"]
            }

    # =====================================================
    # REGISTER
    # =====================================================

    async def register(
        self,
        ws_server_id,
        websocket
    ):

        self.connections[ws_server_id] = websocket

        print(
            f"[MIRROR] conectado -> {ws_server_id}"
        )

    # =====================================================
    # REMOVE
    # =====================================================

    async def remove(self, ws_server_id):

        if ws_server_id in self.connections:
            del self.connections[ws_server_id]

        print(
            f"[MIRROR] desconectado -> {ws_server_id}"
        )

    # =====================================================
    # EXISTS
    # =====================================================

    def exists(self, ws_server_id):

        return ws_server_id in self.connections

    # =====================================================
    # HANDLE MESSAGE
    # =====================================================

    async def handle_message(
        self,
        data
    ):

        msg_type = data.get(
            "type"
        )

        if msg_type != "action_response":
            return

        request_id = data.get(
            "request_id"
        )

        if not request_id:
            return

        future = self.pending.get(
            request_id
        )

        if future and not future.done():

            future.set_result(
                data
            )

    # =====================================================
    # SEND API LOCAL
    # =====================================================

    async def send_api(

        self,

        ws_server_id,

        endpoint,

        body=None,

        headers=None,

        method="POST",

        timeout=15

    ):

        body = dict(body or {})
        headers = dict(headers or {})

        # ==========================================
        # EVITAR LOOP DE MIRROR
        # ==========================================

        headers.pop(
            "X-Mirror",
            None
        )

        return await self._send_request(

            ws_server_id,

            {

                "type": "mirror_api",

                "endpoint": endpoint,

                "method": method,

                "headers": headers,

                "body": body

            },

            timeout

        )

    async def send_rpc(

        self,

        ws_server_id,

        action,

        payload=None,

        timeout=15

    ):

        if payload is None:
            payload = {}

        return await self._send_request(

            ws_server_id,

            {

                "type": "rpc",

                "action": action,

                "payload": payload

            },

            timeout

        )
    async def _send_request(

        self,

        ws_server_id,

        message,

        timeout=15

    ):

        # ==========================================
        # MIRROR ONLINE
        # ==========================================

        if ws_server_id not in self.connections:

            raise Exception(
                "Mirror offline"
            )

        websocket = self.connections[
            ws_server_id
        ]

        # ==========================================
        # REQUEST ID
        # ==========================================

        request_id = str(
            uuid.uuid4()
        )

        message[
            "request_id"
        ] = request_id

        # ==========================================
        # FUTURE
        # ==========================================

        future = asyncio.Future()

        self.pending[
            request_id
        ] = future

        try:

            await websocket.send_json(
                message
            )

            response = await asyncio.wait_for(

                future,

                timeout=timeout

            )

            return response

        finally:

            self.pending.pop(
                request_id,
                None
            )


mirror_manager = MirrorManager()