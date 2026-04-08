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

st.title("📊 Inventario del 8 vs Ventas de enero a 7 de abril")

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
# RENOMBRAR SEGURO
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
# ASEGURAR COLUMNAS EXISTAN
# ===============================
for col in ["indicador_conversion", "puntos_producto", "puntos_promo", "lista_precios"]:
    if col not in ven.columns:
        ven[col] = None

# ===============================
# LIMPIAR SERIAL
# ===============================
inv["serial"] = inv["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()
ven["serial"] = ven["serial"].astype(str).str.replace(".0", "", regex=False).str.strip()

# ===============================
# FECHAS SEGURAS
# ===============================
inv["fecha_ingreso"] = pd.to_datetime(inv["fecha_ingreso"], errors="coerce")
ven["fecha_venta"] = pd.to_datetime(ven["fecha_venta"], errors="coerce")

# ===============================
# MARCA
# ===============================
inv["marca"] = inv["referencia"].astype(str).str.split().str[0]

# ===============================
# CRUCE INVENTARIO + VENTAS
# ===============================
df_inv = inv.merge(
    ven[["serial", "fecha_venta", "indicador_conversion", "puntos_producto", "puntos_promo", "lista_precios"]],
    on="serial",
    how="left"
)

df_inv["origen"] = "INVENTARIO"

# ===============================
# VENTAS QUE NO ESTÁN EN INVENTARIO
# ===============================
ventas_no_inv = ven[~ven["serial"].isin(inv["serial"])].copy()

ventas_no_inv["referencia"] = ventas_no_inv.get("referencia", "SIN REFERENCIA")
ventas_no_inv["sucursal"] = ventas_no_inv.get("sucursal", "SIN SUCURSAL")
ventas_no_inv["tipo"] = "VENTA"
ventas_no_inv["fecha_ingreso"] = pd.NaT
ventas_no_inv["marca"] = ventas_no_inv["referencia"].astype(str).str.split().str[0]
ventas_no_inv["origen"] = "VENTA"

# ===============================
# UNIFICAR
# ===============================
df = pd.concat([df_inv, ventas_no_inv], ignore_index=True)

# ===============================
# VENDIDO
# ===============================
df["vendido"] = df["fecha_venta"].notna()
df["vendido"] = df["vendido"].map({True: "VENDIDO", False: "BODEGA"})

# ===============================
# SEMÁFORO
# ===============================
hoy = pd.to_datetime(datetime.today())

df["dias"] = (hoy - df["fecha_ingreso"]).dt.days
df["meses"] = (df["dias"] / 30).fillna(0)

def semaforo(x):
    if x <= 1:
        return "🟢 Verde"
    elif x <= 2:
        return "🟡 Amarillo"
    else:
        return "🔴 Rojo"

df["semaforo"] = df["meses"].apply(semaforo)

# ===============================
# PROMEDIO 3 MESES (VENTAS)
# ===============================
ultimos = ven[ven["fecha_venta"] >= (hoy - pd.DateOffset(months=3))]

ventas_mes = (
    ultimos.groupby(["referencia", ultimos["fecha_venta"].dt.to_period("M")])
    .size()
    .reset_index(name="ventas")
)

promedio = (
    ventas_mes.groupby("referencia")["ventas"]
    .mean()
    .reset_index()
)

df = df.merge(promedio, on="referencia", how="left")

df["ventas"] = df["ventas"].fillna(0).round(0).astype(int)

# ===============================
# CANTIDAD INVENTARIO REAL
# ===============================
conteo = inv.groupby(["sucursal", "referencia"])["serial"].nunique().reset_index()
conteo = conteo.rename(columns={"serial": "cantidad_referencia"})

df = df.merge(conteo, on=["sucursal", "referencia"], how="left")

# ===============================
# FILTROS
# ===============================
st.sidebar.header("Filtros")

origen_sel = st.sidebar.selectbox("Origen", ["Todos", "INVENTARIO", "VENTA"])

sucursales = ["Todas"] + sorted(df["sucursal"].dropna().unique())
sel_sucursal = st.sidebar.selectbox("Sucursal", sucursales)

tipos = ["Todos"] + sorted(df["tipo"].dropna().unique())
sel_tipo = st.sidebar.selectbox("Tipo", tipos)

marcas = ["Todas"] + sorted(df["marca"].dropna().unique())
sel_marca = st.sidebar.selectbox("Marca", marcas)

if origen_sel != "Todos":
    df = df[df["origen"] == origen_sel]

if sel_sucursal != "Todas":
    df = df[df["sucursal"] == sel_sucursal]

if sel_tipo != "Todos":
    df = df[df["tipo"] == sel_tipo]

if sel_marca != "Todas":
    df = df[df["marca"] == sel_marca]

# ===============================
# KPI
# ===============================
c1, c2, c3 = st.columns(3)

c1.metric("Inventario", df[df["origen"]=="INVENTARIO"].shape[0])
c2.metric("Vendidos", (df["vendido"]=="VENDIDO").sum())
c3.metric("Ventas sin inventario", df[df["origen"]=="VENTA"].shape[0])

# ===============================
# RESUMEN
# ===============================
st.subheader("📊 Resumen Ejecutivo")

resumen = df.groupby(["sucursal", "referencia"]).agg(
    cantidad_bodega=("cantidad_referencia", "max"),
    vendidos=("vendido", lambda x: (x == "VENDIDO").sum()),
    promedio_3_meses=("ventas", "mean"),
    meses_bodega=("meses", "mean")
).reset_index()

resumen["cantidad_bodega"] = resumen["cantidad_bodega"].fillna(0)
resumen["promedio_3_meses"] = resumen["promedio_3_meses"].fillna(0).round(0).astype(int)
resumen["meses_bodega"] = resumen["meses_bodega"].fillna(0).round(0).astype(int)

resumen["sugerido_venta_mes"] = (resumen["cantidad_bodega"]/3).fillna(0).round(0).astype(int)

resumen["semaforo"] = resumen["meses_bodega"].apply(semaforo)

orden = {"🔴 Rojo":3,"🟡 Amarillo":2,"🟢 Verde":1}
resumen["orden"] = resumen["semaforo"].map(orden)

resumen = resumen.sort_values(by=["orden","cantidad_bodega"], ascending=[False, False])

st.dataframe(resumen[[
    "sucursal",
    "referencia",
    "cantidad_bodega",
    "vendidos",
    "sugerido_venta_mes",
    "semaforo"
]])

# ===============================
# DETALLE (SIN STYLER PESADO)
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
    "ventas",
    "semaforo"
]

# evitar errores si falta alguna columna
columnas = [c for c in columnas if c in df.columns]

st.dataframe(df[columnas])