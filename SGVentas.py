import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from util import correo_venta, correo_devolucion

st.set_page_config(
    page_title="SGVentas",
    page_icon="logo.png",
    layout="wide"
)

# ------------------ Utilidades ------------------
RUTA_PRODUCTOS = "productos.json"
RUTA_VENTAS = "ventas.json"
RUTA_INVENTARIO = "inventario.json" 

def cargar_datos(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_datos(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# ------------------ Inventarios / adicionales ------------------
RUTA_ADICIONALES = "adicionales.json"

def cargar_adicionales(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_adicionales(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# Inicializar lista de adicionales
if "adicionales" not in st.session_state:
    st.session_state.adicionales = cargar_adicionales(RUTA_ADICIONALES)

adicionales = st.session_state.adicionales

total_adicionales = sum(a["precio"] for a in st.session_state.adicionales)


# ------------------ Inicialización ------------------
if "carrito" not in st.session_state:
    st.session_state.carrito = []

if "form_estado" not in st.session_state:
    st.session_state.form_estado = {
        "codigo": "",
        "nombre": "",
        "precio": 0.0
    }

if "sound_id" not in st.session_state:
    st.session_state.sound_id = 0

sound_placeholder = st.empty()


if "historial_devoluciones" not in st.session_state:
    st.session_state.historial_devoluciones = []

#adicionales------------------------------------------
def buscar_producto_por_codigo(codigo, productos):
    for p in productos:
        if p["codigo"] == codigo:
            return p
    return None

def registrar_adicional():
    codigo = st.session_state.scan_codigo.strip()

    if not codigo:
        return

    producto = buscar_producto_por_codigo(codigo, productos)

    if producto:
        nuevo = {
            "codigo": producto["codigo"],
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "fecha": datetime.now().strftime("%Y-%m-%d")
        }

        st.session_state.adicionales.append(nuevo)
        guardar_adicionales(RUTA_ADICIONALES, st.session_state.adicionales)

        # 🔔 CORREO VENTA (AQUÍ)
        total_actual = sum(a["precio"] for a in st.session_state.adicionales)

        correo_venta(
            numero_venta=len(st.session_state.adicionales),
            producto_actual=nuevo,
            total_venta=total_actual,
            historial_ventas=st.session_state.adicionales,
            historial_devoluciones=[]  # por ahora vacío
        )

        sonido_ok()  # 🔊 siempre suena

    else:
        sonido_error()  # 🔊 siempre suena
        st.warning(f"⚠️ El código {codigo} no existe en el sistema")

    st.session_state.scan_codigo = ""



def sonido_ok():
    st.session_state.sound_id += 1
    sound_placeholder.empty()
    components.html(
        f"""
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/cartoon/wood_plank_flicks.ogg?{st.session_state.sound_id}">
        </audio>
        """,
        height=0
    )


def sonido_error():
    st.session_state.sound_id += 1
    sound_placeholder.empty()
    components.html(
        f"""
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/cartoon/clang_and_wobble.ogg?{st.session_state.sound_id}">
        </audio>
        """,
        height=0
    )

def eliminar_adicional():
    codigo = st.session_state.scan_devolucion.strip()

    if not codigo:
        return

    adicionales = st.session_state.adicionales

    for i in range(len(adicionales) - 1, -1, -1):
        if adicionales[i]["codigo"] == codigo:
            producto = adicionales.pop(i)
            guardar_adicionales(RUTA_ADICIONALES, adicionales)

            # ✅ GUARDAR DEVOLUCIÓN EN HISTORIAL
            st.session_state.historial_devoluciones.append(producto)

            # 🔔 CORREO DEVOLUCIÓN
            correo_devolucion(
                numero_devolucion=len(st.session_state.historial_devoluciones),
                producto_actual=producto,
                total_devuelto=producto["precio"],
                historial_ventas=adicionales,
                historial_devoluciones=st.session_state.historial_devoluciones
            )
            break
    else:
        st.sidebar.warning("⚠️ Producto no encontrado en adicionales")

    st.session_state.scan_devolucion = ""


productos = cargar_datos(RUTA_PRODUCTOS)
ventas = cargar_datos(RUTA_VENTAS)
inventario = cargar_datos(RUTA_INVENTARIO)

# ------------------ Sidebar ------------------
#st.sidebar.title("Sistemas de Gestión de Ventas")
opcion = st.sidebar.selectbox("Menú", [
    "Adicionales",    
    "Punto de venta",
    "Catálogo de productos",
    "Inventario",  
    "Registros del día"
])


# ------------------ Catálogo ------------------
if opcion == "Catálogo de productos":

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Registrar / Consultar")

    # Formulario solo para el código de barras
    with st.sidebar.form("form_codigo", clear_on_submit=True):
        codigo = st.text_input("Código de barras 🟢", key="codigo_input")
        submit_codigo = st.form_submit_button("Registro manual")

    if submit_codigo:
        if not codigo:
            st.sidebar.error("Debe ingresar un código de barras válido.")
        else:
            st.session_state["codigo_value"] = codigo
            st.rerun()

    # Inyectar JS para enfocar automáticamente el campo
    components.html(
        """
        <script>
        setTimeout(function() {
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                    input.focus();
                    break;
                }
            }
        }, 100);
        </script>
        """,
        height=0
    )

    # Formulario para nombre y precio del producto
    with st.sidebar.form("form_producto", clear_on_submit=True):
        nombre = st.text_input("Nombre del producto 🟢")
        precio = st.text_input("Precio")
        submitted = st.form_submit_button("Agregar producto")

    if submitted:
        try:
            precio_float = float(precio)
            codigo_val = st.session_state.get("codigo_value", "").strip()
            if not codigo_val or not nombre or precio_float <= 0:
                st.sidebar.error("Debe completar todos los campos obligatorios.")
            elif any(str(p["codigo"]).strip() == codigo_val for p in productos):
                st.sidebar.error("El código de barras ya está registrado.")
            else:
                productos.append({
                    "codigo": codigo_val,
                    "nombre": nombre,
                    "precio": precio_float
                })
                guardar_datos(RUTA_PRODUCTOS, productos)
                st.sidebar.success("Producto agregado correctamente.")
                st.session_state["codigo_value"] = ""
                st.rerun()
        except ValueError:
            st.sidebar.error("El precio debe ser un número válido.")


    # --- Checkbox importar CSV ---
    importar_csv = st.sidebar.checkbox("Importar desde CSV")

    if importar_csv:
        archivo_csv = st.sidebar.file_uploader("Selecciona un archivo CSV", type=["csv"], key="archivo_csv")
        if archivo_csv is not None:
            try:
                df_importado = pd.read_csv(archivo_csv)
                columnas_requeridas = {"codigo", "nombre", "precio"}
                if not columnas_requeridas.issubset(df_importado.columns):
                    st.sidebar.error("El archivo debe contener las columnas: codigo, nombre y precio.")
                else:
                    df_mostrado = df_importado.copy()
                    df_mostrado.index = range(1, len(df_mostrado) + 1)
                    st.subheader("Vista previa del catálogo importado")
                    st.dataframe(df_mostrado, use_container_width=True)

                    confirmar = st.button("Importar datos")
                    if confirmar:
                        nuevos_productos = df_importado.to_dict(orient="records")
                        codigos_existentes = {p["codigo"] for p in productos}
                        nuevos_sin_duplicados = [p for p in nuevos_productos if p["codigo"] not in codigos_existentes]

                        if nuevos_sin_duplicados:
                            productos.extend(nuevos_sin_duplicados)
                            guardar_datos(RUTA_PRODUCTOS, productos)
                            st.success(f"Se han importado {len(nuevos_sin_duplicados)} productos nuevos correctamente.")
                            st.rerun()
                        else:
                            st.info("Todos los productos ya existen en el catálogo. No se importó ningún registro.")
            except Exception as e:
                st.sidebar.error(f"Error al leer el archivo CSV: {e}")

    # --- Checkbox gestionar adicionales ---
    gestionar_adicionales = st.sidebar.checkbox("Gestionar adicionales")
    if gestionar_adicionales:
        with st.sidebar.form("form_adicionales", clear_on_submit=True):
            nombre_adicional = st.text_input("Nombre del adicional")
            precio_adicional = st.text_input("Precio del adicional")
            submitted_adicional = st.form_submit_button("Agregar adicional")

        if submitted_adicional:
            try:
                precio_float = float(precio_adicional)
                if not nombre_adicional or precio_float <= 0:
                    st.sidebar.error("Debe completar todos los campos del adicional correctamente.")
                else:
                    adicionales.append({
                        "nombre": nombre_adicional,
                        "precio": precio_float
                    })
                    guardar_datos(RUTA_ADICIONALES, adicionales)
                    st.sidebar.success(f"Adicional '{nombre_adicional}' agregado correctamente.")
                    st.rerun()
            except ValueError:
                st.sidebar.error("El precio debe ser un número válido.")

    # ------------------ Columna de productos registrados ------------------
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Productos registrados")
        if productos:
            df = pd.DataFrame(productos)
            df.set_index("codigo", inplace=True)
            df["precio"] = df["precio"].astype(float)
            df_styled = df.copy()
            df_styled["precio"] = df_styled["precio"].map("${:,.2f}".format)

            filtro = st.text_input("Buscar producto")
            codigo_actual = st.session_state.get("codigo_value", "")

            def resaltar_codigo(row):
                if str(row.name).strip() == str(codigo_actual).strip():
                    return ["background-color: #088602"] * len(row)
                return [""] * len(row)

            if filtro:
                df_filtrado = df_styled[df_styled["nombre"].str.contains(filtro, case=False, na=False)]
                df_filtrado = df_filtrado.style.apply(resaltar_codigo, axis=1)
                st.write(df_filtrado, use_container_width=True)
            else:
                df_formateado = df_styled.style.apply(resaltar_codigo, axis=1)
                st.write(df_formateado)
        else:
            st.info("No hay productos registrados.")

    with col2:
        st.markdown("### Editar / Eliminar producto")
        codigo_edicion = st.session_state.get("codigo_input", "").strip()
        producto_sel_idx = next(
            (i for i, p in enumerate(productos) if str(p.get("codigo", "")).strip() == codigo_edicion),
            None
        )

        if producto_sel_idx is not None:
            producto_sel = productos[producto_sel_idx]
            nuevo_nombre = st.text_input("Nuevo nombre", value=producto_sel["nombre"], key="edit_nombre")
            nuevo_precio = st.text_input("Nuevo precio", value=str(producto_sel["precio"]), key="edit_precio")

            col1_edit, col2_edit, col3_edit, col4_edit = st.columns(4)
            with col1_edit:
                if st.button("Guardar cambios"):
                    try:
                        productos[producto_sel_idx]["nombre"] = nuevo_nombre
                        productos[producto_sel_idx]["precio"] = float(nuevo_precio)
                        guardar_datos(RUTA_PRODUCTOS, productos)
                        st.success("Producto actualizado correctamente.")
                        st.rerun()
                    except ValueError:
                        st.error("El precio debe ser un número válido.")
            with col2_edit:
                if st.button("Eliminar producto"):
                    del productos[producto_sel_idx]
                    guardar_datos(RUTA_PRODUCTOS, productos)
                    st.success("Producto eliminado correctamente.")
                    st.rerun()
                    # JS para enfocar automáticamente
                    components.html(
                        """
                        <script>
                        setTimeout(function() {
                            const inputs = window.parent.document.querySelectorAll('input');
                            for (let input of inputs) {
                                if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                    input.focus();
                                    break;
                                }
                            }
                        }, 100);
                        </script>
                        """,
                        height=0
                    )
        else:
            if codigo_edicion:
                st.info("Para modificar o eliminar, primero asegúrate de registrar el producto o escanear un código válido.")

                # Inyectar JS para enfocar automáticamente el campo
                components.html(
                    """
                    <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.placeholder === "Nombre del producto 🟢" || input.ariaLabel === "Nombre del producto 🟢") {
                                input.focus();
                                break;
                            }
                        }
                    }, 100);
                    </script>
                    """,
                    height=0
                )


# ------------------ Punto de Venta ------------------
elif opcion == "Punto de venta":
    sub_opcion = st.sidebar.radio("Opciones", ["Ventas", "Gastos", "Corte de caja"])

    if sub_opcion == "Ventas":

        col1, col2 = st.columns(2)
        with col1:

            if not productos:
                st.warning("No hay productos disponibles. Agrega productos primero.")
            else:
                st.subheader("Escaneo de productos")

                # Cargar adicionales en session_state
                RUTA_ADICIONALES = "adicionales.json"
                if "adicionales" not in st.session_state:
                    if os.path.exists(RUTA_ADICIONALES):
                        with open(RUTA_ADICIONALES, "r", encoding="utf-8") as f:
                            st.session_state.adicionales = json.load(f)
                    else:
                        st.session_state.adicionales = []

                # Checkbox de adicionales
                activar_adicionales = st.sidebar.checkbox("Adicionales", key="activar_adicionales")

                # Formulario principal
                with st.form("form_codigo_barra", clear_on_submit=True):
                    codigo_input = st.text_input("Código de barras 🟢", key="codigo_barra")
                    cantidad_input = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.25)
                    monto_manual = st.text_input("Monto manual 🟢")

                    # Mostrar adicionales si el checkbox está activo
                    adicionales_inputs = []
                    subtotal_adicionales = 0
                    if activar_adicionales and st.session_state.adicionales:
                        st.markdown("### Selecciona adicionales")
                        col_ad1, col_ad2 = st.columns(2)
                        for i, ad in enumerate(st.session_state.adicionales):
                            col = col_ad1 if i % 2 == 0 else col_ad2
                            with col:
                                key_input = f"adicional_{ad.get('codigo', i)}"
                                cantidad_ad = st.number_input(
                                    f"{ad['nombre']} (${ad['precio']:.2f})",
                                    min_value=0,
                                    value=0,
                                    step=1,
                                    key=key_input
                                )
                                if cantidad_ad > 0:
                                    subtotal_adicionales += ad["precio"] * cantidad_ad
                                    adicionales_inputs.append({
                                        "codigo": ad.get("codigo", f"AD{i+1}"),
                                        "nombre": ad["nombre"],
                                        "precio": ad["precio"],
                                        "cantidad": cantidad_ad
                                    })

                    submitted = st.form_submit_button("Agregar")

                    # JS para enfocar automáticamente
                    components.html(
                        """
                        <script>
                        setTimeout(function() {
                            const inputs = window.parent.document.querySelectorAll('input');
                            for (let input of inputs) {
                                if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                                    input.focus();
                                    break;
                                }
                            }
                        }, 100);
                        </script>
                        """,
                        height=0
                    )

                # Procesamiento del formulario
                if submitted:
                    # Producto por código
                    if codigo_input:
                        producto = next((p for p in productos if p["codigo"] == codigo_input), None)
                        if producto:
                            st.session_state.carrito.append({
                                "codigo": producto["codigo"],
                                "nombre": producto["nombre"],
                                "precio": producto["precio"],
                                "cantidad": cantidad_input
                            })
                        else:
                            st.error(f"Código no encontrado: {codigo_input}")

                    # Monto manual
                    if monto_manual:
                        try:
                            monto_valor = float(monto_manual)
                            if monto_valor > 0:
                                st.session_state.carrito.append({
                                    "codigo": "INGRESO",
                                    "nombre": "VARIOS",
                                    "precio": monto_valor,
                                    "cantidad": 1
                                })
                            else:
                                st.error("El monto manual debe ser mayor que cero.")
                        except ValueError:
                            st.error("Monto manual inválido, ingresa un número válido.")

                    # Adicionales
                    if adicionales_inputs:
                        st.session_state.carrito.extend(adicionales_inputs)

                    st.rerun()

        # ---------------- Columna 2: Carrito ----------------
        with col2:
            st.subheader("Productos escaneados")

            if st.session_state.carrito:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                df_carrito["subtotal"] = df_carrito["precio"] * df_carrito["cantidad"]

                # Formato de moneda
                df_vista = df_carrito.copy()
                df_vista["precio"] = df_vista["precio"].map("${:,.2f}".format)
                df_vista["cantidad"] = df_vista["cantidad"].map("{:,.2f}".format)
                df_vista["subtotal"] = df_vista["subtotal"].map("${:,.2f}".format)

                # Índice desde 1
                df_vista.index = range(1, len(df_vista) + 1)

                st.dataframe(df_vista, use_container_width=True)

                # Eliminar productos del carrito
                opciones = []
                for i, item in enumerate(st.session_state.carrito):
                    subtotal = item["precio"] * item["cantidad"]
                    etiqueta = f"{item['nombre']} – ${subtotal:,.2f}"
                    opciones.append((etiqueta, i))
                if opciones:
                    etiquetas_visibles = [et[0] for et in opciones]
                    seleccion = st.selectbox("Eliminar producto", etiquetas_visibles)
                    idx_a_eliminar = dict(opciones)[seleccion]
                    if st.button("Eliminar del carrito"):
                        eliminado = st.session_state.carrito[idx_a_eliminar]["nombre"]
                        del st.session_state.carrito[idx_a_eliminar]
                        st.success(f"Producto '{eliminado}' eliminado.")
                        st.rerun()

                # Total general
                total = df_carrito["subtotal"].sum()
                st.sidebar.markdown("---")
                st.sidebar.title("Total de la compra")
                st.sidebar.markdown(f"**Subtotal:** ${total:,.2f}")
                st.sidebar.markdown(
                    f"<div style='font-size: 80px; font-weight: bold; color: #2E8B57;'>${total:,.2f}</div>",
                    unsafe_allow_html=True
                )

                # Botón para finalizar venta
                if st.sidebar.button("**Registrar venta**"):
                    ventas.append({
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "items": st.session_state.carrito,
                        "total": total
                    })
                    guardar_datos(RUTA_VENTAS, ventas)
                    st.session_state.carrito = []
                    st.success("Venta registrada correctamente.")
                    st.rerun()
            else:
                st.info("El carrito está vacío.")

            # JS para enfocar automáticamente
            components.html(
                """
                <script>
                setTimeout(function() {
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let input of inputs) {
                        if (input.placeholder === "Código de barras 🟢" || input.ariaLabel === "Código de barras 🟢") {
                            input.focus();
                            break;
                        }
                    }
                }, 100);
                </script>
                """,
                height=0
            )

#--------------- Gastos ----------------------------
    elif sub_opcion == "Gastos":
        accion = st.sidebar.selectbox("Acciones", ["Agregar", "Proveedores"])
        if accion == "Agregar":

            col1, col2 = st.columns(2)

            if "gastos" not in st.session_state:
                st.session_state.gastos = cargar_datos("gastos.json")

            if "proveedores" not in st.session_state:
                st.session_state.proveedores = cargar_datos("proveedores.json")

            proveedores_disponibles = [p["nombre"] for p in st.session_state.proveedores]

            with col1:
                st.subheader("Registrar gasto")

                with st.form("form_gasto", clear_on_submit=True):
                    proveedor = st.selectbox("Proveedor", opciones := proveedores_disponibles)
                    co1, co2 = st.columns(2)
                    with co1:
                        monto = st.text_input("Monto")
                    with co2:
                        fecha = st.date_input("Fecha", value=datetime.now())
                    submitted = st.form_submit_button("Registrar gasto")

                if submitted:
                    try:
                        monto_float = float(monto)
                        if not proveedor or monto_float <= 0:
                            st.error("Por favor selecciona un proveedor y un monto válido.")
                        else:
                            nuevo_gasto = {
                                "proveedor": proveedor,
                                "monto": monto_float,
                                "fecha": fecha.strftime("%Y-%m-%d")
                            }
                            st.session_state.gastos.append(nuevo_gasto)
                            guardar_datos("gastos.json", st.session_state.gastos)
                            st.success("Gasto registrado correctamente.")
                            st.rerun()
                    except ValueError:
                        st.error("El monto debe ser un número válido.")

            with col2:
                st.subheader("Editar / Eliminar gasto")

                if st.session_state.gastos:
                    opciones = []
                    for i, g in enumerate(st.session_state.gastos):
                        etiqueta = f"{g['fecha']} – {g['proveedor']} – ${g['monto']:,.2f}"
                        opciones.append((etiqueta, i))

                    etiquetas_visibles = [et[0] for et in opciones]
                    seleccion = st.selectbox("Selecciona un gasto", etiquetas_visibles, label_visibility="collapsed")
                    idx_seleccionado = dict(opciones)[seleccion]
                    gasto = st.session_state.gastos[idx_seleccionado]

                    proveedor_edit = st.selectbox("Proveedor", proveedores_disponibles, index=proveedores_disponibles.index(gasto["proveedor"]))
                    monto_edit = st.text_input("Monto", value=str(gasto["monto"]))
                    fecha_edit = st.date_input("Fecha", value=datetime.strptime(gasto["fecha"], "%Y-%m-%d"))

                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        if st.button("Actualizar gasto"):
                            try:
                                monto_float = float(monto_edit)
                                gasto["proveedor"] = proveedor_edit
                                gasto["monto"] = monto_float
                                gasto["fecha"] = fecha_edit.strftime("%Y-%m-%d")
                                guardar_datos("gastos.json", st.session_state.gastos)
                                st.success("Gasto actualizado correctamente.")
                                st.rerun()
                            except ValueError:
                                st.error("El monto debe ser un número válido.")

                    with col_ed2:
                        if st.button("Eliminar gasto"):
                            eliminado = st.session_state.gastos[idx_seleccionado]
                            del st.session_state.gastos[idx_seleccionado]
                            guardar_datos("gastos.json", st.session_state.gastos)
                            st.success(f"Gasto del proveedor '{eliminado['proveedor']}' eliminado.")
                            st.rerun()
                else:
                    st.info("No hay gastos registrados.")


# ----------------------
        if accion == "Proveedores":
            

            if "proveedores" not in st.session_state:
                st.session_state.proveedores = cargar_datos("proveedores.json")

            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

            # --- Registro desde sidebar ---
            st.sidebar.markdown("### Registrar proveedor")
            with st.sidebar.form("form_proveedor", clear_on_submit=True):
                nombre = st.text_input("Nombre del proveedor")
                dias = st.multiselect("Días de entrega", options=dias_semana)
                submitted = st.form_submit_button("Registrar")

            if submitted:
                if not nombre or not dias:
                    st.sidebar.error("Debes ingresar el nombre y al menos un día.")
                elif any(p["nombre"].lower() == nombre.lower() for p in st.session_state.proveedores):
                    st.sidebar.error("Este proveedor ya está registrado.")
                else:
                    st.session_state.proveedores.append({
                        "nombre": nombre,
                        "dia": dias  # Se guarda como lista
                    })
                    guardar_datos("proveedores.json", st.session_state.proveedores)
                    st.sidebar.success("Proveedor registrado correctamente.")
                    st.rerun()

            # --- Panel principal dividido en 2 columnas ---
            col1, col2 = st.columns([1, 1])

            # Columna 1: Mostrar proveedores con filtros en columnas
            with col1:
                st.markdown("### Lista de proveedores")

                if st.session_state.proveedores:
                    df_prov = pd.DataFrame(st.session_state.proveedores)

                    # Asegurar que la columna 'dia' sea lista
                    df_prov["dia"] = df_prov["dia"].apply(lambda d: d if isinstance(d, list) else [])

                    # Controles de filtros en columnas
                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        nombre_filtro = st.text_input("Buscar por nombre", key="filtro_nombre")

                    with col_f2:
                        dias_filtro = st.multiselect("Filtrar por día", dias_semana, key="filtro_dias")

                    # Aplicar filtros
                    if nombre_filtro:
                        df_prov = df_prov[df_prov["nombre"].str.contains(nombre_filtro, case=False, na=False)]

                    if dias_filtro:
                        df_prov = df_prov[df_prov["dia"].apply(lambda dias: any(d in dias for d in dias_filtro))]

                    # Convertir días a texto para mostrar
                    df_prov["dia_str"] = df_prov["dia"].apply(lambda d: ", ".join(d))
                    df_prov.index = range(1, len(df_prov) + 1)

                    # Solo columnas que queremos mostrar
                    df_mostrar = df_prov[["nombre", "dia_str"]]

                    def resaltar_nombre(row):
                        color_fila = ""
                        dias = df_prov.loc[row.name, "dia"]
                        if not isinstance(dias, list):
                            dias = []

                        if dias_filtro and any(d in dias for d in dias_filtro):
                            color_fila = "background-color: #90EE9055"  # Verde suave

                        # Crear una lista vacía para todas las columnas (sin color)
                        colores = [""] * len(row)
                        # Buscar índice de la columna "nombre" para pintar solo esa celda
                        idx_nombre = df_mostrar.columns.get_loc("nombre")
                        colores[idx_nombre] = color_fila
                        return colores

                    df_estilado = df_mostrar.style.apply(resaltar_nombre, axis=1)

                    st.dataframe(df_estilado, use_container_width=True)

                else:
                    st.info("No hay proveedores registrados.")


            # Columna 2: Editar o eliminar
            with col2:
                st.markdown("### Modificar/Eliminar proveedor")

                if st.session_state.proveedores:
                    nombres = [p["nombre"] for p in st.session_state.proveedores]
                    seleccion = st.selectbox("Selecciona un proveedor", nombres)

                    proveedor = next((p for p in st.session_state.proveedores if p["nombre"] == seleccion), None)

                    if proveedor:
                        nuevo_nombre = st.text_input("Nuevo nombre", value=proveedor["nombre"], key="edit_nombre_prov")
                        nuevos_dias = st.multiselect(
                            "Nuevos días de entrega",
                            options=dias_semana,
                            default=proveedor.get("dia", []) if isinstance(proveedor.get("dia", []), list) else []
                        )

                        col_ed, col_del, col3, col4 = st.columns(4)
                        with col_ed:
                            if st.button("Guardar cambios"):
                                proveedor["nombre"] = nuevo_nombre
                                proveedor["dia"] = nuevos_dias
                                guardar_datos("proveedores.json", st.session_state.proveedores)
                                st.success("Proveedor actualizado correctamente.")
                                st.rerun()
                        with col_del:
                            if st.button("Eliminar proveedor"):
                                st.session_state.proveedores = [
                                    p for p in st.session_state.proveedores if p["nombre"] != seleccion
                                ]
                                guardar_datos("proveedores.json", st.session_state.proveedores)
                                st.success("Proveedor eliminado correctamente.")
                                st.rerun()
                else:
                    st.info("No hay proveedores para editar o eliminar.")


#--------------- Corte de caja ----------------------------
    elif sub_opcion == "Corte de caja":
        st.title("Corte de Caja")
        if ventas:
            df_hist = pd.DataFrame([
                {
                    "fecha": v["fecha"],
                    "total": v["total"]
                }
                for v in ventas
            ])
            total_general = df_hist["total"].sum()
            st.dataframe(df_hist)
            st.write(f"Total de ventas: ${total_general:.2f}")
        else:
            st.info("No hay ventas registradas.")


# ------------------ Inventario ------------------
elif opcion == "Inventario":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Buscar producto y registrar entrada")

    # Formulario para filtro de producto
    with st.sidebar.form("form_filtro", clear_on_submit=True):
        filtro = st.text_input("Código o nombre del producto")
        submit_filtro = st.write(f"**{filtro}**")
        submit_filtro = st.form_submit_button("Buscar producto")
    # Inyectar JS para enfocar automáticamente el campo
    components.html(
        """
        <script>
        setTimeout(function() {
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.placeholder === "Código o nombre del producto" || input.ariaLabel === "Código o nombre del producto") {
                    input.focus();
                    break;
                }
            }
        }, 100);
        </script>
        """,
        height=0
    )   

    # Formulario para registrar cantidad
    with st.sidebar.form("form_cantidad", clear_on_submit=True):
        cantidad_str = st.text_input("Cantidad")
        submit_cantidad = st.form_submit_button("Registrar entrada")

    # Manejo de la entrada
    if submit_cantidad:
        if not filtro.strip() or not cantidad_str.strip():
            st.sidebar.error("Debe ingresar un código/nombre y una cantidad.")
        else:
            try:
                cantidad = int(cantidad_str)
                if cantidad <= 0:
                    st.sidebar.error("La cantidad debe ser mayor a 0.")
                else:
                    producto = next(
                        (p for p in productos if filtro.lower() in p["nombre"].lower() or filtro.strip() == p["codigo"]),
                        None
                    )
                    if not producto:
                        st.sidebar.error("El producto no existe en el catálogo.")
                    else:
                        # Actualizar stock en inventario
                        item = next((x for x in inventario if x["codigo"] == producto["codigo"]), None)
                        if item:
                            item["stock"] += cantidad
                        else:
                            inventario.append({"codigo": producto["codigo"], "stock": cantidad})
                        guardar_datos(RUTA_INVENTARIO, inventario)
                        # Inyectar JS para enfocar automáticamente el campo
                        components.html(
                            """
                            <script>
                            setTimeout(function() {
                                const inputs = window.parent.document.querySelectorAll('input');
                                for (let input of inputs) {
                                    if (input.placeholder === "Código o nombre del producto" || input.ariaLabel === "Código o nombre del producto") {
                                        input.focus();
                                        break;
                                    }
                                }
                            }, 100);
                            </script>
                            """,
                            height=0
                        )
                        st.sidebar.success(f"Entrada registrada para {producto['nombre']}.")
                        st.rerun()
            except ValueError:
                st.sidebar.error("La cantidad debe ser un número entero válido.")



    # ------------------ Filtrar producto para mostrar ------------------
    if filtro.strip():
        productos_mostrar = [
            p for p in productos
            if filtro.lower() in p["nombre"].lower() or filtro.strip() == p["codigo"]
        ]
    else:
        productos_mostrar = []

    # ------------------ Panel principal con 2 columnas ------------------
    col1, col2 = st.columns([3, 2])  # Ajustar ancho según prefieras

    # ---------- Columna 1: Inventario compacto ----------
    with col1:
        st.subheader("Administrar Inventario")
        if productos_mostrar:
            for prod in productos_mostrar:
                codigo = prod["codigo"]
                nombre = prod["nombre"]
                item = next((x for x in inventario if x["codigo"] == codigo), None)
                stock = item.get("stock", 0) if item else 0


                col_codigo, col_nombre, col_stock, col_acciones = st.columns([2, 2, 2, 2])

                with col_codigo:
                    st.markdown(f"**{codigo}**")
                with col_nombre:
                    st.markdown(nombre)
                with col_stock:
                    nuevo_stock = st.number_input(
                        "",
                        min_value=0,
                        value=stock,
                        step=1,
                        key=f"stock_input_{codigo}",
                        label_visibility="collapsed"
                    )
                with col_acciones:
                    if st.button("Guardar stock", key=f"save_{codigo}"):
                        if item:
                            item["stock"] = nuevo_stock
                        else:
                            inventario.append({"codigo": codigo, "stock": nuevo_stock})
                        guardar_datos(RUTA_INVENTARIO, inventario)
                        st.success(f"Stock de {codigo} actualizado a {nuevo_stock}.")
                        st.rerun()
                    # Inyectar JS para enfocar automáticamente el campo
                    components.html(
                        """
                        <script>
                        setTimeout(function() {
                            const inputs = window.parent.document.querySelectorAll('input');
                            for (let input of inputs) {
                                if (input.placeholder === "Código o nombre del producto" || input.ariaLabel === "Código o nombre del producto") {
                                    input.focus();
                                    break;
                                }
                            }
                        }, 100);
                        </script>
                        """,
                        height=0
                    )
                        #st.markdown("<hr>", unsafe_allow_html=True)
            # Inyectar JS para enfocar automáticamente el campo
            components.html(
                """
                <script>
                setTimeout(function() {
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let input of inputs) {
                        if (input.placeholder === "Cantidad" || input.ariaLabel === "Cantidad") {
                            input.focus();
                            break;
                        }
                    }
                }, 100);
                </script>
                """,
                height=0
            )

        else:
            st.info("Ingresa un código o nombre para mostrar el producto.")
           

    # ---------- Columna 2: DataFrame completo ----------
    with col2:
        st.subheader("Inventario Completo")
        # Combinar productos y stock
        data_df = []
        for p in productos:
            codigo = p["codigo"]
            nombre = p["nombre"]
            item = next((x for x in inventario if x["codigo"] == codigo), None)
            stock = item.get("stock", 0) if item else 0
            data_df.append({"Código": codigo, "Nombre": nombre, "Stock": stock})

        if data_df:
            df = pd.DataFrame(data_df)
            df.set_index("Código", inplace=True)
            st.dataframe(df, use_container_width=True)
            # Inyectar JS para enfocar automáticamente el campo
            components.html(
                """
                <script>
                setTimeout(function() {
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let input of inputs) {
                        if (input.placeholder === "Código o nombre del producto" || input.ariaLabel === "Código o nombre del producto") {
                            input.focus();
                            break;
                        }
                    }
                }, 100);
                </script>
                """,
                height=0
            )
        else:
            st.info("No hay productos en el inventario.")


# ------------------ Registro de ventas del día ------------------
elif opcion == "Registros del día":
    col1, col2 = st.columns(2)
    with col1:
        st.sidebar.title("Ventas del día")
        st.write("**Ventas**")
        if ventas:
            df_hist = pd.DataFrame([
                {
                    "fecha": v["fecha"],
                    "total": v["total"]
                }
                for v in ventas
            ])
            st.line_chart(df_hist.set_index("fecha"))
            st.write("---")
            st.write("Resúmen de ventas")

            # Clonar el DataFrame para no alterar el original
            df_vista = df_hist.copy()
            df_vista.index = range(1, len(df_vista) + 1)  # Índice desde 1

            df_vista["total"] = df_vista["total"].astype(float).map("${:,.2f}".format)
            st.dataframe(df_vista, use_container_width=True)

            # Calcular el total general normalmente
            total_general = df_hist["total"].sum()
            st.sidebar.markdown(
                        f"<div style='font-size: 50px; font-weight: bold; color: #2E8B57;'>${total_general:,.2f}</div>",    #Total general: 
                        unsafe_allow_html=True
                    )
        else:
            st.info("No hay datos disponibles.")


#---------------------------------------------
        with st.expander("Registro de Ventas"):

            if ventas:
                for venta in reversed(ventas):
                    st.markdown(f"Fecha: {venta['fecha']}")

                    # Crear DataFrame y calcular subtotal
                    df = pd.DataFrame(venta["items"])
                    df["subtotal"] = df["precio"] * df["cantidad"]

                    # Formatear columnas numéricas como moneda
                    df["precio"] = df["precio"].map("${:,.2f}".format)
                    df["subtotal"] = df["subtotal"].map("${:,.2f}".format)

                    # Ajustar índice visual desde 1
                    df.index = range(1, len(df) + 1)

                    # Mostrar tabla
                    st.dataframe(df, use_container_width=True)

                    # Mostrar total
                    st.write(f"Total: ${venta['total']:.2f}")
                    st.markdown("---")
            else:
                st.info("No hay ventas registradas.")

    with col2:
        st.sidebar.write("---")
        st.sidebar.title("Gastos del día")
        st.write("**Gastos**")

        gastos = st.session_state.get("gastos", [])

        if gastos:

            # Crear un dataframe con fecha y monto
            df_gastos = pd.DataFrame([
                {
                    "proveedor": g.get("proveedor", "N/A"),
                    #"fecha": g.get("fecha", ""),
                    "total": g.get("total", g.get("monto", 0))  # intenta total, sino monto, sino 0
                }
                for g in gastos
            ])

            # Agrupar por fecha sumando total para graficar resumen diario
            df_gastos_resumen = df_gastos.groupby("proveedor", as_index=False).sum()

            st.line_chart(df_gastos_resumen.set_index("proveedor"))
            st.write("---")
            st.write("Resúmen de gastos")

            # Clonar y preparar para mostrar
            df_gvista = df_gastos_resumen.copy()
            df_gvista.index = range(1, len(df_gvista) + 1)

            df_gvista["total"] = df_gvista["total"].astype(float).map("${:,.2f}".format)
            st.dataframe(df_gvista, use_container_width=True)

            # Total general sumando todos los montos
            #with st.sidebar.container():
            total_gastos = df_gastos["total"].sum()
            st.sidebar.markdown(
                    f"<div style='font-size: 50px; font-weight: bold; color: #B22222;'>${total_gastos:,.2f}</div>",    #Gasto total:
                unsafe_allow_html=True
            )
        else:
            st.info("No hay gastos registrados.")

        with st.expander("Registro de Gastos"):

            if gastos:
                for gasto in reversed(gastos):
                    proveedor = gasto.get("proveedor", "Sin proveedor")
                    total = gasto.get("total", gasto.get("monto", 0))   

                    st.write(f"Proveedor: **{proveedor}**")
                    st.write(f"Total: ${total:.2f}")
                    st.markdown("---")
            else:
                st.info("No hay gastos registrados.")


#---------------ADICIONALES----------------------------------

elif opcion == "Adicionales":

    st.sidebar.markdown("### Adicionales (préstamo)")
    st.sidebar.metric(
        label="Total acumulado",
        value=f"${total_adicionales:.2f}"
    )

    st.subheader("Registro de Adicionales")

    st.text_input(
        "Escanear producto",
        key="scan_codigo",
        placeholder="Escanea el código...",
        label_visibility="collapsed",
        on_change=registrar_adicional
    )

    # JS para enfocar automáticamente
    components.html(
        """
        <script>
        setTimeout(function() {
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.placeholder === "Escanear producto" || input.ariaLabel === "Escanear producto") {
                    input.focus();
                    break;
                }
            }
        }, 100);
        </script>
        """,
        height=0
    )



    #st.markdown("---")

    if st.sidebar.checkbox("Ver resumen del día"):
        if st.session_state.adicionales:
            df_resumen = pd.DataFrame(st.session_state.adicionales)

            # Reordenar columnas si quieres
            df_resumen = df_resumen[["codigo", "nombre", "precio", "fecha"]]

            # Index desde 1
            df_resumen.index = df_resumen.index + 1

            st.subheader("Historial")
            st.dataframe(
                df_resumen,
                use_container_width=True,
                hide_index=False
            )

            
            if st.sidebar.button("Restablecer registros"):
                st.session_state.adicionales = []
                guardar_adicionales(RUTA_ADICIONALES, [])
                st.sidebar.success("Registros restablecidos")
                st.rerun()
        else:
            st.sidebar.info("No hay registros para mostrar")

    #st.sidebar.markdown("### Devoluciones")

    st.sidebar.text_input(
        "Escanear para eliminar",
        key="scan_devolucion",
        placeholder="Escanear devolución",
        label_visibility="collapsed",
        on_change=eliminar_adicional
    )
