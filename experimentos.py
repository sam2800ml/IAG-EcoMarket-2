"""Experimentos: modificar el código o el prompt y observar cómo cambia el comportamiento.

    1. Sin RAG vs. con RAG          -> mismo modelo, misma pregunta; cambia si hay contexto recuperado.
    2. Estrategias de segmentación  -> fijo vs. párrafos vs. recursivo vs. estructural+recursivo,
                                       y tamaños de chunk (solo recuperación, medido con aciertos).
    3. Prompt estricto vs. permisivo -> preguntas cuya respuesta NO está en la base de conocimiento.

Uso:
    python experimentos.py          # los tres
    python experimentos.py 2        # solo uno
Los resultados se guardan en resultados/experimento_N.md
"""

import re
import sys
import time
import unicodedata
from datetime import datetime

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src import config, prompts
from src.extraccion import cargar_politicas, texto_pdf
from src.indexacion import cargar_almacen, obtener_embeddings
from src.llm import cadena_texto, ejecutar
from src.recuperacion import buscar, formatear_contexto, recuperar
from src.segmentacion import (estrategia_estructural_recursiva, estrategia_parrafos, estrategia_recursiva,
                              estrategia_tamano_fijo)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)


def _guardar(numero: int, titulo: str, cuerpo: list[str]) -> None:
    config.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    ruta = config.CARPETA_RESULTADOS / f"experimento_{numero}.md"
    encabezado = (f"# Experimento {numero}: {titulo}\n\nModelo: `{config.MODELO_LLM}` · Embeddings: "
                  f"`{config.MODELO_EMBEDDINGS}` · Generado: {datetime.now():%Y-%m-%d %H:%M}\n")
    ruta.write_text(encabezado + "\n" + "\n".join(cuerpo), encoding="utf-8")
    print(f"\n✅ Guardado en {ruta.relative_to(config.RAIZ)}")


def _cita(texto: str) -> str:
    return "> " + texto.strip().replace("\n", "\n> ")


# EXPERIMENTO 1 · Sin RAG vs. con RAG
PREGUNTAS_E1 = [
    ("¿Cuántos días tengo para devolver un producto?", "30 dias"),
    ("¿Desde qué valor de compra el envío es gratis?", "150.000"),
    ("¿Cuánto cuesta el panel solar portátil y qué puertos tiene?", "320.000"),
    ("¿Puedo pagar contra entrega?", "no aceptamos"),
    ("¿Tienen tienda física donde pueda recoger mi pedido?", "en linea"),
]


def experimento_1() -> None:
    print("\n=== Experimento 1: sin RAG vs. con RAG ===")
    almacen = cargar_almacen()
    sin_rag = cadena_texto(prompts.SIN_RAG, temperatura=0.2)
    con_rag = cadena_texto(prompts.RAG_RESPUESTA, temperatura=0.2)
    md = ["Mismo modelo, misma pregunta y misma temperatura. Lo único que cambia es si el prompt recibe "
          "los fragmentos recuperados de Qdrant.\n",
          "La columna *dato esperado* es una verificación automática aproximada: revisa si la respuesta "
          "contiene el dato correcto de la base de conocimiento. Conviene leer las respuestas completas.\n",
          "| Pregunta | Dato esperado | Sin RAG | Con RAG |", "|---|---|---|---|"]
    detalle = []
    for pregunta, dato in PREGUNTAS_E1:
        print(f"\n❓ {pregunta}")
        r_sin = ejecutar(sin_rag, {"pregunta": pregunta})
        fuentes = recuperar(almacen, pregunta)
        r_con = ejecutar(con_rag, {"contexto": formatear_contexto(fuentes), "pregunta": pregunta}) if fuentes \
            else prompts.SIN_INFORMACION
        ok_sin, ok_con = (("✅" if _normalizar(dato) in _normalizar(r) else "❌") for r in (r_sin, r_con))
        print(f"   Sin RAG {ok_sin}: {r_sin}\n   Con RAG {ok_con}: {r_con}")
        md.append(f"| {pregunta} | `{dato}` | {ok_sin} | {ok_con} |")
        detalle += [f"### {pregunta}\n", "**Sin RAG:**\n", _cita(r_sin), "\n**Con RAG:**\n", _cita(r_con),
                    "\n<details><summary>Fragmentos recuperados</summary>\n\n"
                    + "\n".join(f"- {f.puntaje:.3f} · {f.cita}" for f in fuentes) + "\n\n</details>\n"]
    _guardar(1, "sin RAG vs. con RAG", md + ["\n## Respuestas completas\n"] + detalle)


# EXPERIMENTO 2 · Estrategias de segmentación (solo recuperación)
# Cada pregunta trae la frase exacta de la política que contiene la respuesta.
# Un acierto significa que esa frase aparece COMPLETA en alguno de los fragmentos recuperados.
PREGUNTAS_E2 = [
    ("¿Cuántos días tengo para devolver un producto?", "30 días calendario siguientes a la fecha de entrega"),
    ("¿Puedo devolver un desodorante que no me gustó?", "Productos de higiene personal, como cepillos de dientes"),
    ("¿Qué hago si el producto me llegó roto?", "llegó defectuoso, dañado o no corresponde a lo que se compró"),
    ("¿En cuánto tiempo me devuelven la plata?", "en un plazo de 5 a 7 días hábiles"),
    ("¿Cuánto se demora un envío a un municipio pequeño?", "En municipios y zonas rurales es de 5 a 10 días hábiles"),
    ("¿Desde qué valor el envío es gratis?", "El envío es gratis en compras desde 150.000 pesos"),
    ("¿Puedo cambiar la dirección de entrega?", "solo se puede cambiar mientras el pedido está en preparación"),
    ("¿Cuánto dura la garantía de una lámpara solar?", "tienen garantía de 12 meses contra fallas de fabricación"),
    ("Se me cayó el panel y se dañó, ¿lo cubre la garantía?", "daños por mal uso, golpes, humedad o caídas"),
    ("¿Puedo pagar en efectivo cuando me llegue el pedido?", "No aceptamos pagos contra entrega ni en efectivo"),
    ("¿Me pueden hacer la factura a nombre de mi empresa?", "necesita la factura a nombre de una empresa"),
    ("¿Cómo pido que borren mis datos personales?", "pedir la eliminación de sus datos"),
    ("¿Hacen envíos a otros países?", "no hacemos envíos internacionales"),
    ("¿Las tarjetas regalo se pueden devolver?", "Tarjetas regalo: no son reembolsables una vez emitidas"),
]


def _evaluar_estrategia(fragmentos: list[str], embeddings, nombre: str) -> dict:
    cliente = QdrantClient(":memory:")  # colección temporal en memoria, una por estrategia
    vectores = embeddings.embed_documents(fragmentos)
    cliente.create_collection(nombre, vectors_config=models.VectorParams(size=len(vectores[0]),
                                                                          distance=models.Distance.COSINE))
    cliente.upsert(nombre, points=[models.PointStruct(id=i, vector=v, payload={"page_content": t, "metadata": {}})
                                   for i, (t, v) in enumerate(zip(fragmentos, vectores))])
    almacen = QdrantVectorStore(client=cliente, collection_name=nombre, embedding=embeddings)

    aciertos1 = aciertos3 = 0
    rr = []
    fallos = []
    for pregunta, frase in PREGUNTAS_E2:
        docs = [d.page_content for d in almacen.similarity_search(pregunta, k=3)]
        posicion = next((i for i, d in enumerate(docs, 1) if _normalizar(frase) in _normalizar(d)), None)
        aciertos1 += posicion == 1
        aciertos3 += posicion is not None
        rr.append(1 / posicion if posicion else 0)
        if posicion is None:
            fallos.append(pregunta)
    n = len(PREGUNTAS_E2)
    longitudes = [len(f) for f in fragmentos]
    return {"fragmentos": len(fragmentos), "long_prom": sum(longitudes) / len(longitudes),
            "hit1": aciertos1 / n, "hit3": aciertos3 / n, "mrr": sum(rr) / n, "fallos": fallos}


def experimento_2() -> None:
    print("\n=== Experimento 2: estrategias de segmentación ===")
    embeddings = obtener_embeddings()
    texto, secciones = texto_pdf(), cargar_politicas()
    estrategias = {
        "Tamaño fijo (500, sin solapamiento)": estrategia_tamano_fijo(texto, 500),
        "Por párrafos": estrategia_parrafos(texto),
        "Recursiva (500/75) sin estructura": estrategia_recursiva(texto, 500, 75),
        "Estructural + recursiva (500/75) · ELEGIDA": estrategia_estructural_recursiva(secciones, 500, 75),
    }
    tamanos = {f"Estructural + recursiva ({t}/{int(t * .15)})": estrategia_estructural_recursiva(secciones, t, int(t * .15))
               for t in (150, 300, 1000)}

    md = ["Se indexa solo el PDF de políticas con cada estrategia y se hacen las mismas "
          f"{len(PREGUNTAS_E2)} preguntas. Un **acierto** significa que la frase exacta que contiene la "
          "respuesta aparece completa en un fragmento recuperado. Si la estrategia la partió en dos, "
          "el modelo de lenguaje no puede responder bien aunque la búsqueda \"casi\" acierte.\n",
          "- **Acierto@1**: la frase está en el primer resultado.",
          "- **Acierto@3**: la frase está en alguno de los 3 primeros.",
          "- **MRR**: promedio de 1/posición del primer acierto (1 = siempre primero).\n"]

    def tabla(titulo: str, grupo: dict) -> list[str]:
        filas = [f"## {titulo}\n", "| Estrategia | Fragmentos | Long. promedio | Acierto@1 | Acierto@3 | MRR |",
                 "|---|---|---|---|---|---|"]
        fallos = []
        for nombre, fragmentos in grupo.items():
            inicio = time.perf_counter()
            m = _evaluar_estrategia(fragmentos, embeddings, re.sub(r"\W+", "_", nombre))
            print(f"   {nombre:<48} acierto@1={m['hit1']:.0%} acierto@3={m['hit3']:.0%} "
                  f"MRR={m['mrr']:.2f} ({time.perf_counter() - inicio:.1f} s)")
            filas.append(f"| {nombre} | {m['fragmentos']} | {m['long_prom']:.0f} | {m['hit1']:.0%} | "
                         f"{m['hit3']:.0%} | {m['mrr']:.2f} |")
            if m["fallos"]:
                fallos.append(f"- **{nombre}:** " + "; ".join(m["fallos"]))
        return filas + (["\nPreguntas sin acierto en el top 3:\n"] + fallos if fallos else []) + [""]

    md += tabla("Comparación de estrategias", estrategias)
    md += tabla("Efecto del tamaño de chunk (estrategia elegida)", tamanos | {
        "Estructural + recursiva (500/75) · ELEGIDA": estrategias["Estructural + recursiva (500/75) · ELEGIDA"]})
    ejemplo = estrategias["Tamaño fijo (500, sin solapamiento)"]
    md += ["## Ejemplo de por qué falla el tamaño fijo\n",
           "Final de un fragmento y comienzo del siguiente con la estrategia de tamaño fijo:\n",
           "```text\n…" + ejemplo[2][-160:] + "\n--- corte ---\n" + ejemplo[3][:160] + "…\n```"]
    _guardar(2, "estrategias de segmentación", md)


# EXPERIMENTO 3 · Prompt estricto (con umbral) vs. permisivo (sin umbral)
PREGUNTAS_E3 = [
    "¿Tienen descuento para estudiantes?",
    "¿Hacen entregas el mismo día en Bogotá?",
    "¿Venden paneles solares de 100 W para el techo?",
    "¿Cuál es la capital de Australia?",
    "¿Los productos de higiene personal se pueden devolver?",  # control: SÍ está en la base
]


def experimento_3() -> None:
    print("\n=== Experimento 3: prompt estricto vs. permisivo ===")
    almacen = cargar_almacen()
    estricto = cadena_texto(prompts.RAG_RESPUESTA, temperatura=0.2)
    permisivo = cadena_texto(prompts.RAG_PERMISIVO, temperatura=0.2)
    md = ["Preguntas cuya respuesta **no está** en la base de conocimiento (la última es un control que sí está).\n",
          f"- **Estricto**: prompt principal con reglas de anclaje + umbral de similitud ({config.UMBRAL_RELEVANCIA}); "
          "si ningún fragmento lo supera, se responde \"no tengo esa información\" sin llamar al modelo.",
          "- **Permisivo**: prompt sin reglas (\"usa este contexto como ayuda\") y sin umbral: el modelo "
          "recibe los 4 fragmentos más parecidos, aunque no tengan que ver.\n"]
    for pregunta in PREGUNTAS_E3:
        print(f"\n❓ {pregunta}")
        top = buscar(almacen, pregunta)
        relevantes = recuperar(almacen, pregunta)
        r_est = (ejecutar(estricto, {"contexto": formatear_contexto(relevantes), "pregunta": pregunta})
                 if relevantes else prompts.SIN_INFORMACION)
        r_per = ejecutar(permisivo, {"contexto": formatear_contexto(top), "pregunta": pregunta})
        print(f"   mejor similitud: {top[0].puntaje:.3f} ({top[0].cita})")
        print(f"   Estricto: {r_est}\n   Permisivo: {r_per}")
        md += [f"## {pregunta}\n",
               f"Mejor similitud encontrada: **{top[0].puntaje:.3f}** ({top[0].cita}) · "
               f"fragmentos sobre el umbral: {len(relevantes)}\n",
               "**Estricto:**\n", _cita(r_est), "\n**Permisivo:**\n", _cita(r_per), ""]
    _guardar(3, "prompt estricto vs. permisivo", md)


if __name__ == "__main__":
    elegidos = sys.argv[1:] or ["1", "2", "3"]
    for numero in elegidos:
        {"1": experimento_1, "2": experimento_2, "3": experimento_3}[numero]()
