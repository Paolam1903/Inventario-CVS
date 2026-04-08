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
# NORMALIZAR INVENTARIO
# ===============================
if "descgrupo" in inv.columns:
    inv.rename(columns={"descgrupo": "sucursal"}, inplace=True)

if "codgrupo" in inv.columns:
    inv.rename(columns={"codgrupo": "tipo"}, inplace=True)

inv["sucursal"] = inv["sucursal"].astype(str).str.upper().str.strip()

# ===============================
# NORMALIZAR VENTAS
# ===============================
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
inv["serial"] = inv["serial"].astype(str).str.replace(".0","",regex=False).str.strip()
ven["serial"] = ven["serial"].astype(str).str.replace(".0","",regex=False).str.strip()

# ===============================
# FECHAS
# ===============================
inv["fecha_ingreso"] = pd.to_datetime(inv["fecha_ingreso"], errors="coerce")
ven["fecha_venta"] = pd.to_datetime(ven["fecha_venta"], errors="coerce")

# ===============================
# CRUCE INVENTARIO
# ===============================
df_inv = inv.merge(
    ven[[
        "serial","fecha_venta","indicador_conversion",
        "puntos_producto","puntos_promo","lista_precios"
    ]],
    on="serial",
    how="left"
)

df_inv["origen"] = "INVENTARIO"

# ===============================
# VENTAS SIN INVENTARIO
# ===============================
ventas_no_inv = ven[~ven["serial"].isin(inv["serial"])].copy()
ventas_no_inv["origen"] = "VENTA"

for col in df_inv.columns:
    if col not in ventas_no_inv.columns:
        ventas_no_inv[col] = None

# ===============================
# UNIR
# ===============================
df = pd.concat([df_inv, ventas_no_inv], ignore_index=True)

# ===============================
# MARCA
# ===============================
df["marca"] = df["referencia"].astype(str).str.split().str[0]

# ===============================
# VENDIDO
# ===============================
df["vendido"] = df["fecha_venta"].notna()
df["vendido"] = df["vendido"].apply(lambda x: "VENDIDO" if x else "BODEGA")

# ===============================
# SEMÁFORO DETALLE
# ===============================
hoy = pd.to_datetime(datetime.today())

df["dias"] = (hoy - df["fecha_ingreso"]).dt.days
df["meses"] = ((df["dias"]/30)).fillna(0).round(0).astype(int)

def semaforo(x):
    if x <= 1:
        return "🟢 Verde"
    elif x <= 2:
        return "🟡 Amarillo"
    else:
        return "🔴 Rojo"

df["semaforo"] = df["meses"].apply(semaforo)

# ===============================
# PROMEDIO 3 MESES (SOLO VENTAS)
# ===============================
ultimos = ven[ven["fecha_venta"] >= (hoy - pd.DateOffset(months=3))].copy()

ultimos["mes"] = ultimos["fecha_venta"].dt.to_period("M")

ventas_mes = (
    ultimos.groupby(["referencia","mes"])
    .size()
    .reset_index(name="ventas")
)

promedio = (
    ventas_mes.groupby("referencia")["ventas"]
    .mean()
    .reset_index()
)

promedio["ventas"] = promedio["ventas"].round(0).astype(int)

df = df.merge(promedio, on="referencia", how="left")
df.rename(columns={"ventas":"promedio_3_meses"}, inplace=True)

df["promedio_3_meses"] = df["promedio_3_meses"].fillna(0).astype(int)

# ===============================
# CANTIDAD POR REFERENCIA
# ===============================
conteo_ref = (
    df.groupby(["sucursal","referencia"])["serial"]
    .nunique()
    .reset_index()
    .rename(columns={"serial":"cantidad_referencia"})
)

df = df.merge(conteo_ref, on=["sucursal","referencia"], how="left")

# ===============================
# 🎛️ FILTROS (CORRECTOS)
# ===============================
st.sidebar.header("Filtros")

filtro_origen = st.sidebar.selectbox("Vista", ["TODOS","INVENTARIO","VENTA"])

sucursales = ["Todas"] + sorted(df["sucursal"].dropna().unique())
sel_sucursal = st.sidebar.selectbox("Sucursal", sucursales)

tipos = ["Todos"] + sorted(df["tipo"].dropna().unique())
sel_tipo = st.sidebar.selectbox("Tipo", tipos)

marcas = ["Todas"] + sorted(df["marca"].dropna().unique())
sel_marca = st.sidebar.selectbox("Marca", marcas)

# ===============================
# APLICAR FILTROS BIEN
# ===============================
df_filtrado = df.copy()

if filtro_origen != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["origen"] == filtro_origen]

if sel_sucursal != "Todas":
    df_filtrado = df_filtrado[df_filtrado["sucursal"] == sel_sucursal]

if sel_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == sel_tipo]

if sel_marca != "Todas":
    df_filtrado = df_filtrado[df_filtrado["marca"] == sel_marca]

# ===============================
# KPI
# ===============================
k1,k2,k3 = st.columns(3)

k1.metric("📦 Inventario", len(df_filtrado[df_filtrado["origen"]=="INVENTARIO"]))
k2.metric("✅ Vendidos", (df_filtrado["vendido"]=="VENDIDO").sum())
k3.metric("📊 Ventas sin inventario", len(df_filtrado[df_filtrado["origen"]=="VENTA"]))

# ===============================
# RESUMEN
# ===============================
st.subheader("📊 Resumen Ejecutivo")

resumen = df_filtrado.groupby(["sucursal","referencia"]).agg(
    cantidad_bodega=("cantidad_referencia","max"),
    vendidos=("vendido", lambda x: (x=="VENDIDO").sum()),
    meses_bodega=("meses","max")
).reset_index()

resumen["meses_bodega"] = resumen["meses_bodega"].fillna(0).astype(int)


resumen["sugerido_venta_mes"] = (
    (resumen["cantidad_bodega"]/3)
    .fillna(0)
    .round(0)
    .astype(int)
)

resumen["semaforo"] = resumen["meses_bodega"].apply(semaforo)

st.dataframe(resumen)

# ===============================
# DETALLE
# ===============================
st.subheader("📋 Detalle Inventario")

columnas = [
    "sucursal","tipo","referencia","cantidad_referencia","serial",
    "fecha_ingreso","fecha_venta","vendido",
    "indicador_conversion","puntos_producto",
    "puntos_promo",
    "promedio_3_meses","semaforo"
]

st.dataframe(df_filtrado[columnas])