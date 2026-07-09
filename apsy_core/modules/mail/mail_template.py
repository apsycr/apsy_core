def render_template(
    titulo,
    mensaje,
    boton_texto=None,
    boton_url=None,
    footer="APSY ERP"
):

    boton = ""

    if boton_texto and boton_url:
        boton = f"""
        <div style="text-align:center;margin:30px 0;">
            <a href="{boton_url}"
               style="
               background:#2563eb;
               color:white;
               padding:14px 25px;
               border-radius:8px;
               text-decoration:none;
               font-weight:600;
               display:inline-block;">
                {boton_texto}
            </a>
        </div>
        """


    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

</head>

<body style="
margin:0;
padding:0;
background:#0f1115;
font-family:'Segoe UI',Arial,sans-serif;
color:#ffffff;
">


<table width="100%" 
       cellpadding="0" 
       cellspacing="0"
       style="padding:40px 0;background:#0f1115;">

<tr>
<td align="center">


<table width="600"
       cellpadding="0"
       cellspacing="0"
       style="
       background:#171a21;
       border-radius:14px;
       overflow:hidden;
       border:1px solid #1f2937;
       ">


<tr>

<td style="
padding:30px;
text-align:center;
background:#111827;
">


<h1 style="
margin:0;
font-size:28px;
color:#ffffff;
">

APSY

</h1>


<p style="
margin-top:8px;
color:#9ca3af;
font-size:14px;
">

Sistema Empresarial

</p>


</td>

</tr>



<tr>

<td style="
padding:35px;
">


<h2 style="
color:#ffffff;
font-size:22px;
">

{titulo}

</h2>


<p style="
color:#d1d5db;
font-size:16px;
line-height:1.6;
">

{mensaje}

</p>


{boton}


</td>

</tr>



<tr>

<td style="
padding:20px;
text-align:center;
background:#111827;
color:#9ca3af;
font-size:12px;
">

© {footer}

<br>

Este correo fue generado automáticamente.

</td>

</tr>


</table>


</td>
</tr>


</table>


</body>
</html>
"""