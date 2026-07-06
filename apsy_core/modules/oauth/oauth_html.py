from fastapi.responses import HTMLResponse


class OAuthHTML:

    def __init__(self):

        self.style = """
:root{

    --bg:#0f172a;
    --bg-card:#1e293b;
    --border:#334155;
    --text:#f8fafc;
    --text-secondary:#94a3b8;
    --accent:#2563eb;

}

*{

    margin:0;
    padding:0;
    box-sizing:border-box;

}

body{

    font-family:Arial,Helvetica,sans-serif;
    background:var(--bg);
    color:var(--text);

    display:flex;
    align-items:center;
    justify-content:center;

    min-height:100vh;
    padding:30px;

}

.container{

    width:100%;
    max-width:520px;

}

.card{

    background:var(--bg-card);
    border:1px solid var(--border);
    border-radius:18px;

    padding:42px;

    box-shadow:0 20px 60px rgba(0,0,0,.35);

}

.logo{

    font-size:58px;
    text-align:center;
    margin-bottom:20px;

}

.title{

    text-align:center;
    margin-bottom:15px;

}

.subtitle{

    text-align:center;
    color:var(--text-secondary);
    line-height:1.8;

}

button{

    width:100%;
    height:48px;

    margin-top:30px;

    border:none;
    border-radius:10px;

    background:var(--accent);

    color:white;

    font-size:15px;
    font-weight:600;

    cursor:pointer;

}

button:hover{

    filter:brightness(1.08);

}

.footer{

    margin-top:25px;

    text-align:center;

    color:#64748b;

    font-size:13px;

}
"""

    def _script(self, correo):

        return f"""
function cerrar() {{

    if(window.opener) {{

        window.opener.postMessage({{

            event: "oauth",
            ok: true,
            correo: "{correo}"

        }}, "*");

    }}

    window.close();

}}

setTimeout(cerrar, 1200);
"""

    def _page(
        self,
        titulo,
        icono,
        mensaje,
        boton,
        script=""
    ):

        return f"""
<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="utf-8">

<title>{titulo}</title>

<style>

{self.style}

</style>

</head>

<body>

<div class="container">

    <div class="card">

        <div class="logo">{icono}</div>

        <h2 class="title">

            {titulo}

        </h2>

        <p class="subtitle">

            {mensaje}

        </p>

        <button onclick="{boton}">

            Continuar

        </button>

        <div class="footer">

            APSY ERP

        </div>

    </div>

</div>

<script>

{script}

</script>

</body>

</html>
"""

    # ==========================================
    # OK
    # ==========================================

    def ok(self, correo):

        mensaje = f"""
La cuenta <b>{correo}</b><br><br>
fue autorizada correctamente.<br><br>

Esta ventana se cerrará automáticamente.
"""

        return HTMLResponse(

            self._page(

                titulo="Cuenta conectada",

                icono="✅",

                mensaje=mensaje,

                boton="cerrar()",

                script=self._script(correo)

            )

        )

    # ==========================================
    # ERROR
    # ==========================================

    def error(self, mensaje="No fue posible conectar la cuenta."):

        return HTMLResponse(

            self._page(

                titulo="Error de conexión",

                icono="❌",

                mensaje=mensaje,

                boton="window.close()"

            )

        )