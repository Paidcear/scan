from fastapi import FastAPI
from datetime import datetime
import json
import os
from util import correo_venta, correo_devolucion

app = FastAPI()

RUTA_PRODUCTOS = "productos.json"
RUTA_ADICIONALES = "adicionales.json"

# ------------------ utilidades ------------------

def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def buscar_producto(codigo, productos):
    for p in productos:
        if p["codigo"] == codigo:
            return p
    return None

# ------------------ SCAN VENTA ------------------

@app.post("/scan/{codigo}")
def registrar_scan(codigo: str):

    productos = cargar_json(RUTA_PRODUCTOS)
    adicionales = cargar_json(RUTA_ADICIONALES)

    producto = buscar_producto(codigo, productos)

    if not producto:
        return {"error": "producto no encontrado"}

    nuevo = {
        "codigo": producto["codigo"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "fecha": datetime.now().strftime("%Y-%m-%d")
    }

    adicionales.append(nuevo)
    guardar_json(RUTA_ADICIONALES, adicionales)

    total = sum(p["precio"] for p in adicionales)

    # 🔔 correo automático
    correo_venta(
        numero_venta=len(adicionales),
        producto_actual=producto,
        total_venta=producto["precio"],
        historial_ventas=adicionales,
        historial_devoluciones=[]
    )


    return {
        "ok": True,
        "producto": producto["nombre"],
        "total": total
    }

# ------------------ SCAN DEVOLUCIÓN ------------------

@app.post("/devolver/{codigo}")
def devolver_producto(codigo: str):

    adicionales = cargar_json(RUTA_ADICIONALES)

    for i in range(len(adicionales)-1, -1, -1):
        if adicionales[i]["codigo"] == codigo:
            producto = adicionales.pop(i)
            guardar_json(RUTA_ADICIONALES, adicionales)

            correo_devolucion(
                numero_devolucion=len(devoluciones),
                producto_actual=producto,
                total_devuelto=producto["precio"],
                historial_ventas=adicionales,
                historial_devoluciones=devoluciones
            )


            return {"ok": True, "devuelto": producto["nombre"]}

    return {"error": "producto no encontrado"}
