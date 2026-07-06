from fastapi.responses import HTMLResponse


class OAuthHTML:

    # ==========================================
    # OK
    # ==========================================

    def ok(
        self,
        correo: str
    ):

        html = f"""
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="utf-8">

<title>Cuenta conectada</title>

<style>
    .container{

    width:100%;
    max-width:520px;

}

.card{

    background:var(--bg-card);

    border:1px solid var(--border);

    border-radius:18px;

    padding:48px;

    box-shadow:0 15px 50px rgba(0,0,0,.45);

}

.title{

    margin-bottom:12px;

    text-align:center;

}

.subtitle{

    margin-bottom:30px;

    text-align:center;

    color:var(--text-secondary);

    line-height:1.8;

}

.logo{

    font-size:56px;

    text-align:center;

    margin-bottom:15px;

}

button{

    width:100%;

    height:48px;

    margin-top:10px;

    border:none;

    border-radius:10px;

    background:var(--accent);

    color:#fff;

    font-size:15px;

    font-weight:600;

    cursor:pointer;

    transition:.2s;

}

button:hover{

    filter:brightness(1.08);

}

.btn-secondary{

    background:#20252f;

}

.btn-secondary:hover{

    background:#2b313d;

}

button:hover{

    opacity:.92;

}

.footer{

    margin-top:25px;

    text-align:center;

    color:gray;

    font-size:13px;

}

.form-group{

    margin:22px 0;

}

.form-group label{

    display:block;

    margin-bottom:8px;

    color:var(--text-secondary);

    font-size:14px;

    font-weight:500;

}

.form-group input{

    width:100%;

    height:48px;

    padding:0 16px;

    border-radius:10px;

    border:1px solid var(--border);

    background:#11151d;

    color:var(--text-primary);

    font-size:15px;

    transition:
        border-color .2s,
        box-shadow .2s,
        background .2s;

    outline:none;

}

.form-group input::placeholder{

    color:#6b7280;

}

.form-group input:hover{

    border-color:#374151;

}

.form-group input:focus{

    border-color:var(--accent);

    box-shadow:0 0 0 3px rgba(37,99,235,.20);

}
</style>

</head>

<body>

<div class="container">

    <div class="card">

        <div class="logo">
            ✅
        </div>

        <h2 class="title">

            Cuenta conectada

        </h2>

        <p class="subtitle">

            La cuenta <b>{correo}</b><br>
            fue autorizada correctamente.

            <br><br>

            Ya puede regresar a APSY ERP.

        </p>

        <button onclick="cerrar()">

            Continuar

        </button>

        <div class="footer">

            APSY ERP

        </div>

    </div>

</div>

<script>

function cerrar(){

    if(window.opener){

        window.opener.postMessage({

            event:"oauth",

            ok:true,

            correo:"%s"

        },"*");

    }

    window.close();

}

setTimeout(cerrar,1200);

</script>

</body>

</html>
""" % correo

        return HTMLResponse(html)

    # ==========================================
    # ERROR
    # ==========================================

    def error(
        self,
        mensaje="No fue posible conectar la cuenta."
    ):

        html = f"""
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="utf-8">

<title>Error</title>

<style>
    .container{

    width:100%;
    max-width:520px;

}

.card{

    background:var(--bg-card);

    border:1px solid var(--border);

    border-radius:18px;

    padding:48px;

    box-shadow:0 15px 50px rgba(0,0,0,.45);

}

.title{

    margin-bottom:12px;

    text-align:center;

}

.subtitle{

    margin-bottom:30px;

    text-align:center;

    color:var(--text-secondary);

    line-height:1.8;

}

.logo{

    font-size:56px;

    text-align:center;

    margin-bottom:15px;

}

button{

    width:100%;

    height:48px;

    margin-top:10px;

    border:none;

    border-radius:10px;

    background:var(--accent);

    color:#fff;

    font-size:15px;

    font-weight:600;

    cursor:pointer;

    transition:.2s;

}

button:hover{

    filter:brightness(1.08);

}

.btn-secondary{

    background:#20252f;

}

.btn-secondary:hover{

    background:#2b313d;

}

button:hover{

    opacity:.92;

}

.footer{

    margin-top:25px;

    text-align:center;

    color:gray;

    font-size:13px;

}

.form-group{

    margin:22px 0;

}

.form-group label{

    display:block;

    margin-bottom:8px;

    color:var(--text-secondary);

    font-size:14px;

    font-weight:500;

}

.form-group input{

    width:100%;

    height:48px;

    padding:0 16px;

    border-radius:10px;

    border:1px solid var(--border);

    background:#11151d;

    color:var(--text-primary);

    font-size:15px;

    transition:
        border-color .2s,
        box-shadow .2s,
        background .2s;

    outline:none;

}

.form-group input::placeholder{

    color:#6b7280;

}

.form-group input:hover{

    border-color:#374151;

}

.form-group input:focus{

    border-color:var(--accent);

    box-shadow:0 0 0 3px rgba(37,99,235,.20);

}
</style>

</head>

<body>

<div class="container">

    <div class="card">

        <div class="logo">
            ❌
        </div>

        <h2 class="title">

            Error de conexión

        </h2>

        <p class="subtitle">

            {mensaje}

        </p>

        <button onclick="window.close()">

            Cerrar

        </button>

    </div>

</div>

</body>

</html>
"""

        return HTMLResponse(html)