import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")

# ===============================
# LOGO
# ===============================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=180)

st.title("📊 Inventario al 9 de junio vs Ventas de mayo al 9 de junio")

# =========================
# RUTAS
# =========================
ruta_inventario = "inventario.xlsx"
ruta_ventas = "ventas.xlsx"

if not os.path.exists(ruta_inventario) or not os.path.exists(ruta_ventas):
    st.error("Faltan archivos")
    st.stop()

# =========================
# CARGA
# =========================
@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(ruta_inventario, ruta_ventas):
    df_inv = pd.read_excel(ruta_inventario, engine="openpyxl")
    df_ven = pd.read_excel(ruta_ventas, engine="openpyxl")

    # limpiar columnas
    df_inv.columns = df_inv.columns.str.strip().str.lower().str.replace(" ", "_")
    df_ven.columns = df_ven.columns.str.strip().str.lower().str.replace(" ", "_")

    # fechas
    df_inv["fecha_ultimo_traslado"] = pd.to_datetime(df_inv["fecha_ultimo_traslado"], errors="coerce")
    df_inv["fecha_ingreso"] = pd.to_datetime(df_inv["fecha_ingreso"], errors="coerce")
    df_ven["fecha"] = pd.to_datetime(df_ven["fecha"], errors="coerce")

    # serial limpio
    df_inv["serial"] = df_inv["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()
    df_ven["serial"] = df_ven["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()

    return df_inv, df_ven


df_inv, df_ven = cargar_datos(ruta_inventario, ruta_ventas)



# =========================
# LIMPIEZA
# =========================
df_inv.columns = df_inv.columns.str.strip().str.lower().str.replace(" ", "_")
df_ven.columns = df_ven.columns.str.strip().str.lower().str.replace(" ", "_")

# =========================
# FECHAS
# =========================
df_inv["fecha_ultimo_traslado"] = pd.to_datetime(df_inv["fecha_ultimo_traslado"], errors="coerce")
df_inv["fecha_ingreso"] = pd.to_datetime(df_inv["fecha_ingreso"], errors="coerce")
df_ven["fecha"] = pd.to_datetime(df_ven["fecha"], errors="coerce")

# =========================
# SERIAL LIMPIO
# =========================
df_inv["serial"] = df_inv["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()
df_ven["serial"] = df_ven["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()

# =========================
# FILTROS
# =========================
st.sidebar.title("Filtros")

grupo = st.sidebar.multiselect("Grupo", df_inv["grupo"].unique())
marca = st.sidebar.multiselect("Marca", df_inv["marca"].unique())
sucursal = st.sidebar.multiselect("Sucursal", df_inv["sucursal"].unique())

df_inv_fil = df_inv.copy()
df_ven_fil = df_ven.copy()

if grupo:
    df_inv_fil = df_inv_fil[df_inv_fil["grupo"].isin(grupo)]

if marca:
    df_inv_fil = df_inv_fil[df_inv_fil["marca"].isin(marca)]

if sucursal:
    df_inv_fil = df_inv_fil[df_inv_fil["sucursal"].isin(sucursal)]
    df_ven_fil = df_ven_fil[df_ven_fil["sucursal"].isin(sucursal)]

inv_ref_fil = df_inv_fil.groupby(
    ["referencia"]
)["serial"].count().reset_index(name="Total_Bodega_Sucursal")



# =========================
# PROTECCIÓN OFICINA PRINCIPAL
# =========================
if sucursal and "Oficina Principal" in sucursal:

    if "auth_principal" not in st.session_state:
        st.session_state["auth_principal"] = False

    if not st.session_state["auth_principal"]:
        password = st.sidebar.text_input(
            "🔒 Contraseña Oficina Principal",
            type="password"
        )

        if password == "1234":
            st.session_state["auth_principal"] = True
        else:
            st.warning("Acceso restringido a Oficina Principal")
            st.stop()

# reset si quita la sucursal
if not sucursal or "Oficina Principal" not in sucursal:
    st.session_state["auth_principal"] = False




# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventario", "📆 Prestamos sub", "📊 Resumen", "📥 Descarga de Archivos"])

# =========================
# TAB SEMAFORO
# =========================
with tab1:
    st.subheader("📦 Inventario")

    # =========================
    # FILTRO POR REFERENCIA
    # =========================
    lista_ref = sorted(df_inv_fil["referencia"].dropna().unique())

    ref_select = st.selectbox(
        "Selecciona una referencia",
        options=["Todas"] + lista_ref
    )

    if ref_select != "Todas":
        df_inv_tab1 = df_inv_fil[df_inv_fil["referencia"] == ref_select].copy()
    else:
        df_inv_tab1 = df_inv_fil.copy(deep=True)

    # =========================
    # SEMÁFORO POR MES (CORREGIDO Y SEGURO)
    # =========================

    hoy = datetime.today()
    mes_actual = pd.Period(hoy, freq="M")
    mes_1 = mes_actual - 1
    mes_2 = mes_actual - 2

    # 🔒 validar que la columna exista
    if "fecha_ultimo_traslado" in df_inv_tab1.columns:

        # convertir a datetime seguro
        df_inv_tab1["fecha_ultimo_traslado"] = pd.to_datetime(
            df_inv_tab1["fecha_ultimo_traslado"],
            errors="coerce"
        )

        # convertir a periodo mes
        df_inv_tab1["mes_traslado"] = df_inv_tab1["fecha_ultimo_traslado"].dt.to_period("M")

    else:
        df_inv_tab1["mes_traslado"] = pd.NaT


    # =========================
    # FUNCIÓN SEMÁFORO SEGURA
    # =========================
    def semaforo(mes):
        if pd.isna(mes):
            return "⚪ Sin dato"
        try:
            if mes in [mes_actual, mes_1]:
                return "🟢 Verde"
            elif mes == mes_2:
                return "🟡 Amarillo"
            else:
                return "🔴 Rojo"
        except:
            return "⚪ Error"


    df_inv_tab1["semaforo"] = df_inv_tab1["mes_traslado"].apply(semaforo)

    # =========================
    # DETALLE CON FILTROS
    # =========================
    st.subheader("Detalle Inventario con Semáforo")

    df_detalle_tab1 = df_inv_tab1.copy()

    # =========================
    # FILTROS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        filtro_semaforo = st.multiselect(
            "Filtrar por Semáforo",
            options=df_detalle_tab1["semaforo"].dropna().unique(),
            default=df_detalle_tab1["semaforo"].dropna().unique()
        )

    with col2:
        filtro_estado = st.multiselect(
            "Filtrar por Estado",
            options=df_detalle_tab1["descestado"].dropna().unique(),
            default=df_detalle_tab1["descestado"].dropna().unique()
        )

    # aplicar filtros
    df_detalle = df_detalle_tab1[
        df_detalle_tab1["semaforo"].isin(filtro_semaforo) &
        df_detalle_tab1["descestado"].isin(filtro_estado)
    ]




    # =========================
    # MOSTRAR TABLA
    # =========================
    st.dataframe(df_detalle[[
        "grupo",
        "sucursal",
        "marca",
        "referencia",
        "serial",
        "fecha_ultimo_traslado",
        "descestado",
        "semaforo"
    ]], use_container_width=True)

    # =========================
    # RESUMEN AGRUPADO
    # =========================
    st.subheader("Resumen Inventario")

    inv = df_inv_tab1.groupby(
        ["grupo", "sucursal", "marca", "referencia"]
    )["serial"].count().reset_index(name="cantidad")

    st.dataframe(inv, use_container_width=True)

    # =========================
    # RESUMEN POSTPAGO / PREPAGO
    # =========================
    st.subheader("Resumen por Referencia")

    base = df_inv_tab1.copy()
    base["grupo"] = base["grupo"].str.upper().str.strip()

    resumen = base.pivot_table(
        index="referencia",
        columns="grupo",
        values="serial",
        aggfunc="count",
        fill_value=0
    ).reset_index()

    resumen.columns.name = None

    for col in ["POSTPAGO", "PREPAGO"]:
        if col not in resumen.columns:
            resumen[col] = 0

    resumen["TOTAL"] = resumen["POSTPAGO"] + resumen["PREPAGO"]

    st.dataframe(resumen, use_container_width=True)



# =========================
# PRESTAMOS A ASESORES
# =========================
# =========================
# TAB 2 VENTAS
# =========================
with tab2:
    st.title("📆 Prestamos sub")

    df_prestamo = df_inv_fil[
        df_inv_fil["descestado"] == "Prestamo Asesor"
    ].copy()

    if df_prestamo.empty:
        st.info("No hay equipos en préstamo con los filtros actuales")
    else:

        # 🔍 detectar columnas automáticamente
        col_asesor = [c for c in df_prestamo.columns if "asesor" in c.lower()][0]
        col_edad = [c for c in df_prestamo.columns if "edadprestamo" in c.lower()][0]
        col_fecha = [c for c in df_prestamo.columns if "fechaprestamo" in c.lower()][0]

        # =========================
        # FILTRO POR ASESOR
        # =========================
        lista_asesores = sorted(df_prestamo[col_asesor].dropna().unique())

        asesor_select = st.selectbox(
            "👤 Selecciona un Asesor",
            options=["Todos"] + lista_asesores
        )

        if asesor_select != "Todos":
            df_prestamo = df_prestamo[
                df_prestamo[col_asesor] == asesor_select
            ]

        # =========================
        # SEMÁFORO
        # =========================
        def semaforo_prestamo(dias):
            if pd.isna(dias):
                return "⚪ Sin dato"
            elif dias <= 30:
                return "🟢 Verde"
            elif dias <= 60:
                return "🟡 Amarillo"
            else:
                return "🔴 Rojo"

        df_prestamo["semaforo"] = df_prestamo[col_edad].apply(semaforo_prestamo)

        # =========================
        # MÉTRICAS
        # =========================
        col1, col2, col3 = st.columns(3)

        col1.metric("Total equipos", len(df_prestamo))
        col2.metric("🔴 +60 días", len(df_prestamo[df_prestamo[col_edad] > 60]))
        col3.metric("🟢 <=30 días", len(df_prestamo[df_prestamo[col_edad] <= 30]))

        # =========================
        # RESUMEN
        # =========================
        resumen = df_prestamo.groupby(
            ["referencia"]
        )["serial"].count().reset_index(name="cantidad")

        st.subheader("📊 Resumen por Referencia")
        st.dataframe(resumen, use_container_width=True)

        # =========================
        # DETALLE
        # =========================
        st.subheader("🔍 Detalle")

        st.dataframe(df_prestamo[[
            "referencia",
            "grupo",
            "serial",
            col_fecha,
            col_asesor,
            col_edad,
            "semaforo"
        ]], use_container_width=True)


df_ven_fil["fecha"] = pd.to_datetime(
    df_ven_fil["fecha"],
    errors="coerce"
)

# =========================
# TAB 3 VENTAS
# =========================
with tab3:
    st.title("📊 Ventas vs Inventario")

    # 🔥 usar último mes REAL de datos para TODO
    fecha_max = df_ven_fil["fecha"].dropna().max()

    if pd.isna(fecha_max):
        st.error("No hay fechas válidas en ventas")
        st.stop()

    mes_actual = fecha_max.to_period("M")

    # =========================
    # FILTRO POR REFERENCIA
    # =========================
    lista_ref = sorted(df_ven_fil["referencia"].dropna  ().unique())

    ref_select = st.selectbox(
        "Selecciona una referencia",
        options=["Todas"] + lista_ref
    )

    if ref_select != "Todas":
        df_ven_tab = df_ven_fil[df_ven_fil["referencia"] == ref_select]
        df_inv_tab = df_inv_fil[df_inv_fil["referencia"] == ref_select]
    else:
        df_ven_tab = df_ven_fil
        df_inv_tab = df_inv_fil

    # =========================
    # PREPARACIÓN
    # =========================
    df_ven_tab["mes"] = df_ven_tab["fecha"].dt.to_period("M")

    # =========================
    # VENTAS MES ACTUAL (REAL)
    # =========================
    ventas_mes = df_ven_tab[df_ven_tab["mes"] == mes_actual]

    ventas_ref = ventas_mes.groupby(
        ["referencia"]
    )["cantidad"].sum().reset_index(name="ventas_mes_actual")

    # =========================
    # INVENTARIO
    # =========================
    inv_ref = df_inv_tab.groupby(
        ["referencia"]
    )["serial"].count().reset_index(name="Total_Bodega")

    
    # =========================
    # PROMEDIO 3 MESES
    # =========================
    meses_validos = [mes_actual - i for i in range(1, 4)]

    df_3m = df_ven_tab[df_ven_tab["mes"].isin(meses_validos)]

    # =========================
    # PROMEDIO REAL 3 MESES
    # SIN AFECTAR SUCURSALES NUEVAS
    # =========================

    ventas_mes_ref = df_3m.groupby(
        ["sucursal", "referencia", "mes"]
    )["cantidad"].sum().reset_index()

    ventas_mes_ref = ventas_mes_ref.pivot_table(
        index=["sucursal", "referencia"],
        columns="mes",
        values="cantidad",
        fill_value=0
    )

    # asegurar columnas de meses
    for m in meses_validos:
        if m not in ventas_mes_ref.columns:
            ventas_mes_ref[m] = 0

    # ordenar meses
    ventas_mes_ref = ventas_mes_ref[sorted(ventas_mes_ref.columns)]

    # contar solo meses con ventas
    meses_con_datos = (ventas_mes_ref > 0).sum(axis=1)

    # evitar división por cero
    meses_con_datos = meses_con_datos.replace(0, 1)

    # promedio real
    ventas_mes_ref["promedio"] = (
        ventas_mes_ref.sum(axis=1) / meses_con_datos
    ).round(0).astype(int)

    # volver a referencia global
    prom = (
        ventas_mes_ref.groupby("referencia")["promedio"]
        .mean()
        .round(0)
        .astype(int)
        .reset_index()
    )



    # =========================
    # UNIÓN FINAL
    # =========================
    final = ventas_ref.merge(inv_ref, on="referencia", how="left")
    final = final.merge(prom, on="referencia", how="left")

    final.fillna(0, inplace=True)

    st.dataframe(final, use_container_width=True)

    # =========================
    # DETALLE VENTAS
    # =========================
    st.subheader("Detalle Ventas")

    lista_roles = sorted(ventas_mes["rolvendedor"].dropna().unique())

    rol_select = st.selectbox(
        "Filtrar por Rol Vendedor",
        options=["Todos"] + lista_roles
    )

    if rol_select != "Todos":
        ventas_mes = ventas_mes[
            ventas_mes["rolvendedor"] == rol_select
        ]

    col_conversion = next(
        (c for c in df_ven_tab.columns if "conversion" in c),
        None
    )

    if col_conversion:
        detalle = ventas_mes.groupby(
            ["referencia", "rolvendedor", "productodeventa", col_conversion]
        )["cantidad"].sum().reset_index()
    else:
        detalle = ventas_mes.groupby(
            ["referencia", "rolvendedor", "productodeventa"]
        )["cantidad"].sum().reset_index()
        st.warning("No se encontró columna de conversión")

    st.dataframe(detalle, use_container_width=True)

    st.session_state["final"] = final

# =========================
# TAB 4 DESCARGAS
# =========================
with tab4:
    st.title("📥 Descarga de Inventario")

    from io import BytesIO

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        return output.getvalue()

    st.subheader("📦 Inventario")

    excel_inv = to_excel(df_inv_fil)

    st.download_button(
        label="⬇️ Descargar Inventario",
        data=excel_inv,
        file_name="inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )