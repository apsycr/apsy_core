SYNC_APPS = {

    "marcas": {

        "version": 1,

        "tables": [

            # =====================================
            # EMPLEADOS
            # =====================================

            {

                "tabla": "empleados",

                "version": 1,

                "create_table": """
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT,
                    cedula TEXT
                )
                """,

                "server_side": {

                    "pull": {

                        "table": "empleados",

                        "pk": "id",

                        "fields": [
                            "id",
                            "nombre",
                            "cedula"
                        ],

                        "where":
                        "idsucursal=@@idsucursal"

                    },

                    "push": {

                        "enabled": False

                    }

                },

                "client_side": {

                    "pull": {

                        "table": "empleados",

                        "fields": [
                            "id",
                            "nombre",
                            "cedula"
                        ]

                    },

                    "push": {

                        "enabled": False

                    }

                }

            },

            # =====================================
            # TIPO MARCAS
            # =====================================

            {

                "tabla": "tipomarcaempleados",

                "version": 1,

                "create_table": """
                CREATE TABLE IF NOT EXISTS tipomarcaempleados (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT,
                    label TEXT,
                    idsalida INTEGER,
                    idsucursal INTEGER
                )
                """,

                "server_side": {

                    "pull": {

                        "table": "tipomarcaempleados",

                        "pk": "id",

                        "fields": [

                            "id",

                            "nombre",

                            "label",

                            {
                                "field": "idsalida",
                                "expr":
                                "IF(label<>'',0,id+1)"
                            },

                            "idsucursal"

                        ],

                        "where":
                        "idsucursal=@@idsucursal"

                    }

                },

                "client_side": {

                    "pull": {

                        "table": "tipomarcaempleados",

                        "fields": [

                            "id",
                            "nombre",
                            "label",
                            "idsalida",
                            "idsucursal"

                        ]

                    }

                }

            },

            # =====================================
            # MARCAS
            # =====================================

            {

                "tabla": "marcas",

                "version": 1,

                "create_table": """
                CREATE TABLE IF NOT EXISTS marcas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idempleado INTEGER,
                    idmarca INTEGER,
                    fecha DATE,
                    entrada TIME,
                    salida TIME,
                    synced INTEGER DEFAULT 0
                )
                """,

                "server_side": {

                    # historial para consultas futuras

                    "pull": {

                        "table": "empleado_marcas",

                        "pk": "id",

                        "fields": [

                            "id",

                            {
                                "field": "idempleado",
                                "lookup": "empleados"
                            },

                            {
                                "field": "idmarca",
                                "lookup": "tipomarcaempleados"
                            },

                            "fecha",

                            "entrada",

                            "salida"

                        ],

                        "where":
                        "idsucursal=@@idsucursal"

                    },

                    # registros nuevos desde tablet

                    "push": {

                        "table": "empleado_marcas",

                        "fields": [

                            {
                                "field": "idempleado",
                                "lookup": "empleados"
                            },

                            {
                                "field": "idtipo",
                                "lookup": "tipomarcaempleados"
                            },

                            "fecha",

                            "entrada",

                            "salida"

                        ]

                    }

                },

                "client_side": {

                    "pull": {

                        "table": "marcas",

                        "fields": [

                            "id",
                            "idempleado",
                            "idmarca",
                            "fecha",
                            "entrada",
                            "salida"

                        ]

                    },

                    "push": {

                        "table": "marcas",

                        "fields": [

                            "idempleado",
                            "idmarca",
                            "fecha",
                            "entrada",
                            "salida"

                        ]

                    }

                },

                "depends": {

                    "idempleado": "empleados",

                    "idmarca": "tipomarcaempleados"

                }

            }

        ]
    }
}