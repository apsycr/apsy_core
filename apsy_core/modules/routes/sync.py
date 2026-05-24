from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/sync")
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


@router.get("/sync")
def me():
    return {"user": "admin", "tipo": "cms"}