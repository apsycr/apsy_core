import asyncio
import uuid

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

    async def handle_message(self, data):

        tipo = data.get("type")

        # ==========================================
        # RPC RESPONSE
        # ==========================================

        if tipo == "action_response":

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
    # SEND ACTION
    # =====================================================

    async def send_action(

        self,

        ws_server_id,

        action,

        payload=None,

        timeout=15

    ):

        if payload is None:
            payload = {}

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

        # ==========================================
        # MESSAGE
        # ==========================================

        message = {

            "type": "action",

            "action": action,

            "request_id": request_id,

            "payload": payload

        }

        # ==========================================
        # FUTURE
        # ==========================================

        future = asyncio.Future()

        self.pending[
            request_id
        ] = future

        try:

            # ======================================
            # SEND WS
            # ======================================

            await websocket.send_json(
                message
            )

            # ======================================
            # WAIT RESPONSE
            # ======================================

            response = await asyncio.wait_for(

                future,

                timeout=timeout

            )

            return response

        finally:

            # ======================================
            # CLEANUP
            # ======================================

            if request_id in self.pending:

                del self.pending[
                    request_id
                ]


mirror_manager = MirrorManager()