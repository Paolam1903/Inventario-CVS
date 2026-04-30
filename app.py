import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sqlite3
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# =============================
# CONFIG
# =============================
st.set_page_config("Dashboard Comercial - Marzo CVS 2026", layout="wide")


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "comisiones.db"
LOGO_PATH = BASE_DIR / "logo.png"

RUTA_LIQ = DATA_DIR / "liquidacion_final.xlsx"
RUTA_METAS = DATA_DIR / "metas.xlsx"

# =============================
# VALIDACIÓN
# =============================
if not RUTA_LIQ.exists() or not RUTA_METAS.exists():
    st.error("❌ Faltan archivos en /data")
    st.stop()

# =============================
# HEADER
# =============================
st.markdown("""
<div style="background-color:#E30613;padding:15px;border-radius:10px">
<h1 style="color:white;text-align:center">📊 Dashboard Comercial ventas de 01 al 29 – CVS PLUS al 28 de abril 2026</h1>
</div>
""", unsafe_allow_html=True)

# =============================
# LOGO
# =============================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)


# =============================
# PERFIL + SEGURIDAD
# =============================
# =============================
# ACCESOS
# =============================
CLAVE_DIRECTOR = "Director2026+"
CLAVE_ADMIN = "Sercom2026+"

ACCESOS_CVS = {
    "COPACABANA": "copa20*",
    "BARBOSA": "barbosa20+",
    "CAUCASIA": "cvscaucasia2026/",
    "CIUDAD BOLIVAR": "bolivar2020+",
    "DABEIBA": "dabeiba2020+",
    "DON MATIAS": "cvsmatias2026*",
    "EL BAGRE": "bagre2021*",
    "FRONTINO": "frontino2026+",
    "LA ESTRELLA": "estrella20+",
    "NECHI": "cvssernechi2026+",
    "PRADO": "prado20*",
    "SEGOVIA": "sersegovia2026+",
    "YARUMAL": "cvsyarumal2026+",
    "ZARAGOZA": "zaragozaser2020+",
    "BELLO": "bello123+",
    "ENVIGADO": "envigado20+",
    "ITAGUI": "itagui2026+",
    "CALDAS": "caldas20+",
    "JUNIN": "junin2026+",
    "SABANETA": "sabaneta2020+",
    "TERMINAL NORTE": "norte2026*",
    "GENERAL": "Todos12345+",
    "NUMERARIO": "numerario2026+",
    "GIRARDOTA": "girardota20+",
    "SAN CRISTOBAL" : "Cristobal123",


}

st.sidebar.subheader("🔐 Acceso")

perfil = st.sidebar.selectbox(
    "Perfil",
    ["CVS", "ADMINISTRATIVO", "DIRECTOR COMERCIAL"]
)

es_director = False
es_admin = False
cvs_usuario = None

# =============================
# PERFIL CVS
# =============================
if perfil == "CVS":
    cvs_input = st.sidebar.selectbox(
        "Selecciona tu CVS",
        list(ACCESOS_CVS.keys())
    )
    clave = st.sidebar.text_input("Clave CVS", type="password")

    if clave == ACCESOS_CVS.get(cvs_input):
        cvs_usuario = cvs_input
        st.sidebar.success(f"Acceso autorizado: {cvs_usuario}")
    elif clave:
        st.sidebar.error("Clave incorrecta")

# =============================
# PERFIL ADMINISTRATIVO
# =============================
elif perfil == "ADMINISTRATIVO":
    clave = st.sidebar.text_input("Clave administrativa", type="password")
    if clave == CLAVE_ADMIN:
        es_admin = True
        st.sidebar.success("Acceso administrativo autorizado")
    elif clave:
        st.sidebar.error("Clave incorrecta")

# =============================
# PERFIL DIRECTOR
# =============================
elif perfil == "DIRECTOR COMERCIAL":
    clave = st.sidebar.text_input("Contraseña Director", type="password")
    if clave == CLAVE_DIRECTOR:
        es_director = True
        st.sidebar.success("Acceso director autorizado")
    elif clave:
        st.sidebar.error("Contraseña incorrecta")


# =============================
# CARGA DATOS Y FILTROS SEGURAMENTE
# ============================

# -----------------------------
# Leer archivos
# -----------------------------
df = pd.read_excel(RUTA_LIQ)
df_meta = pd.read_excel(RUTA_METAS)

# -----------------------------
# Formatear fecha y crear columna Mes
# -----------------------------
df["Fecha"] = pd.to_datetime(df["Fecha"])
df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")

# -----------------------------
# Normalizar columnas de texto
# -----------------------------
for c in ["Sucursal", "Producto", "Rol"]:
    if c in df.columns:
        df[c] = df[c].astype(str).str.upper().str.strip()
    if c in df_meta.columns:
        df_meta[c] = df_meta[c].astype(str).str.upper().str.strip()

# -----------------------------
# Merge con columnas necesarias
# Evitar traer "Mes" del df_meta para no sobreescribir
# -----------------------------
columnas_meta = [col for col in df_meta.columns if col not in ["Mes", "Sucursal", "Producto"]]
df = df.merge(df_meta[["Sucursal", "Producto"] + columnas_meta], 
              on=["Sucursal", "Producto"], how="left")

# -----------------------------
# FILTROS EN SIDEBAR
# -----------------------------
st.sidebar.subheader("📅 Filtros")

# Filtro por mes
meses = ["Todos"] + sorted(df["Mes"].dropna().unique())
mes_sel = st.sidebar.selectbox("Mes", meses)

# Filtro por CVS según perfil
if es_director or es_admin:
    cvs_sel = st.sidebar.selectbox(
        "CVS",
        ["Todos"] + sorted(df["Sucursal"].dropna().unique())
    )
else:
    cvs_sel = cvs_usuario

# -----------------------------
# APLICAR FILTROS
# -----------------------------
df_f = df.copy()

# Filtro mes
if mes_sel != "Todos":
    df_f = df_f[df_f["Mes"] == mes_sel]

# Filtro CVS
if cvs_sel and cvs_sel != "Todos":
    df_f = df_f[df_f["Sucursal"] == cvs_sel]


# =============================
# KPI CVS PLUS (ANTES DE LOS TABS)
# =============================

if cvs_sel and cvs_sel != "Todos":

    df_cvs_plus = df_f[
        (df_f["Sucursal"] == cvs_sel) &
        (df_f["Producto"].str.upper() == "CVS PLUS")
    ]

    # Meta CVS PLUS
    meta_plus = df_cvs_plus["Meta_Producto"].max()

    # Ejecutado (cantidad)
    ejec_plus = df_cvs_plus["Cantidad"].iloc[0] if not df_cvs_plus.empty else 0

    # % cumplimiento
    if meta_plus > 0:
        pct_plus = round((ejec_plus / meta_plus) * 100, 1)
    else:
        pct_plus = 0

    # Semáforo
    if pct_plus >= 100:
        color = "#2ecc71"
        estado = "Cumplido"
    elif pct_plus >= 80:
        color = "#f39c12"
        estado = "En riesgo"
    else:
        color = "#e74c3c"
        estado = "Bajo cumplimiento"

    # Cuadro visual
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:20px;
            border-radius:12px;
            text-align:center;
            color:white;
            font-size:22px;
            font-weight:bold;
            margin-bottom:15px;
        ">
        📦 CVS PLUS — {cvs_sel}<br><br>
        Meta: {int(meta_plus):,} | Ejecutado: {int(ejec_plus):,}<br>
        Cumplimiento: {pct_plus}% ({estado})
        </div>
        """,
        unsafe_allow_html=True
    )





# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Presupuesto / Comisión", "⚖️Cumplimiento General"])

# =============================
# TAB 1 – DASHBOARD
# =============================
with tab1:
    st.subheader("📦 Cumplimiento por Producto")
    
    # Lista fija de productos
    productos_base = ["HOGAR", "POSTPAGO", "TERMINALES", "CVS PLUS", "OTROS"]
    
    
    # Agrupar meta y ejecutado por producto
    prod = df_f.groupby("Producto").agg(
        Meta=("Meta_Producto", "max"),   # meta única
        Ejecutado=("Cantidad", "sum")    # cantidad vendida
    ).reset_index()


    # Asegurar productos base
    prod = pd.DataFrame(productos_base, columns=["Producto"]).merge(
        prod, on="Producto", how="left"
    ).fillna(0)


    # Calcular % cumplimiento
    prod["% Cumplimiento"] = (
        prod["Ejecutado"] / prod["Meta"]
    ).replace([np.inf, -np.inf], 0).fillna(0) * 100

    # Convertir a enteros
    prod["Meta"] = prod["Meta"].astype(int)
    prod["Ejecutado"] = prod["Ejecutado"].astype(int)
    prod["% Cumplimiento"] = prod["% Cumplimiento"].round(1)

    # Ordenar por ejecutado
    prod = prod.sort_values("Ejecutado", ascending=False).reset_index(drop=True)

    # Posiciones
    x = np.arange(len(prod["Producto"]))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars_meta = ax.bar(x - width/2, prod["Meta"], width, label="Meta")
    bars_ejec = ax.bar(x + width/2, prod["Ejecutado"], width, label="Ejecutado")

    # Etiquetas para META
    for bar in bars_meta:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{int(height):,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    # Etiquetas para EJECUTADO + %
    for i, bar in enumerate(bars_ejec):
        height = bar.get_height()
        pct = prod["% Cumplimiento"].iloc[i]
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{int(height):,}\n{pct:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    # Línea de tendencia
    z = np.polyfit(x, prod["Ejecutado"], 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), linestyle="--", linewidth=2, label="Tendencia Ejecutado")

    ax.set_xticks(x)
    ax.set_xticklabels(prod["Producto"], rotation=45, ha="right")
    ax.set_ylabel("Puntos")
    ax.set_title("Meta vs Ejecutado por Producto")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    st.pyplot(fig)


    # =============================
    # META GENERAL VS EJECUTADO
    # =============================

    st.subheader("🎯 Meta General vs Ejecutado")

    # Meta general sin duplicar CVS
    meta_general = (
        df_f[["Sucursal", "Meta_General"]]
        .drop_duplicates()
        ["Meta_General"]
        .sum()
    )

    # Ejecutado general
    ejecutado_general = df_f["Puntos"].sum()

    # % cumplimiento general
    pct_general = (ejecutado_general / meta_general * 100) if meta_general > 0 else 0

    # DataFrame gráfico
    df_general = pd.DataFrame({
        "Concepto": ["Meta General", "Ejecutado"],
        "Valor": [meta_general, ejecutado_general]
    })

    # Gráfico
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(df_general["Concepto"], df_general["Valor"])

    for bar in bars:
        height = bar.get_height()
        valor = f"{height:,.0f}".replace(",", ".")
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height * 1.01,
            valor,
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold"
        )

    # Título con % cumplimiento
    ax.set_title(f"Cumplimiento general: {pct_general:.1f}%", fontsize=8)


    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", "."))
    )

    # Reducir tamaño de números del eje Y
    ax.tick_params(axis='y', labelsize=6)

    ax.grid(axis="y", linestyle="--", alpha=0.5)

    st.pyplot(fig)



# =====================
# SUPERNUMERARIOS
# =====================
SUPERNUMERARIOS = [
    "Johan Daniel Herrera Mazo",
    "Kelly Yuliana Ospina Saldarriaga",
    "Lider Zargoza Kelly Celsa",
    "Sara Julieth Acevedo Gutierrez"
]


# =====================
# REGLA DE DISTRIBUCIÓN
# =====================
def calcular_distribucion(n_asesores, cvs):
    if str(cvs).upper() == "FRONTINO":
        return 0.40, 0.60

    if n_asesores == 0:
        return 1.0, 1.0

    if n_asesores == 1:
        return 0.40, 0.60
    elif n_asesores == 2:
        return 0.25, 0.375
    elif n_asesores >= 3:
        return 0.20, 0.266
    else:
        return 1.0, 0.0


# =====================
# MAESTRO DE PRODUCTOS
# =====================
def maestro_productos_por_cvs(df, cvs_sel):
    df_cvs = df[df["Sucursal"] == cvs_sel]

    maestro = (
        df_cvs[["Producto", "Meta_Producto"]]
        .drop_duplicates()
        .set_index("Producto")["Meta_Producto"]
        .to_dict()
    )

    productos_base = ["HOGAR", "POSTPAGO", "TERMINALES", "CVS PLUS", "OTROS"]

    for p in productos_base:
        if p not in maestro:
            maestro[p] = 0

    return maestro


def construir_tabla_productos(df_vendedor, maestro, df_cvs, rol):

    # ❌ EXCLUIR SUPERNUMERARIOS SOLO PARA META
    df_cvs_kpi = df_cvs[~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)]

    n_asesores = df_cvs_kpi[df_cvs_kpi["Rol"] == "ASESOR"]["Nombre_Vendedor"].nunique()

    porc_asesor, porc_lider = calcular_distribucion(n_asesores, df_cvs["Sucursal"].iloc[0])

    porcentaje = porc_lider if rol == "ASESOR" else porc_asesor

    ejec = df_vendedor.groupby("Producto")["Cantidad"].sum().to_dict()

    filas = []

    for producto, meta in maestro.items():

        meta_ajustada = meta * porcentaje
        ejecutado = ejec.get(producto, 0)

        if meta_ajustada > 0:
            pct = int(round((ejecutado / meta_ajustada) * 100))
        else:
            pct = 0

        filas.append({
            "Producto": producto,
            "Meta_Producto": int(round(meta_ajustada)),
            "Ejecutado": int(ejecutado),
            "% Cumplimiento": f"{pct}%"
        })

    tabla = pd.DataFrame(filas)

    orden_productos = ["POSTPAGO", "HOGAR", "TERMINALES", "OTROS", "CVS PLUS"]

    tabla["Producto"] = pd.Categorical(tabla["Producto"], categories=orden_productos, ordered=True)
    tabla = tabla.sort_values("Producto")

    return tabla


# =====================
# KPI DE PUNTOS
# =====================
def calcular_kpi_puntos(df_cvs, df_persona, rol):

    # ❌ excluir supernumerarios del cálculo general
    df_cvs_kpi = df_cvs[~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)]

    meta_general = df_cvs_kpi["Meta_General"].iloc[0]

    n_asesores = df_cvs_kpi[df_cvs_kpi["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()

    cvs = df_cvs_kpi["Sucursal"].iloc[0]

    pct_lider, pct_asesor_individual = calcular_distribucion(n_asesores, cvs)

    if rol == "LIDER":
        meta = meta_general * pct_lider
    else:
        meta = meta_general * pct_asesor_individual

    ejecutado = df_persona["Puntos"].sum()

    cumplimiento = round((ejecutado / meta) * 100, 1) if meta > 0 else 0

    return meta, ejecutado, cumplimiento


# =======================
# HISTÓRICO
# =======================
RUTA_HISTORICO = DATA_DIR / "historico_comisiones.xlsx"

if RUTA_HISTORICO.exists():
    df_historico = pd.read_excel(RUTA_HISTORICO)
else:
    df_historico = pd.DataFrame(
        columns=[
            "Mes", "CVS", "Nombre", "Rol", "Producto",
            "Meta_Producto", "Ejecutado", "% Cumplimiento",
            "Tipo Pago Comisión", "Observación",
            "% Cumplimiento Puntos", "ACC"
        ]
    )

# 🔴 asegurar columna nueva
if "% Cumplimiento Puntos" not in df_historico.columns:
    df_historico["% Cumplimiento Puntos"] = 0

if "historico_decisiones" not in st.session_state:
    st.session_state["historico_decisiones"] = df_historico.to_dict("records")

with st.sidebar:
    st.subheader("Filtros")
    meses = sorted(df["Mes"].dropna().unique())
    mes_sel = st.selectbox("Selecciona el mes historico", meses)


# =======================
# TAB 2
# =======================

with tab2:
    st.subheader("📍 Detalle por CVS")

    if cvs_sel == "Todos" or not cvs_sel:
        st.info("Selecciona un CVS en el panel lateral")
        st.stop()

    df_cvs = df_f[df_f["Sucursal"] == cvs_sel]
    maestro = maestro_productos_por_cvs(df_f, cvs_sel)

    tablas_guardar = []

    # =====================
    # LÍDER
    # =====================
    df_lider = df_cvs[df_cvs["Rol"] == "LIDER"].copy()

    if not df_lider.empty:
        nombre_lider = df_lider["Nombre_Vendedor"].iloc[0]
        st.markdown(f"## 👔 Líder: **{nombre_lider}**")

        meta_p, ejec_p, pct_p = calcular_kpi_puntos(df_cvs, df_lider, "LIDER")

        st.metric("🎯 KPI Puntos", f"{int(ejec_p)} / {int(meta_p)}", f"{pct_p}%")

        tabla_lider = construir_tabla_productos(df_lider, maestro, df_cvs, "LIDER")

        tabla_lider["Nombre"] = nombre_lider
        tabla_lider["Rol"] = "LIDER"
        tabla_lider["CVS"] = cvs_sel
        tabla_lider["Mes"] = mes_sel

        tabla_lider[["Tipo Pago Comisión", "Observación"]] = tabla_lider.apply(
            lambda r: next(
                (
                    (x["Tipo Pago Comisión"], x["Observación"])
                    for x in st.session_state["historico_decisiones"]
                    if x["Mes"] == mes_sel
                    and x["CVS"] == cvs_sel
                    and x["Nombre"] == nombre_lider
                    and x["Producto"] == r["Producto"]
                ),
                ("Sin pago (0%)", "")
            ),
            axis=1,
            result_type="expand"
        )

        tabla_lider["Observación"] = tabla_lider["Observación"].fillna("").astype(str)

        tabla_lider = st.data_editor(
            tabla_lider,
            column_config={
                "Tipo Pago Comisión": st.column_config.SelectboxColumn(
                    options=["Pago 100%", "Pago 90%", "Sin pago (0%)"]
                ),
                "Observación": st.column_config.TextColumn(width="large")
            },
            disabled=not es_director,
            use_container_width=True,
            key="editor_lider"
        )

        tablas_guardar.append(tabla_lider)

    # =====================
    # ASESORES (NORMALES)
    # =====================
    st.markdown("## 👥 Asesoras")

    df_asesores = df_cvs[
        (df_cvs["Rol"] == "ASESOR") &
        (~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS))
    ]

    for nombre, g in df_asesores.groupby("Nombre_Vendedor"):

        with st.expander(f"👤 {nombre}"):

            meta_p, ejec_p, pct_p = calcular_kpi_puntos(df_cvs, g, "ASESOR")

            st.metric("🎯 KPI Puntos", f"{int(ejec_p)} / {int(meta_p)}", f"{pct_p}%")

            tabla = construir_tabla_productos(g, maestro, df_cvs, "ASESOR")

            tabla["Nombre"] = nombre
            tabla["Rol"] = "ASESOR"
            tabla["CVS"] = cvs_sel
            tabla["Mes"] = mes_sel

            tabla[["Tipo Pago Comisión", "Observación"]] = tabla.apply(
                lambda r: next(
                    (
                        (x["Tipo Pago Comisión"], x["Observación"])
                        for x in st.session_state["historico_decisiones"]
                        if x["Mes"] == mes_sel
                        and x["CVS"] == cvs_sel
                        and x["Nombre"] == nombre
                        and x["Producto"] == r["Producto"]
                    ),
                    ("Sin pago (0%)", "")
                ),
                axis=1,
                result_type="expand"
            )

            tabla["Observación"] = tabla["Observación"].fillna("").astype(str)

            tabla = st.data_editor(
                tabla,
                column_config={
                    "Tipo Pago Comisión": st.column_config.SelectboxColumn(
                        options=["Pago 100%", "Pago 90%", "Sin pago (0%)"]
                    ),
                    "Observación": st.column_config.TextColumn(width="large")
                },
                disabled=not es_director,
                use_container_width=True,
                key=f"editor_{nombre}"
            )

            tablas_guardar.append(tabla)

    # =====================
    # SUPERNUMERARIOS
    # =====================
    df_supernumerarios = df_cvs[
        (df_cvs["Rol"] == "ASESOR") &
        (df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS))
    ]

    if not df_supernumerarios.empty:

        st.divider()
        st.markdown("## 🟡 Supernumerarios (Apoyo temporal)")

        for nombre, g in df_supernumerarios.groupby("Nombre_Vendedor"):

            with st.expander(f"🟡 {nombre} (Supernumerario)"):

                ejec_p = g["Puntos"].sum()

                st.metric("🎯 KPI Puntos", f"{int(ejec_p)} / 0", "No aplica")

                st.warning("No afecta KPI ni metas del CVS")

                tabla = construir_tabla_productos(g, maestro, df_cvs, "ASESOR")

                tabla["Nombre"] = nombre
                tabla["Rol"] = "SUPERNUMERARIO"
                tabla["CVS"] = cvs_sel
                tabla["Mes"] = mes_sel

                tabla[["Tipo Pago Comisión", "Observación"]] = tabla.apply(
                    lambda r: next(
                        (
                            (x["Tipo Pago Comisión"], x["Observación"])
                            for x in st.session_state["historico_decisiones"]
                            if x["Mes"] == mes_sel
                            and x["CVS"] == cvs_sel
                            and x["Nombre"] == nombre
                            and x["Producto"] == r["Producto"]
                        ),
                        ("Sin pago (0%)", "")
                    ),
                    axis=1,
                    result_type="expand"
                )

                tabla["Observación"] = tabla["Observación"].fillna("").astype(str)

                tabla = st.data_editor(
                    tabla,
                    column_config={
                        "Tipo Pago Comisión": st.column_config.SelectboxColumn(
                            options=["Pago 100%", "Pago 90%", "Sin pago (0%)"]
                        ),
                        "Observación": st.column_config.TextColumn(width="large")
                    },
                    disabled=not es_director,
                    use_container_width=True,
                    key=f"editor_super_{nombre}"
                )

                tablas_guardar.append(tabla)

    # =====================
    # 🔴 GUARDAR HISTÓRICO (CORREGIDO)
    # =====================
    st.divider()

    if es_director and st.button("💾 Guardar decisiones del CVS"):

        tablas_con_acc = []

        for tabla in tablas_guardar:

            tabla = tabla.copy()
            nombre = tabla["Nombre"].iloc[0]
            rol = tabla["Rol"].iloc[0]

            acc_valor = st.session_state.get(f"acc_{cvs_sel}_{nombre}", 100)
            tabla["ACC"] = acc_valor

            df_persona = df_f[
                (df_f["Sucursal"] == cvs_sel) &
                (df_f["Nombre_Vendedor"] == nombre)
            ]

            if nombre.upper() in SUPERNUMERARIOS:
                pct_kpi = 0
            else:
                _, _, pct_kpi = calcular_kpi_puntos(df_cvs, df_persona, rol)

            tabla["% Cumplimiento Puntos"] = pct_kpi

            tablas_con_acc.append(tabla)

        nuevas_decisiones = pd.concat(tablas_con_acc, ignore_index=True)

        if RUTA_HISTORICO.exists():
            df_historico = pd.read_excel(RUTA_HISTORICO)
        else:
            df_historico = pd.DataFrame(columns=nuevas_decisiones.columns)

        df_historico = df_historico[~(
            (df_historico["Mes"] == mes_sel) &
            (df_historico["CVS"] == cvs_sel)
        )]

        df_historico = pd.concat([df_historico, nuevas_decisiones], ignore_index=True)

        df_historico.to_excel(RUTA_HISTORICO, index=False)

        st.session_state["historico_decisiones"] = df_historico.to_dict("records")

        st.success("✅ Guardado correctamente")

    # =====================
    # DESCARGAR HISTÓRICO
    # =====================
    st.subheader("📊 Descargar histórico")

    if st.button("📥 Descargar histórico del mes"):

        df_hist = pd.DataFrame(st.session_state.get("historico_decisiones", []))
        df_hist = df_hist[df_hist["Mes"] == mes_sel]

        if not df_hist.empty:

            archivo_mes = DATA_DIR / f"Historico_Comisiones_{mes_sel}.xlsx"
            df_hist.to_excel(archivo_mes, index=False)

            with open(archivo_mes, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=f,
                    file_name=f"Historico_Comisiones_{mes_sel}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("⚠️ No hay datos para este mes")


# =======================
# TAB 3 – CUMPLIMIENTO GENERAL COORDINADOR Y SUPERVISORA
# =======================
# =========================
# TAB 3 – PANEL COORDINADOR
# =========================
with tab3:
    st.subheader("⚖️Cumplimiento General")

    # =========================
    # TOTALES GENERALES
    # =========================

    # Meta total (sin duplicar sucursal)
    meta_total = (
        df_f[["Sucursal", "Meta_General"]]
        .drop_duplicates()
        ["Meta_General"]
        .sum()
    )

    # Puntos totales
    puntos_total = df_f["Puntos"].sum()

    # Cantidad total
    cantidad_total = df_f["Cantidad"].sum()

    # % cumplimiento
    if meta_total > 0:
        pct_total = (puntos_total / meta_total) * 100
    else:
        pct_total = 0

    pct_total = round(pct_total, 1)

    # =========================
    # KPI SEMÁFORO
    # =========================
    if pct_total >= 100:
        color = "green"
        estado = "Excelente"
    elif pct_total >= 90:
        color = "orange"
        estado = "Aceptable"
    else:
        color = "red"
        estado = "Crítico"

    # =========================
    # PANEL SUPERIOR
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🎯 Meta total", f"{meta_total:,.0f}".replace(",", "."))
    col2.metric("⭐ Puntos totales", f"{puntos_total:,.0f}".replace(",", "."))
    col3.metric("📦 Cantidad total", f"{cantidad_total:,.0f}".replace(",", "."))
    col4.metric("📈 Cumplimiento", f"{pct_total} %")

    # Semáforo visual
    st.markdown(
        f"""
        <div style="background-color:{color};
                    padding:15px;
                    border-radius:10px;
                    text-align:center;
                    color:white;
                    font-size:20px;
                    font-weight:bold;">
            KPI General: {estado} ({pct_total}%)
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # =========================
    # RESUMEN POR PRODUCTO
    # =========================
    st.subheader("📦 Resumen por producto")

    resumen_prod = df_f.groupby("Producto").agg(
        Cantidad=("Cantidad", "sum"),
        Puntos=("Puntos", "sum")
    ).reset_index()

    st.dataframe(resumen_prod, use_container_width=True)
