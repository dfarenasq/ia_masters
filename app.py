"""TiendaDigital · Recomendador — demo visual (Streamlit).
Ejecutar:  streamlit run app.py     (necesita modelo.py en la misma carpeta)"""
import html

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import modelo as m

st.set_page_config(page_title="TiendaDigital · Recomendador", page_icon="🛒", layout="wide")

# ------------------------------------------------------------------ constantes visuales
NOMBRES = {"popularidad": "Popularidad", "contenido": "Contenido", "colaborativo": "Colaborativo", "hibrido": "Híbrido"}
DESCRIPCION = {
    "popularidad": "Lo más comprado de la tienda. Igual para todos.",
    "contenido": "Productos parecidos a los que el usuario ya miró.",
    "colaborativo": "«Quienes compraron X también compraron Y».",
    "hibrido": "Mezcla de los tres, con pesos ajustados al usuario.",
}
CAT_COLOR = {"Computación": "#4C78A8", "Celulares": "#F58518", "Audio": "#B279A2", "Gaming": "#E45756",
             "Oficina": "#72B7B2", "Papelería": "#EECA3B", "Hogar inteligente": "#54A24B", "Accesorios": "#9D755D"}
CAT_EMOJI = {"Computación": "💻", "Celulares": "📱", "Audio": "🎧", "Gaming": "🎮",
             "Oficina": "🖨️", "Papelería": "📝", "Hogar inteligente": "🏠", "Accesorios": "🎒"}
EVENTO_EMOJI = {"vista": "👁️ vista", "carrito": "🛒 carrito", "compra": "✅ compra"}
COMP_COLOR = {"colaborativo": "#4C78A8", "contenido": "#F58518", "popularidad": "#9D9D9D"}
MODELO_COLOR = ["#9D9D9D", "#F58518", "#4C78A8", "#54A24B"]

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
.kpi {border:1px solid rgba(128,128,128,.28); border-radius:14px; padding:12px 16px; background:rgba(128,128,128,.07);}
.kpi .v {font-size:1.7rem; font-weight:700; line-height:1.2;}
.kpi .l {font-size:.78rem; opacity:.7; text-transform:uppercase; letter-spacing:.05em;}
.card {border:1px solid rgba(128,128,128,.28); border-radius:14px; padding:14px 14px 12px 14px;
       background:rgba(128,128,128,.06); height:265px; overflow:hidden;}
.card.hit {border:2px solid #2ca02c; background:rgba(44,160,44,.09);}
.chip {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.72rem; font-weight:600; color:#fff;}
.rank {font-size:.8rem; opacity:.6; font-weight:600;}
.pname {font-size:1.02rem; font-weight:700; margin:6px 0 2px 0; line-height:1.25;}
.price {font-size:.95rem; opacity:.85;}
.why {font-size:.8rem; opacity:.8; margin-top:8px; line-height:1.35;}
.bar {height:6px; border-radius:6px; background:rgba(128,128,128,.25); margin-top:10px; overflow:hidden;}
.bar > div {height:100%; background:#4C78A8;}
.badge {font-size:.75rem; font-weight:700; color:#2ca02c; margin-top:8px;}
.step {border:1px solid rgba(128,128,128,.28); border-radius:14px; padding:14px; background:rgba(128,128,128,.06); height:100%;}
.step .n {font-size:.75rem; font-weight:700; opacity:.6;}
.step .t {font-weight:700; margin:2px 0 6px 0;}
.step .d {font-size:.84rem; opacity:.85; line-height:1.4;}
.pill {display:inline-block; padding:3px 12px; border-radius:999px; font-size:.78rem; font-weight:600;
       border:1px solid rgba(128,128,128,.4); margin-right:6px;}
</style>
""", unsafe_allow_html=True)


def kpi(col, valor, etiqueta):
    col.markdown(f'<div class="kpi"><div class="v">{valor}</div><div class="l">{etiqueta}</div></div>', unsafe_allow_html=True)


def chip(cat):
    return f'<span class="chip" style="background:{CAT_COLOR[cat]}">{CAT_EMOJI[cat]} {html.escape(cat)}</span>'


def precio(x):
    return "$" + f"{int(x):,}".replace(",", ".")


def tarjeta(pos, i, score, score_max, motivo, acierto):
    p = m.productos.loc[i]
    ancho = 0 if score_max <= 0 else max(4, int(100 * score / score_max))
    extra = '<div class="badge">✓ Lo puso en carrito/compró después</div>' if acierto else ""
    return f"""<div class="card {'hit' if acierto else ''}">
      <div class="rank">#{pos}</div>{chip(p['categoria'])}
      <div class="pname">{html.escape(p['nombre'])}</div>
      <div class="price">{precio(p['precio'])} COP</div>
      <div class="bar"><div style="width:{ancho}%"></div></div>
      <div class="why">{html.escape(motivo)}</div>{extra}</div>"""


def cuadricula(rec, r, modelo_id, u):
    sc, _ = m.puntajes(r)
    puntos = [sc[modelo_id][i] for i in rec]
    tope = max(puntos) if puntos else 1
    for fila in range(0, len(rec), 5):
        cols = st.columns(5)
        for c, (pos, i) in zip(cols, list(enumerate(rec, 1))[fila:fila + 5]):
            motivo = m.explicar(r, i) if modelo_id in ("hibrido", "colaborativo") else DESCRIPCION[modelo_id]
            c.markdown(tarjeta(pos, i, sc[modelo_id][i], tope, motivo, u is not None and i in m.relevantes.get(u, set())),
                       unsafe_allow_html=True)
        st.write("")


# ------------------------------------------------------------------ encabezado y KPIs
st.title("🛒 TiendaDigital · Sistema de recomendación")
st.caption("Prototipo con datos simulados · Referencia de diseño: sistema de recomendación de Netflix (Gomez-Uribe y Hunt, 2015)")
d = m.resumen_datos()
k1, k2, k3, k4, k5 = st.columns(5)
kpi(k1, d["usuarios"], "usuarios"); kpi(k2, d["productos"], "productos")
kpi(k3, f'{d["interacciones"]:,}'.replace(",", "."), "interacciones")
kpi(k4, f'{d["densidad"]:.0%}', "densidad de la matriz"); kpi(k5, f'{d["prueba"]:,}'.replace(",", "."), "interacciones ocultas (prueba)")
st.write("")

# ------------------------------------------------------------------ barra lateral
st.sidebar.header("🎛️ Controles")
modo = st.sidebar.radio("Tipo de usuario", ["Usuario existente", "Usuario nuevo (arranque en frío)"])
modelo_sel = st.sidebar.radio("Modelo", m.MODELOS, index=3, format_func=NOMBRES.get)
st.sidebar.caption(DESCRIPCION[modelo_sel])
k = st.sidebar.slider("Cantidad de recomendaciones", 5, 10, 5)

u = None
if modo.startswith("Usuario existente"):
    evaluables = sorted(m.relevantes)
    u = st.sidebar.selectbox("Usuario", evaluables, index=evaluables.index(217))
    r = m.R[u]
    hist = m.historial(u)
    etiqueta_user = f"Usuario {u}"
else:
    nuevos = m.productos["product_id"].tolist()
    por_defecto = [int(m.productos[m.productos["tipo"] == "Cuaderno universitario"].iloc[0]["product_id"])]
    elegidos = st.sidebar.multiselect("Productos con los que interactuó (máx. 3)", nuevos, default=por_defecto, max_selections=3,
                                      format_func=lambda i: f"{m.productos.loc[i, 'nombre']} · {m.productos.loc[i, 'categoria']}")
    accion = st.sidebar.selectbox("Tipo de interacción", list(m.PESO_EVENTO), index=2)
    r = np.zeros(m.N_ITEMS)
    for i in elegidos:
        r[i] = m.PESO_EVENTO[accion]
    hist = None
    etiqueta_user = "Usuario nuevo"

w = m.pesos_activos(r)
frio = (r > 0).sum() < m.UMBRAL_FRIO
st.markdown(f"### {etiqueta_user}")
st.markdown(
    f'<span class="pill">{"❄️ Arranque en frío" if frio else "🔥 Historial suficiente"}</span>'
    f'<span class="pill">Pesos del híbrido → colaborativo {w["colaborativo"]:.0%} · contenido {w["contenido"]:.0%} · popularidad {w["popularidad"]:.0%}</span>',
    unsafe_allow_html=True)
st.write("")

t0, t1, t2, t3, t4, t5 = st.tabs(["🧭 Cómo funciona", "👤 Perfil", "⭐ Recomendaciones", "🔍 Por qué el híbrido",
                                   "⚖️ Comparar modelos", "📊 Evaluación"])

# ------------------------------------------------------------------ 0. cómo funciona
with t0:
    st.markdown("#### El recorrido de los datos, de principio a fin")
    pasos = [("1", "Datos", "Catálogo de 128 productos y el historial de cada usuario: vista (1), carrito (3) o compra (5)."),
             ("2", "Entrenar / probar", "El 20 % más reciente de cada usuario se oculta. Es el «futuro» que luego intentamos adivinar."),
             ("3", "Tres señales", "Popularidad, parecido de contenido (TF-IDF) y comportamiento de otros usuarios (ítem-ítem)."),
             ("4", "Híbrido", "Se normalizan los puntajes y se combinan con pesos. Con poco historial, pesa más la popularidad."),
             ("5", "Top-K + motivo", "Se ordenan los productos que el usuario aún no ha visto y se muestra por qué se sugieren.")]
    for c, (n, t, desc) in zip(st.columns(5), pasos):
        c.markdown(f'<div class="step"><div class="n">PASO {n}</div><div class="t">{t}</div><div class="d">{desc}</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("#### Los cuatro enfoques")
    st.dataframe(pd.DataFrame({
        "Enfoque": [NOMBRES[x] for x in m.MODELOS],
        "Qué hace": [DESCRIPCION[x] for x in m.MODELOS],
        "Fortaleza": ["Funciona sin historial", "Sirve con productos nuevos", "Descubre relaciones no obvias", "Compensa las debilidades de los otros"],
        "Debilidad": ["Casi no cubre el catálogo", "Encierra al usuario en lo conocido", "Falla con usuarios nuevos", "Más parámetros por ajustar"]}),
        hide_index=True)
    st.info("**Idea tomada de Netflix:** ningún algoritmo basta solo. Combinar señales y medir con datos que el modelo no vio es lo que "
            "permite saber si la recomendación realmente sirve.")

# ------------------------------------------------------------------ 1. perfil
with t1:
    if u is not None:
        c1, c2 = st.columns([1, 1.15])
        pc = hist.groupby("categoria")["peso"].sum().reset_index().sort_values("peso", ascending=False)
        graf = (alt.Chart(pc).mark_bar(cornerRadiusEnd=4)
                .encode(x=alt.X("peso:Q", title="Peso acumulado (vista=1, carrito=3, compra=5)"),
                        y=alt.Y("categoria:N", sort="-x", title=None),
                        color=alt.Color("categoria:N", scale=alt.Scale(domain=list(CAT_COLOR), range=list(CAT_COLOR.values())), legend=None),
                        tooltip=["categoria", "peso"]).properties(height=280))
        with c1:
            st.markdown("**Lo que el sistema deduce del historial**")
            st.altair_chart(graf)
            with st.expander("Revelar las categorías favoritas reales del usuario (simuladas)"):
                st.write("El sistema **no** conoce esto; se usó para generar los datos. Sirve para comprobar si lo deduce bien:",
                         ", ".join(m.favoritas[u]))
        with c2:
            st.markdown(f"**Historial de entrenamiento** · {len(hist)} productos, de mayor a menor interés")
            tabla = hist[["nombre", "categoria", "evento", "precio"]].copy()
            tabla["evento"] = tabla["evento"].map(EVENTO_EMOJI)
            tabla["precio"] = tabla["precio"].map(precio)
            tabla.columns = ["Producto", "Categoría", "Acción", "Precio"]
            st.dataframe(tabla.reset_index(drop=True), hide_index=True, height=320)
    else:
        if r.sum() == 0:
            st.info("Elige al menos un producto en la barra lateral.")
        else:
            idx = np.where(r > 0)[0]
            st.markdown("**Historial del usuario nuevo** (solo lo que eligió en la barra lateral)")
            st.dataframe(pd.DataFrame({"Producto": [m.productos.loc[i, "nombre"] for i in idx],
                                       "Categoría": [m.productos.loc[i, "categoria"] for i in idx],
                                       "Acción": [EVENTO_EMOJI[m.NOMBRE_EVENTO[int(r[i])]] for i in idx]}), hide_index=True)
            st.caption("Con menos de 5 interacciones el híbrido deja de confiar en el comportamiento de otros usuarios y se apoya en la popularidad.")

# ------------------------------------------------------------------ 2. recomendaciones
with t2:
    if r.sum() == 0:
        st.info("Elige al menos un producto en la barra lateral.")
    else:
        st.markdown(f"**Top {k} · modelo {NOMBRES[modelo_sel]}**")
        rec = m.recomendar(r, modelo_sel, k)
        cuadricula(rec, r, modelo_sel, u)
        if u is not None:
            ac = sum(i in m.relevantes.get(u, set()) for i in rec)
            st.success(f"{ac} de {k} recomendaciones coinciden con lo que el usuario realmente puso en carrito o compró en el periodo de prueba "
                       "(datos que el modelo nunca vio).")
        st.caption("La barra de cada tarjeta muestra el puntaje relativo dentro de esta lista.")

# ------------------------------------------------------------------ 3. por qué el híbrido
with t3:
    if r.sum() == 0:
        st.info("Elige al menos un producto en la barra lateral.")
    else:
        st.markdown("**¿De dónde sale el puntaje de cada recomendación del híbrido?**")
        rec_h = m.recomendar(r, "hibrido", k)
        comp, _ = m.componentes(r)
        filas = [{"Producto": f"{pos}. {m.productos.loc[i, 'nombre']}", "Señal": NOMBRES[s], "Aporte": float(comp[s][i]), "orden": pos}
                 for pos, i in enumerate(rec_h, 1) for s in ("colaborativo", "contenido", "popularidad")]
        df = pd.DataFrame(filas)
        graf = (alt.Chart(df).mark_bar()
                .encode(y=alt.Y("Producto:N", sort=alt.SortField("orden"), title=None, axis=alt.Axis(labelLimit=260)),
                        x=alt.X("Aporte:Q", title="Aporte al puntaje final (0 a 1)"),
                        color=alt.Color("Señal:N", title=None, legend=alt.Legend(orient="bottom"), scale=alt.Scale(domain=["Colaborativo", "Contenido", "Popularidad"],
                                                                    range=[COMP_COLOR["colaborativo"], COMP_COLOR["contenido"], COMP_COLOR["popularidad"]])),
                        tooltip=["Producto", "Señal", alt.Tooltip("Aporte:Q", format=".3f")]).properties(height=36 * len(rec_h) + 60))
        st.altair_chart(graf)
        st.caption(f"Pesos activos para este usuario: colaborativo {w['colaborativo']:.0%}, contenido {w['contenido']:.0%}, popularidad {w['popularidad']:.0%}. "
                   "Cambia a «Usuario nuevo» y observa cómo la barra gris (popularidad) crece cuando hay poco historial.")

# ------------------------------------------------------------------ 4. comparar modelos
with t4:
    if r.sum() == 0:
        st.info("Elige al menos un producto en la barra lateral.")
    else:
        st.markdown("**Los cuatro enfoques para el mismo usuario**")
        cols = st.columns(4)
        for col, mid in zip(cols, m.MODELOS):
            rec = m.recomendar(r, mid, k)
            with col:
                st.markdown(f"##### {NOMBRES[mid]}")
                if u is not None:
                    ac = sum(i in m.relevantes.get(u, set()) for i in rec)
                    st.metric("Aciertos", f"{ac} de {k}")
                for pos, i in enumerate(rec, 1):
                    p = m.productos.loc[i]
                    hit = u is not None and i in m.relevantes.get(u, set())
                    fondo = "rgba(44,160,44,.15)" if hit else "rgba(128,128,128,.07)"
                    col.markdown(f'<div style="border-left:5px solid {CAT_COLOR[p["categoria"]]};background:{fondo};border-radius:8px;'
                                 f'padding:6px 10px;margin-bottom:6px;font-size:.86rem"><b>{pos}.</b> {html.escape(p["nombre"])}'
                                 f'{" ✓" if hit else ""}<br><span style="opacity:.65;font-size:.75rem">{CAT_EMOJI[p["categoria"]]} {html.escape(p["categoria"])}</span></div>',
                                 unsafe_allow_html=True)
        if u is not None:
            st.divider()
            st.markdown("**Lo que el usuario realmente puso en carrito o compró después:** " +
                        ", ".join(m.productos.loc[i, "nombre"] for i in sorted(m.relevantes.get(u, set()))))
            st.caption("✓ y fondo verde = acierto.")

# ------------------------------------------------------------------ 5. evaluación
with t5:
    kk = st.radio("K (cantidad de recomendaciones evaluadas)", [5, 10], horizontal=True)
    res = m.RESULTADOS[kk].rename(index=NOMBRES)
    st.caption(f"Evaluado sobre {d['evaluables']} usuarios con al menos un carrito o compra en el periodo de prueba.")
    a, b = st.columns(2)
    for col, titulo, cols_m in [(a, "Precisión de las recomendaciones", [f"Precision@{kk}", f"Recall@{kk}", f"NDCG@{kk}"]),
                                (b, "Relevancia y cobertura", ["Afinidad de categoría", "Cobertura de catálogo"])]:
        largo = res[cols_m].reset_index().melt("modelo", var_name="Métrica", value_name="Valor")
        graf = (alt.Chart(largo).mark_bar(cornerRadiusEnd=3)
                .encode(x=alt.X("Métrica:N", title=None, axis=alt.Axis(labelAngle=0, labelLimit=200), sort=cols_m),
                        xOffset="modelo:N", y=alt.Y("Valor:Q", scale=alt.Scale(domain=[0, 1])),
                        color=alt.Color("modelo:N", title=None, legend=alt.Legend(orient="bottom"), sort=[NOMBRES[x] for x in m.MODELOS],
                                        scale=alt.Scale(domain=[NOMBRES[x] for x in m.MODELOS], range=MODELO_COLOR)),
                        tooltip=["modelo", "Métrica", alt.Tooltip("Valor:Q", format=".3f")]).properties(height=330))
        with col:
            st.markdown(f"**{titulo}**")
            st.altair_chart(graf)
    st.dataframe(res.style.format("{:.3f}").highlight_max(axis=0, color="rgba(44,160,44,.3)"))
    ganador = res[f"Precision@{kk}"].idxmax()
    base = res.loc["Popularidad", f"Precision@{kk}"]
    st.success(f"Mejor precisión: **{ganador}** ({res.loc[ganador, f'Precision@{kk}']:.3f}), frente a {base:.3f} de «lo más vendido».")
    st.warning("Datos simulados: las cifras sirven para **comparar** modelos entre sí, no como desempeño real de una tienda. "
               "Además, el contenido acierta la categoría pero casi nunca el producto exacto, y el sesgo hacia lo popular no desaparece del todo.")
