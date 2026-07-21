from modules.db import ejecutar_api


class State:

    @staticmethod
    def change(
        table,
        where,
        params,
        estado,
        motivo=None,
        idusuario=None,
        idsucursal=None,
        idtenant=None
    ):

        sql = f"""

            SELECT
                id,
                estado

            FROM {table}

            WHERE {where}

            LIMIT 1

        """

        row = ejecutar_api(
            sql,
            params,
            'one'
        )

        if not row:
            return False

        estado_anterior = row["estado"]

        update_sql = f"""

            UPDATE {table}

            SET estado=%s

            WHERE {where}

        """

        ejecutar_api(
            update_sql,
            (estado, *params),
            'none'
        )

        ejecutar_api(
            """

            INSERT INTO system_states (

                tabla,
                idregistro,

                estado_anterior,
                estado_nuevo,

                motivo,

                idusuario,
                idsucursal,
                idtenant

            )

            VALUES (

                %s,
                %s,

                %s,
                %s,

                %s,

                %s,
                %s,
                %s

            )

            """,

            (

                table,
                row["id"],

                estado_anterior,
                estado,

                motivo,

                idusuario,
                idsucursal,
                idtenant

            ),
            'none'

        )

        return True