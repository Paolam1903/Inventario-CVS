import streamlit as st
import pandas as pd
from datetime import datetime

inv = pd.read_excel("./inventario.xlsx")
ven = pd.read_excel("./ventas.xlsx")

st.set_page_config(layout="wide")
st.title("📊 Inventario vs Ventas")

# ===============================
# CARGA
# ===============================
inv = pd.read_excel("inventario.xlsx")
ven = pd.read_excel("ventas.xlsx")

# ===============================
# LIMPIAR COLUMNAS
# ===============================
inv.columns = inv.columns.str.lower().str.strip()
ven.columns = ven.columns.str.lower().str.strip()

# ===============================
# RENOMBRAR
# ===============================
inv = inv.rename(columns={
    "serial": "serial",
    "referencia": "referencia",
    "codgrupo": "tipo",
    "descgrupo": "sucursal",
    "fecha_ingreso": "fecha_ingreso"
})

ven = ven.rename(columns={
    "fecha": "fecha_venta",
    "indicador conversion": "indicador_conversion",
    "puntos producto": "puntos_producto",
    "puntos promo": "puntos_promo",
    "lista de precios": "lista_precios"
})

# ===============================
# LIMPIAR SERIAL
# ===============================
inv["serial"] = inv["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()
ven["serial"] = ven["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()

# ===============================
# FECHAS
# ===============================
inv["fecha_ingreso"] = pd.to_datetime(inv["fecha_ingreso"], errors="coerce")
ven["fecha_venta"] = pd.to_datetime(ven["fecha_venta"], errors="coerce")

# ===============================
# CANTIDAD REAL INVENTARIO
# ===============================
conteo_ref = (
    inv.groupby(["sucursal", "referencia"])["serial"]
    .nunique()
    .reset_index()
    .rename(columns={"serial": "cantidad_referencia"})
)

# ===============================
# CRUCE
# ===============================
df = inv.merge(
    ven[
        [
            "serial",
            "fecha_venta",
            "indicador_conversion",
            "puntos_producto",
            "puntos_promo",
            "lista_precios"
        ]
    ],
    on="serial",
    how="left"
)

df = df.merge(conteo_ref, on=["sucursal", "referencia"], how="left")

# ===============================
# VENDIDO
# ===============================
df["vendido"] = df["fecha_venta"].notna()
df["vendido"] = df["vendido"].apply(lambda x: "VENDIDO" if x else "BODEGA")

# ===============================
# SEMÁFORO
# ===============================
hoy = pd.to_datetime(datetime.today())

df["dias"] = (hoy - df["fecha_ingreso"]).dt.days
df["meses"] = df["dias"] / 30

def semaforo(x):
    if x <= 1:
        return "🟢 Verde"
    elif x <= 2:
        return "🟡 Amarillo"
    else:
        return "🔴 Rojo"

df["semaforo"] = df["meses"].apply(semaforo)

# ===============================
# PROMEDIO 3 MESES
# ===============================
df["mes"] = df["fecha_venta"].dt.to_period("M")

ultimos = df[
    df["fecha_venta"] >= (hoy - pd.DateOffset(months=3))
]

ventas_mes = (
    ultimos
    .groupby(["referencia", "mes"])
    .size()
    .reset_index(name="ventas")
)

promedio = (
    ventas_mes
    .groupby("referencia")["ventas"]
    .mean()
    .reset_index()
    .rename(columns={"ventas": "promedio_3_meses"})
)

df = df.merge(promedio, on="referencia", how="left")

# ===============================
# FILTRO
# ===============================
st.sidebar.header("Filtros")

sucursales = ["Todas"] + sorted(df["sucursal"].dropna().unique())
sel = st.sidebar.selectbox("Sucursal", sucursales)

if sel != "Todas":
    df = df[df["sucursal"] == sel]

# ===============================
# KPI
# ===============================
col1, col2, col3 = st.columns(3)

col1.metric("Inventario", len(df))
col2.metric("Vendidos", int((df["vendido"] == "VENDIDO").sum()))
col3.metric("No vendidos", int((df["vendido"] == "BODEGA").sum()))

# ===============================
# RESUMEN EJECUTIVO
# ===============================
st.subheader("📊 Resumen Ejecutivo")

resumen = df.groupby(["sucursal", "referencia"]).agg(
    cantidad_bodega=("cantidad_referencia", "max"),
    vendidos=("vendido", lambda x: (x == "VENDIDO").sum()),
    promedio_3_meses=("promedio_3_meses", "mean"),
    meses_bodega=("meses", "mean")
).reset_index()

resumen["promedio_3_meses"] = resumen["promedio_3_meses"].fillna(0)
resumen["sugerido_venta_mes"] = (resumen["cantidad_bodega"] / 3).round(0).astype(int)

def semaforo_resumen(x):
    if x <= 1:
        return "🟢 Verde"
    elif x <= 2:
        return "🟡 Amarillo"
    else:
        return "🔴 Rojo"

resumen["semaforo"] = resumen["meses_bodega"].apply(semaforo_resumen)

orden = {"🔴 Rojo": 3, "🟡 Amarillo": 2, "🟢 Verde": 1}
resumen["orden"] = resumen["semaforo"].map(orden)

resumen = resumen.sort_values(by=["orden", "cantidad_bodega"], ascending=[False, False])

df["puntos_producto"] = df["puntos_producto"].map(lambda x: f"{x:.1f}" if pd.notnull(x) else "")
df["puntos_promo"] = df["puntos_promo"].map(lambda x: f"{x:.1f}" if pd.notnull(x) else "")


df["promedio_3_meses"] = (
    pd.to_numeric(df["promedio_3_meses"], errors="coerce")
    .fillna(0)
    .round(0)
    .astype(int)
)

st.dataframe(resumen[
    [
        "sucursal",
        "referencia",
        "cantidad_bodega",
        "vendidos",
        "promedio_3_meses",
        "sugerido_venta_mes",
        "semaforo"
    ]
])

# ===============================
# 🎨 COLOR SOLO EN VENDIDO
# ===============================
def color_vendido(val):
    if val == "VENDIDO":
        return "background-color: #28a745; color: white; font-weight: bold"
    elif val == "BODEGA":
        return "background-color: #dc3545; color: white; font-weight: bold"
    else:
        return ""

# ===============================
# DETALLE
# ===============================
st.subheader("📋 Detalle Inventario")

columnas = [
    "sucursal",
    "tipo",
    "referencia",
    "cantidad_referencia",
    "serial",
    "fecha_ingreso",
    "fecha_venta",
    "vendido",
    "indicador_conversion",
    "puntos_producto",
    "puntos_promo",
    "lista_precios",
    "promedio_3_meses",
    "semaforo"
]

st.dataframe(
    df[columnas].style.applymap(color_vendido, subset=["vendido"])
)