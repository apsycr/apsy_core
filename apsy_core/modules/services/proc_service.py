from modules.db import get_db


def save_proceso(proceso_id, campos):
    with get_db() as db:   
        # 1. borrar definición previa
        db.execute(f"DELETE FROM procesos.elementos_procesos WHERE id_proceso={proceso_id}")

        # 2. insertar nueva definición
        for i, c in enumerate(campos):

            sql = f"""
            INSERT INTO procesos.elementos_procesos
            (id_proceso, campo, elemento, tipo, orden)
            VALUES
            ({proceso_id}, '{c['campo']}', '{c['elemento']}', '{c['tipo']}', {i})
            """

            db.execute(sql)

        # 3. crear / actualizar tabla
        tabla = generar_tabla_proceso(proceso_id)

        return tabla