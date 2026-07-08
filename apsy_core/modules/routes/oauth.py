from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from modules.oauth.ctr_oauth import OAuth

oauth = OAuth()

router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

@router.get("/{provider}/connect")
async def connect(
    provider: str,
    context: str = "{}"
):

    return oauth.connect(
        provider,
        json.loads(context)
    )


@router.get("/{provider}/callback")
async def callback(
    provider: str,
    code: str,
    state: str = None
):

    return oauth.callback(
        provider,
        code=code,
        state=state
    )

@router.get("/test")
async def test():

    return {
        "ok": True,
        "message": "OAuth activo"
    }