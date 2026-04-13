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

st.title("📊 Inventario del 13 de abril vs Ventas de enero al 12 de abril")

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
# ASEGURAR COLUMNAS
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
# FECHAS
# ===============================
inv["fecha_ingreso"] = pd.to_datetime(inv["fecha_ingreso"], errors="coerce")
ven["fecha_venta"] = pd.to_datetime(ven["fecha_venta"], errors="coerce")



# ===============================
# MARCA
# ===============================
inv["marca"] = inv["referencia"].astype(str).str.split().str[0]

# ===============================
# CRUCE INVENTARIO
# ===============================
# ===============================
# ASEGURAR COLUMNAS DE VENTAS
# ===============================
columnas_ventas = [
    "serial",
    "fecha_venta",
    "indicador_conversion",
    "puntos_producto",
    "puntos_promo",
    "lista_precios"
]

for col in columnas_ventas:
    if col not in ven.columns:
        ven[col] = None

# ===============================
# CRUCE INVENTARIO + VENTAS
# ===============================
df_inv = inv.merge(
    ven[columnas_ventas],
    on="serial",
    how="left"
)

df_inv["origen"] = "INVENTARIO"



# ===============================
# VENTAS SIN INVENTARIO
# ===============================
ventas_no_inv = ven[~ven["serial"].isin(inv["serial"])].copy()

ventas_no_inv["referencia"] = ventas_no_inv.get("referencia", "SIN REFERENCIA")
ventas_no_inv["sucursal"] = ventas_no_inv.get("sucursal", "SIN SUCURSAL")
ventas_no_inv["tipo"] = "VENTA"
ventas_no_inv["fecha_ingreso"] = pd.NaT
ventas_no_inv["marca"] = ventas_no_inv["referencia"].astype(str).str.split().str[0]
ventas_no_inv["origen"] = "VENTA"

# ===============================
# ASEGURAR COLUMNAS EN VENTAS SIN INVENTARIO
# ===============================
for col in ["indicador_conversion", "puntos_producto", "puntos_promo", "lista_precios"]:
    if col not in ventas_no_inv.columns:
        ventas_no_inv[col] = None



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
# TIEMPO EN INVENTARIO
# ===============================
hoy = pd.to_datetime(datetime.today())

df["dias"] = (hoy - df["fecha_ingreso"]).dt.days
df["meses"] = (df["dias"] / 30).fillna(0)



# ===============================
# SEMÁFORO
# ===============================
def semaforo(x):
    if x <= 1:
        return "🟢 Verde"
    elif x <= 2:
        return "🟡 Amarillo"
    else:
        return "🔴 Rojo"

df["semaforo"] = df["meses"].apply(semaforo)



# ===============================
# 📊 TABLA PEQUEÑA POR MES (YA FILTRADA)
# ===============================
tabla_mes = df.copy()

tabla_mes["mes_ingreso"] = tabla_mes["fecha_ingreso"].dt.to_period("M").astype(str)

tabla_mes = (
    tabla_mes.groupby("mes_ingreso")["serial"]
    .nunique()
    .reset_index(name="cantidad")
    .sort_values("mes_ingreso")
)



# ===============================
# PROMEDIO 3 MESES
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
# CANTIDAD INVENTARIO
# ===============================
conteo = inv.groupby(["sucursal", "referencia"])["serial"].nunique().reset_index()
conteo = conteo.rename(columns={"serial": "cantidad_referencia"})

df = df.merge(conteo, on=["sucursal", "referencia"], how="left")


# ===============================
# 🎛️ FILTROS (PRIMERO)
# ===============================
st.sidebar.header("Filtros")

origen_sel = st.sidebar.selectbox("Origen", ["Todos", "INVENTARIO", "VENTA"])

sucursales = ["Todas"] + sorted(df["sucursal"].dropna().unique())
sel_sucursal = st.sidebar.selectbox("Sucursal", sucursales)

tipos = ["Todos"] + sorted(df["tipo"].dropna().unique())
sel_tipo = st.sidebar.selectbox("Tipo", tipos)

marcas = ["Todas"] + sorted(df["marca"].dropna().unique())
sel_marca = st.sidebar.selectbox("Marca", marcas)

# Aplicar filtros
df_filtrado = df.copy()

if origen_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["origen"] == origen_sel]

if sel_sucursal != "Todas":
    df_filtrado = df_filtrado[df_filtrado["sucursal"] == sel_sucursal]

if sel_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == sel_tipo]

if sel_marca != "Todas":
    df_filtrado = df_filtrado[df_filtrado["marca"] == sel_marca]


# ===============================
# 🎨 FUNCIÓN COLOR (ANTES DE USAR)
# ===============================
def color_fila(row):
    hoy = pd.to_datetime(datetime.today())
    fecha = pd.to_datetime(row["mes_ingreso"])

    meses_diff = (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)

    if meses_diff <= 1:
        color = "#28a745"  # Verde
    elif meses_diff == 2:
        color = "#ffc107"  # Amarillo
    else:
        color = "#dc3545"  # Rojo

    return [f"background-color: {color}; color: white"] * len(row)


# ===============================
# 📊 TABLA PEQUEÑA (YA FILTRADA)
# ===============================
tabla_mes = df_filtrado.copy()

tabla_mes = tabla_mes[tabla_mes["origen"] == "INVENTARIO"]  # 🔥 solo inventario

tabla_mes["mes_ingreso"] = tabla_mes["fecha_ingreso"].dt.to_period("M").astype(str)

tabla_mes = (
    tabla_mes.groupby("mes_ingreso")["serial"]
    .nunique()
    .reset_index(name="cantidad")
    .sort_values("mes_ingreso")
)


# ===============================
# 📊 DISTRIBUCIÓN EN COLUMNAS
# ===============================
col1, col2 = st.columns([1, 2])

# 👉 TABLA IZQUIERDA
with col1:
    st.markdown("### 📅 Inventario por Mes")

    st.dataframe(
        tabla_mes.style.apply(color_fila, axis=1),
        height=250
    )

# 👉 KPI DERECHA
with col2:
    st.markdown("### 📊 Indicadores")

    k1, k2, k3 = st.columns(3)

    k1.metric("📦 Inventario", df_filtrado[df_filtrado["origen"]=="INVENTARIO"].shape[0])
    k2.metric("✅ Vendidos", (df_filtrado["vendido"]=="VENDIDO").sum())
    k3.metric("🚫 Ventas sin inventario", df_filtrado[df_filtrado["origen"]=="VENTA"].shape[0])



# ===============================
# RESUMEN EJECUTIVO
# ===============================
st.subheader("📊 Resumen Ejecutivo")

# 🔥 SOLO INVENTARIO PARA MESES
resumen = df_filtrado[df_filtrado["origen"] == "INVENTARIO"].groupby(["sucursal", "referencia"]).agg(
    cantidad_bodega=("cantidad_referencia", "max"),
    meses_bodega=("meses", "mean")
).reset_index()

# FORMATO
resumen["cantidad_bodega"] = resumen["cantidad_bodega"].fillna(0)

# 🔥 MESES ENTERO
resumen["meses_bodega"] = resumen["meses_bodega"].fillna(0).round(0).astype(int)

# SUGERIDO
resumen["sugerido_venta_mes"] = (
    (resumen["cantidad_bodega"] / 3)
    .fillna(0)
    .round(0)
    .astype(int)
)

# SEMÁFORO
resumen["semaforo"] = resumen["meses_bodega"].apply(semaforo)

orden = {"🔴 Rojo": 3, "🟡 Amarillo": 2, "🟢 Verde": 1}
resumen["orden"] = resumen["semaforo"].map(orden)

resumen = resumen.sort_values(by=["orden", "cantidad_bodega"], ascending=[False, False])

st.dataframe(resumen[
    [
        "sucursal",
        "referencia",
        "cantidad_bodega",
        "meses_bodega",
        "sugerido_venta_mes",
        "semaforo"
    ]
])


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
    "puntos_producto",
    "puntos_promo",
    "ventas",
    "semaforo"
]

columnas = [c for c in columnas if c in df_filtrado.columns]

st.dataframe(df_filtrado[columnas])