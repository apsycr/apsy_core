from fastapi import APIRouter, HTTPException, Request
from modules.services.formularios import guardar_formulario

router = APIRouter()

@router.post("/site")
def login(data: dict):
    user = data.get("user")
    password = data.get("pass")

    # 🔴 aquí luego conectas MariaDB
    if user == "admin" and password == "123":
        return {
            "token": "fake-jwt-token",
            "tipo": "cms"
        }

    raise HTTPException(status_code=401, detail="Credenciales inválidas")


@router.get("/site")
def me():
    return {"user": "admin", "tipo": "cms"}

@router.post("/forms/{codigo}")
async def guardar_forms(codigo: str, request: Request):
    data = await request.json()
    return guardar_formulario(codigo, data)