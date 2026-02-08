import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import streamlit as st

# -------------------------------------------------
# Cargar configuración desde secrets.py
# -------------------------------------------------
EMAIL_USER = st.secrets["EMAIL"]["USER"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["PASSWORD"]
EMAIL_DESTINO = st.secrets["EMAIL"]["DESTINO"]


# -------------------------------------------------
# Envío de correo
# -------------------------------------------------
def enviar_correo(asunto, html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(EMAIL_DESTINO)
    msg["Subject"] = asunto

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_DESTINO, msg.as_string())
    except Exception as e:
        st.error(f"Error enviando correo: {e}")


# -------------------------------------------------
# HTML helpers
# -------------------------------------------------
def tabla_html(registros, titulo):
    if not registros:
        return f"<p><b>{titulo}:</b> Sin registros</p>"

    filas = ""
    total = 0

    for i, r in enumerate(registros, start=1):
        precio = r.get("precio", 0)
        total += precio

        filas += f"""
        <tr>
            <td>{i}</td>
            <td>{r['codigo']}</td>
            <td>{r['nombre']}</td>
            <td>${precio:.2f}</td>
            <td>{r['fecha']}</td>
        </tr>
        """

    return f"""
    <h4>{titulo}</h4>
    <table border="1" cellspacing="0" cellpadding="6"
           style="border-collapse:collapse;width:100%">
        <tr style="background:#f0f0f0">
            <th>#</th>
            <th>Código</th>
            <th>Producto</th>
            <th>Precio</th>
            <th>Fecha</th>
        </tr>
        {filas}
    </table>

    <p style="text-align:right;font-size:14px;margin-top:6px">
        <b>Total {titulo.lower()}:</b> ${total:.2f}
    </p>
    """


# -------------------------------------------------
# Generar correo de VENTA
# -------------------------------------------------
def correo_venta(
    numero_venta,
    producto_actual,
    total_venta,
    historial_ventas,
    historial_devoluciones
):
    fecha = datetime.now().strftime("%d/%m/%Y")

    asunto = f"VENTA {numero_venta} - ${total_venta:.2f}"

    html = f"""
    <html>
    <body style="font-family:Arial">
        <h2 style="color:#46B52A">
            VENTA {numero_venta} - Total ${total_venta:.2f}
        </h2>

        <p><b>Fecha:</b> {fecha}</p>

        <hr>

        <h3>Producto escaneado</h3>
        <p>
            <b>Código:</b> {producto_actual['codigo']}<br>
            <b>Nombre:</b> {producto_actual['nombre']}<br>
            <b>Precio:</b> ${producto_actual['precio']:.2f}
        </p>

        <hr>

        {tabla_html(historial_ventas, "Historial de ventas")}
        <br>
        {tabla_html(historial_devoluciones, "Historial de devoluciones")}
    </body>
    </html>
    """

    enviar_correo(asunto, html)


# -------------------------------------------------
# Generar correo de DEVOLUCIÓN
# -------------------------------------------------
def correo_devolucion(
    numero_devolucion,
    producto_actual,
    total_devuelto,
    historial_ventas,
    historial_devoluciones
):
    fecha = datetime.now().strftime("%d/%m/%Y")

    asunto = f"DEVOLUCIÓN {numero_devolucion} - ${total_devuelto:.2f}"

    html = f"""
    <html>
    <body style="font-family:Arial">
        <h2 style="color:#C0392B">
            DEVOLUCIÓN {numero_devolucion} - Total ${total_devuelto:.2f}
        </h2>

        <p><b>Fecha:</b> {fecha}</p>

        <hr>

        <h3>Producto devuelto</h3>
        <p>
            <b>Código:</b> {producto_actual['codigo']}<br>
            <b>Nombre:</b> {producto_actual['nombre']}<br>
            <b>Precio:</b> ${producto_actual['precio']:.2f}
        </p>

        <hr>

        {tabla_html(historial_ventas, "Historial de ventas")}
        <br>
        {tabla_html(historial_devoluciones, "Historial de devoluciones")}
    </body>
    </html>
    """

    enviar_correo(asunto, html)
