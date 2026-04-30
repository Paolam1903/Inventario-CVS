import pandas as pd

# =====================
# REGLA DE DISTRIBUCIÓN
# =====================
def calcular_distribucion(n_asesores, cvs):
    # Regla especial para Frontino
    if str(cvs).upper() == "FRONTINO":
        return 0.40, 0.60
    
    # Si no hay asesores, el líder cumple al 100%
    if n_asesores == 0:
        return 1.0, 1.0  # 100% meta productos, 100% meta general

    # Reglas normales
    if n_asesores == 1:
        return 0.40, 0.60
    elif n_asesores == 2:
        return 0.25, 0.375
    elif n_asesores >= 3:
        return 0.20, 0.266
    else:
        return 1.0, 0.0



# =================================================
# META GENERAL + EJECUCIÓN (RESUMEN POR CVS)
# =================================================
def resumen_meta_general_por_cvs(df):
    resultados = []

    for sucursal, grupo in df.groupby("Sucursal"):
        meta_total = grupo["Meta_General"].iloc[0]

        n_asesores = grupo[grupo["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()
        pct_lider, pct_asesores = calcular_distribucion(n_asesores, sucursal)


        puntos_lider = grupo[grupo["Rol"] == "LIDER"]["Puntos"].sum()
        puntos_asesores = grupo[grupo["Rol"] == "ASESOR"]["Puntos"].sum()

        resultados.append({
            "Sucursal": sucursal,
            "Estructura": f"1 Líder + {n_asesores} Asesor(es)",

            "Meta CVS": meta_total,

            "Meta Líder": meta_total * pct_lider,
            "Ejecutado Líder": puntos_lider,
            "Cumplimiento Líder %": round(
                (puntos_lider / (meta_total * pct_lider)) * 100, 2
            ) if meta_total * pct_lider > 0 else 0,

            "Meta Asesores": meta_total * pct_asesores,
            "Ejecutado Asesores": puntos_asesores,
            "Cumplimiento Asesores %": round(
                (puntos_asesores / (meta_total * pct_asesores)) * 100, 2
            ) if meta_total * pct_asesores > 0 else 0,
        })

    return pd.DataFrame(resultados)


# =================================================
# KPI POR PRODUCTO + EJECUCIÓN (RESUMEN POR CVS)
# =================================================
def resumen_kpi_producto_por_cvs(df):
    resultados = []

    for (sucursal, producto), grupo in df.groupby(["Sucursal", "Producto"]):
        meta_producto = grupo["Meta_Producto"].iloc[0]

        n_asesores = grupo[grupo["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()
        pct_lider, pct_asesores = calcular_distribucion(n_asesores, sucursal)


        puntos_lider = grupo[grupo["Rol"] == "LIDER"]["Puntos"].sum()
        puntos_asesores = grupo[grupo["Rol"] == "ASESOR"]["Puntos"].sum()

        resultados.append({
            "Sucursal": sucursal,
            "Producto": producto,

            "Meta Producto": meta_producto,

            "Meta Líder": meta_producto * pct_lider,
            "Ejecutado Líder": puntos_lider,
            "Cumplimiento Líder %": round(
                (puntos_lider / (meta_producto * pct_lider)) * 100, 2
            ) if meta_producto * pct_lider >= 0 else 0,

            "Meta Asesores": meta_producto * pct_asesores,
            "Ejecutado Asesores": puntos_asesores,
            "Cumplimiento Asesores %": round(
                (puntos_asesores / (meta_producto * pct_asesores)) * 100, 2
            ) if meta_producto * pct_asesores >= 0 else 0,
        })

    return pd.DataFrame(resultados)
