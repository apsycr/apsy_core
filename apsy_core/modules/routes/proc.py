from fastapi import APIRouter, HTTPException
from modules.services.proc_service import save_proceso

router = APIRouter()

@router.post("/proc/save")
def proc_save(data: dict):

    try:

        #proceso_id = data.get("proceso_id")
        #campos = data.get("campos")

        #result = save_proceso(proceso_id, campos)
        result = 'ok'
        return {"status": "ok", "tabla": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))