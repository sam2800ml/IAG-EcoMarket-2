"""Pasos 4 y 5 de la indexación: VECTORIZACIÓN (embeddings) y CARGA en Qdrant.

    fragmentos ──> OllamaEmbeddings (bge-m3, por lotes) ──> vectores de 1024 dimensiones
                                                              │
                                                              ▼
                       Qdrant: colección con  [ vector | texto original | metadatos ]

Qdrant corre en "modo local": guarda la colección en la carpeta qdrant_data/ sin
necesidad de un servidor. El mismo código funciona contra un servidor Qdrant (Docker)
o Qdrant Cloud con solo definir QDRANT_URL.
"""

import atexit
import sys
import time
import uuid

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src import config

_cliente: QdrantClient | None = None


def obtener_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=config.MODELO_EMBEDDINGS, base_url=config.OLLAMA_URL)


def obtener_cliente() -> QdrantClient:
    """Un solo cliente por proceso (el modo local bloquea la carpeta mientras está abierta)."""
    global _cliente
    if _cliente is None:
        if config.QDRANT_URL:
            _cliente = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        else:
            config.CARPETA_QDRANT.mkdir(parents=True, exist_ok=True)
            _cliente = QdrantClient(path=str(config.CARPETA_QDRANT))
        atexit.register(_cliente.close)  # libera la carpeta al terminar
    return _cliente


def _dimension_embeddings(embeddings) -> int:
    try:
        return len(embeddings.embed_query("dimensión"))
    except Exception as error:  # noqa: BLE001
        mensaje = str(error).lower()
        if "not found" in mensaje or "404" in mensaje:
            sys.exit(f"El modelo de embeddings '{config.MODELO_EMBEDDINGS}' no está descargado. "
                     f"Ejecuta: ollama pull {config.MODELO_EMBEDDINGS}")
        if "connect" in mensaje or "refused" in mensaje:
            sys.exit("No se pudo conectar con Ollama. Verifica que esté abierto o ejecuta: ollama serve")
        raise


def crear_indice(fragmentos: list[Document], coleccion: str = config.COLECCION,
                 cliente: QdrantClient | None = None, embeddings=None,
                 tamano_lote: int = config.TAMANO_LOTE_EMBEDDINGS) -> tuple[QdrantVectorStore, float]:
    """Crea (o recrea) la colección y carga los fragmentos. Devuelve el vector store y la duración."""
    cliente = cliente or obtener_cliente()
    embeddings = embeddings or obtener_embeddings()
    dimension = _dimension_embeddings(embeddings)

    if cliente.collection_exists(coleccion):
        cliente.delete_collection(coleccion)
    cliente.create_collection(
        collection_name=coleccion,
        # Distancia coseno: compara la dirección de los vectores (el significado), no su longitud.
        vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
    )
    # Índices sobre los metadatos más usados en filtros (aceleran el filtrado en servidor).
    if config.QDRANT_URL:
        for campo in ("tipo_documento", "tema", "categoria"):
            cliente.create_payload_index(coleccion, f"metadata.{campo}", models.PayloadSchemaType.KEYWORD)

    almacen = QdrantVectorStore(client=cliente, collection_name=coleccion, embedding=embeddings)
    # Qdrant exige IDs enteros o UUID: se deriva un UUID estable del chunk_id.
    ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f.metadata["chunk_id"])) for f in fragmentos]

    inicio = time.perf_counter()
    # add_documents envía los textos al modelo de embeddings en lotes de `tamano_lote`.
    almacen.add_documents(fragmentos, ids=ids, batch_size=tamano_lote)
    return almacen, time.perf_counter() - inicio


def cargar_almacen(coleccion: str = config.COLECCION) -> QdrantVectorStore:
    """Abre una colección ya indexada para hacer búsquedas."""
    cliente = obtener_cliente()
    if not cliente.collection_exists(coleccion):
        sys.exit("La base de conocimiento no existe todavía. Ejecuta primero: python indexar.py")
    return QdrantVectorStore(client=cliente, collection_name=coleccion, embedding=obtener_embeddings())
