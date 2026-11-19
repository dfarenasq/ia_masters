"""Motor del recomendador de TiendaDigital (datos simulados).
Se calcula una sola vez al importar el módulo; app.py solo consume los resultados."""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SEMILLA = 42
rng = np.random.default_rng(SEMILLA)

# ------------------------------------------------------------------ catálogo
CATALOGO = {
    "Computación":      {"tipos": ["Portátil", "Mouse inalámbrico", "Teclado mecánico", "Monitor", "Disco SSD", "Hub USB-C", "Webcam", "Base refrigerante"],
                         "marcas": ["Lenovo", "Logitech", "HP", "Kingston", "Samsung"], "precio": (60_000, 3_500_000),
                         "etiquetas": ["trabajo", "estudio", "productividad", "portatil", "escritorio"]},
    "Celulares":        {"tipos": ["Smartphone", "Cargador rápido", "Funda", "Protector de pantalla", "Power bank", "Cable USB-C", "Soporte para auto", "Tarjeta microSD"],
                         "marcas": ["Samsung", "Xiaomi", "Motorola", "Anker", "Baseus"], "precio": (15_000, 2_200_000),
                         "etiquetas": ["movil", "carga", "proteccion", "viaje", "android"]},
    "Audio":            {"tipos": ["Audífonos Bluetooth", "Parlante portátil", "Barra de sonido", "Micrófono USB", "Audífonos in-ear", "Adaptador de audio", "Soporte para parlante", "Diadema"],
                         "marcas": ["JBL", "Sony", "Edifier", "Logitech", "Anker"], "precio": (25_000, 1_200_000),
                         "etiquetas": ["musica", "inalambrico", "sonido", "podcast", "streaming"]},
    "Gaming":           {"tipos": ["Control inalámbrico", "Silla gamer", "Mouse gamer", "Teclado gamer", "Audífonos gamer", "Tarjeta de video", "Mousepad XL", "Capturadora de video"],
                         "marcas": ["Razer", "Redragon", "Logitech", "HyperX", "Corsair"], "precio": (40_000, 4_500_000),
                         "etiquetas": ["juegos", "rgb", "competitivo", "consola", "pc"]},
    "Oficina":          {"tipos": ["Impresora multifuncional", "Silla ergonómica", "Escritorio", "Lámpara LED", "Calculadora científica", "Trituradora de papel", "Organizador de escritorio", "Proyector"],
                         "marcas": ["Epson", "Canon", "HP", "Brother", "Casio"], "precio": (20_000, 2_800_000),
                         "etiquetas": ["trabajo", "ergonomia", "oficina", "documentos", "reunion"]},
    "Papelería":        {"tipos": ["Cuaderno universitario", "Resma de papel", "Set de marcadores", "Agenda", "Bolígrafos x12", "Carpeta archivadora", "Calculadora básica", "Pegante y tijeras"],
                         "marcas": ["Norma", "Faber-Castell", "Pelikan", "Scribe", "Bic"], "precio": (3_000, 120_000),
                         "etiquetas": ["escolar", "estudio", "escritura", "organizacion", "colegio"]},
    "Hogar inteligente": {"tipos": ["Bombillo WiFi", "Cámara de seguridad", "Enchufe inteligente", "Timbre con cámara", "Router WiFi 6", "Asistente de voz", "Sensor de movimiento", "Tira LED"],
                          "marcas": ["TP-Link", "Xiaomi", "Philips", "Ring", "Tuya"], "precio": (18_000, 700_000),
                          "etiquetas": ["casa", "seguridad", "automatizacion", "wifi", "ahorro"]},
    "Accesorios":       {"tipos": ["Morral para portátil", "Maletín", "Cable HDMI", "Regleta", "Adaptador multipuerto", "Soporte para monitor", "Limpiador de pantallas", "Candado para portátil"],
                         "marcas": ["Targus", "Baseus", "Ugreen", "Samsonite", "Anker"], "precio": (8_000, 450_000),
                         "etiquetas": ["transporte", "conexion", "proteccion", "viaje", "escritorio"]},
}
CATEGORIAS = list(CATALOGO)

filas = []
for cat, info in CATALOGO.items():
    for tipo in info["tipos"]:
        for marca in rng.choice(info["marcas"], size=2, replace=False):
            et = rng.choice(info["etiquetas"], size=2, replace=False)
            lo, hi = info["precio"]
            precio = int(np.exp(rng.uniform(np.log(lo), np.log(hi))) // 1000 * 1000)
            filas.append({"nombre": f"{tipo} {marca}", "categoria": cat, "tipo": tipo, "marca": marca,
                          "etiquetas": " ".join(et), "precio": max(precio, 1000)})
productos = pd.DataFrame(filas).reset_index(names="product_id")
N_ITEMS = len(productos)

# ------------------------------------------------- usuarios e interacciones
N_USERS = 300
PESO_EVENTO = {"vista": 1, "carrito": 3, "compra": 5}
NOMBRE_EVENTO = {v: k for k, v in PESO_EVENTO.items()}

favoritas = {u: [str(c) for c in rng.choice(CATEGORIAS, size=2, replace=False)] for u in range(N_USERS)}
pop_intrinseca = rng.lognormal(mean=0, sigma=1.0, size=N_ITEMS)
cat_arr = productos["categoria"].to_numpy()

registros = []
for u in range(N_USERS):
    n_eventos = int(rng.integers(20, 46))
    mascara_fav = np.isin(cat_arr, favoritas[u])
    for _ in range(n_eventos):
        pool = mascara_fav if rng.random() < 0.75 else np.ones(N_ITEMS, dtype=bool)
        p = pop_intrinseca * pool
        item = int(rng.choice(N_ITEMS, p=p / p.sum()))
        evento = rng.choice(["vista", "carrito", "compra"], p=[0.60, 0.25, 0.15])
        registros.append({"user_id": u, "product_id": item, "evento": evento, "dia": int(rng.integers(0, 90))})

crudo = pd.DataFrame(registros)
crudo["peso"] = crudo["evento"].map(PESO_EVENTO)
interacciones = (crudo.sort_values(["peso", "dia"]).groupby(["user_id", "product_id"], as_index=False)
                      .agg(peso=("peso", "max"), dia=("dia", "max")))
interacciones["evento"] = interacciones["peso"].map(NOMBRE_EVENTO)

# --------------------------------------------- entrenamiento / prueba (tiempo)
train_rows, test_rows = [], []
for u, g in interacciones.sort_values("dia").groupby("user_id"):
    n_test = max(1, int(round(len(g) * 0.20)))
    train_rows.append(g.iloc[:-n_test])
    test_rows.append(g.iloc[-n_test:])
train, test = pd.concat(train_rows), pd.concat(test_rows)

R = np.zeros((N_USERS, N_ITEMS))
R[train["user_id"], train["product_id"]] = train["peso"]
relevantes = test[test["peso"] >= 3].groupby("user_id")["product_id"].apply(set).to_dict()

# -------------------------------------------------------------- componentes
POP = R.sum(axis=0)
texto = (productos["categoria"] + " " + productos["categoria"] + " " + productos["tipo"] + " "
         + productos["marca"] + " " + productos["etiquetas"]).str.lower()
X = TfidfVectorizer().fit_transform(texto).toarray()
S = cosine_similarity(R.T)
np.fill_diagonal(S, 0)
SIM_EXPLICAR = 0.5 * S + 0.5 * cosine_similarity(X)
np.fill_diagonal(SIM_EXPLICAR, 0)

W_NORMAL = {"colaborativo": 0.50, "contenido": 0.30, "popularidad": 0.20}
W_FRIO = {"colaborativo": 0.10, "contenido": 0.30, "popularidad": 0.60}
UMBRAL_FRIO = 5
MODELOS = ["popularidad", "contenido", "colaborativo", "hibrido"]


def _norm(v, vistos):
    sin_ver = v[~vistos]
    return (v - sin_ver.min()) / (sin_ver.max() - sin_ver.min() + 1e-9)


def puntajes(r):
    """Puntaje de cada producto según cada modelo, dado el vector de interacciones r (n_items,)."""
    vistos = r > 0
    cont = cosine_similarity((r @ X).reshape(1, -1), X)[0] if vistos.any() else np.zeros(N_ITEMS)
    cf = r @ S
    w = W_FRIO if vistos.sum() < UMBRAL_FRIO else W_NORMAL
    hib = (w["colaborativo"] * _norm(cf, vistos) + w["contenido"] * _norm(cont, vistos)
           + w["popularidad"] * _norm(POP, vistos))
    return {"popularidad": POP.copy(), "contenido": cont, "colaborativo": cf, "hibrido": hib}, vistos


def recomendar(r, modelo, k=5):
    sc, vistos = puntajes(r)
    s = np.where(vistos, -np.inf, sc[modelo])
    return [int(i) for i in np.argsort(-s)[:k]]


def explicar(r, i):
    """Texto corto: por qué se recomienda el producto i a quien tiene el historial r."""
    comprados = np.where(r > 0)[0]
    if len(comprados) == 0:
        return "Popular en la tienda"
    aporte = r[comprados] * SIM_EXPLICAR[i, comprados]
    if aporte.max() <= 0:
        return "Popular en la tienda"
    j = comprados[aporte.argmax()]
    return f"Similar a «{productos.loc[j, 'nombre']}» (tuvo {NOMBRE_EVENTO[int(r[j])]})"


def historial(u):
    return (train[train["user_id"] == u].merge(productos, on="product_id")
            .sort_values(["peso", "dia"], ascending=False))


# --------------------------------------------------------------- evaluación
def _metricas_usuario(rec, rel, k):
    hits = [1 if i in rel else 0 for i in rec[:k]]
    dcg = sum(h / np.log2(pos + 2) for pos, h in enumerate(hits))
    idcg = sum(1 / np.log2(pos + 2) for pos in range(min(len(rel), k)))
    return sum(hits) / k, sum(hits) / len(rel), dcg / idcg


def _afinidad(u, rec):
    cats = historial(u).groupby("categoria")["peso"].sum().nlargest(2).index
    return np.mean([productos.loc[i, "categoria"] in cats for i in rec])


def evaluar(k=5):
    filas = []
    for m in MODELOS:
        res, vistos_rec = [], set()
        for u, rel in relevantes.items():
            rec = recomendar(R[u], m, k)
            vistos_rec.update(rec)
            res.append((*_metricas_usuario(rec, rel, k), _afinidad(u, rec)))
        p, rc, n, a = np.mean(res, axis=0)
        filas.append({"modelo": m, f"Precision@{k}": p, f"Recall@{k}": rc, f"NDCG@{k}": n,
                      "Afinidad de categoría": a, "Cobertura de catálogo": len(vistos_rec) / N_ITEMS})
    return pd.DataFrame(filas).set_index("modelo")


RESULTADOS = {5: evaluar(5), 10: evaluar(10)}


def componentes(r):
    """Desglose del híbrido: aporte (ya ponderado) de cada modelo al puntaje final de cada producto.
    Sirve para explicar visualmente POR QUÉ el híbrido recomienda lo que recomienda."""
    vistos = r > 0
    cont = cosine_similarity((r @ X).reshape(1, -1), X)[0] if vistos.any() else np.zeros(N_ITEMS)
    cf = r @ S
    w = W_FRIO if vistos.sum() < UMBRAL_FRIO else W_NORMAL
    return {"colaborativo": w["colaborativo"] * _norm(cf, vistos),
            "contenido": w["contenido"] * _norm(cont, vistos),
            "popularidad": w["popularidad"] * _norm(POP, vistos)}, w


def pesos_activos(r):
    return W_FRIO if (r > 0).sum() < UMBRAL_FRIO else W_NORMAL


def resumen_datos():
    return {"usuarios": N_USERS, "productos": N_ITEMS, "categorias": len(CATEGORIAS),
            "interacciones": len(interacciones), "densidad": len(interacciones) / (N_USERS * N_ITEMS),
            "entrenamiento": len(train), "prueba": len(test), "evaluables": len(relevantes)}


def dataset_csv():
    """Tabla única (una fila por interacción, con los datos del producto) lista para exportar a CSV."""
    cols = ["user_id", "product_id", "nombre", "categoria", "tipo", "marca", "etiquetas", "precio", "evento", "peso", "dia"]
    return interacciones.merge(productos, on="product_id")[cols]
