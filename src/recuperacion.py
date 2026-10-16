"""RECUPERACIÓN: la "R" de RAG.

Dada una pregunta, la convierte en vector con el mismo modelo de embeddings y busca
en Qdrant los fragmentos más parecidos (similitud coseno). Además:

- Filtra por metadatos (por ejemplo, solo políticas de envíos) cuando el orquestador
  identificó el tema. Si el filtro no encuentra nada relevante, repite sin filtro,
  para que un error de clasificación no deje al cliente sin respuesta.
- Descarta los fragmentos por debajo de un umbral de similitud. Si no queda ninguno,
  el asistente sabe que NO tiene la información y lo dice, en lugar de inventar.
"""

from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http import models

from src import config

TEMAS_VALIDOS = {"devoluciones", "envios", "garantias", "pagos", "privacidad", "productos",
                 "cuenta", "pedidos", "tienda", "promociones", "sostenibilidad", "contacto"}


@dataclass
class Resultado:
    documento: Document
    puntaje: float

    @property
    def cita(self) -> str:
        m = self.documento.metadata
        if m["tipo_documento"] == "politica":
            return f"{m['fuente']} · {m['politica']}, sección {m['seccion']}"
        if m["tipo_documento"] == "producto":
            return f"{m['fuente']} · {m['id_producto']} {m['nombre']}"
        return f"{m['fuente']} · {m['id_faq']}"


def construir_filtro(temas: list[str] | None = None, tipos: list[str] | None = None) -> models.Filter | None:
    condiciones = []
    if temas:
        condiciones.append(models.FieldCondition(key="metadata.tema", match=models.MatchAny(any=temas)))
    if tipos:
        condiciones.append(models.FieldCondition(key="metadata.tipo_documento", match=models.MatchAny(any=tipos)))
    return models.Filter(must=condiciones) if condiciones else None


def buscar(almacen: QdrantVectorStore, consulta: str, k: int = config.K_RESULTADOS,
           temas: list[str] | None = None, tipos: list[str] | None = None) -> list[Resultado]:
    """Búsqueda por similitud. El puntaje es la similitud coseno (más alto = más parecido)."""
    pares = almacen.similarity_search_with_score(consulta, k=k, filter=construir_filtro(temas, tipos))
    return [Resultado(doc, float(puntaje)) for doc, puntaje in pares]


def recuperar(almacen: QdrantVectorStore, consulta: str, temas: list[str] | None = None,
              k: int = config.K_RESULTADOS, umbral: float = config.UMBRAL_RELEVANCIA) -> list[Resultado]:
    """Recuperación con filtro por tema, respaldo sin filtro y umbral de relevancia."""
    temas = [t for t in (temas or []) if t in TEMAS_VALIDOS]
    resultados = buscar(almacen, consulta, k, temas=temas) if temas else []
    if not resultados or resultados[0].puntaje < umbral:
        resultados = buscar(almacen, consulta, k)
    return [r for r in resultados if r.puntaje >= umbral]


def formatear_contexto(resultados: list[Resultado]) -> str:
    """Arma el bloque de contexto que se inserta en el prompt, numerado para poder citarlo."""
    if not resultados:
        return "(no se encontró información relevante en la base de conocimiento)"
    return "\n\n".join(
        f"[{i}] Fuente: {r.cita}\n{r.documento.page_content}" for i, r in enumerate(resultados, start=1)
    )
