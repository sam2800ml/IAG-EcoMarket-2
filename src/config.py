"""Configuración central del sistema RAG de EcoMarket.

Todos los valores se pueden cambiar con variables de entorno sin tocar el código,
lo que facilita los experimentos (por ejemplo, probar otro tamaño de chunk).
"""

import os
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DOCUMENTOS = RAIZ / "data" / "documentos"
ARCHIVO_PEDIDOS = RAIZ / "data" / "pedidos.json"
CARPETA_RESULTADOS = RAIZ / "resultados"

# --- Modelos (servidos localmente por Ollama) ---------------------------------
MODELO_LLM = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
MODELO_EMBEDDINGS = os.getenv("OLLAMA_EMBEDDINGS", "bge-m3")
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
RAZONAMIENTO = os.getenv("OLLAMA_THINK", "false").lower() == "true"

# --- Base de datos vectorial (Qdrant en modo local, sin servidor) ------------
CARPETA_QDRANT = Path(os.getenv("QDRANT_PATH", RAIZ / "qdrant_data"))
QDRANT_URL = os.getenv("QDRANT_URL")  # Si se define, usa un servidor Qdrant (Docker o Cloud).
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLECCION = os.getenv("QDRANT_COLLECTION", "ecomarket_conocimiento")

# --- Segmentación -----------------------------------------------------------
TAMANO_CHUNK = int(os.getenv("CHUNK_SIZE", "500"))       # caracteres
SOLAPAMIENTO = int(os.getenv("CHUNK_OVERLAP", "75"))     # 15 % del chunk
TAMANO_LOTE_EMBEDDINGS = int(os.getenv("EMBED_BATCH", "32"))

# --- Recuperación -----------------------------------------------------------
K_RESULTADOS = int(os.getenv("RAG_K", "4"))
# Similitud coseno mínima para considerar que un fragmento es relevante.
# Si ningún fragmento la supera, el asistente reconoce que no tiene la información.
UMBRAL_RELEVANCIA = float(os.getenv("RAG_UMBRAL", "0.45"))

# Fecha "de hoy" fija para que los cálculos de plazos sean reproducibles.
FECHA_HOY = date.fromisoformat(os.getenv("FECHA_REFERENCIA", "2026-09-24"))
