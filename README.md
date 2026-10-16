# EcoMarket · Asistente de atención al cliente con RAG

Taller Práctico #2: extender el asistente del Taller 1 con un sistema **RAG** (Generación Aumentada por Recuperación) para que pueda responder **cualquier consulta** de los clientes de EcoMarket con información de la empresa, o reconocer cuándo no tiene la información.

## Entregables

| Fase | Contenido | Documento |
|---|---|---|
| 1 | Selección del modelo de embeddings y la base vectorial | [`docs/fase1_componentes.md`](docs/fase1_componentes.md) |
| 2 | Documentos, estrategia de segmentación e indexación | [`docs/fase2_base_conocimiento.md`](docs/fase2_base_conocimiento.md) |
| 3 | Explicación del código, integración y experimentos | [`docs/fase3_integracion_codigo.md`](docs/fase3_integracion_codigo.md) |
| 3 | Limitaciones y suposiciones | [`docs/limitaciones_y_suposiciones.md`](docs/limitaciones_y_suposiciones.md) |

## La solución en breve

| Componente | Elección |
|---|---|
| Modelo de embeddings | **BGE-M3** (código abierto, multilingüe, servido con Ollama) |
| Base de datos vectorial | **Qdrant** (modo local; el mismo código funciona con servidor o Qdrant Cloud) |
| Framework | **LangChain** |
| Modelo de generación | `qwen3:4b` en Ollama (el del Taller 1) |
| Documentos | Políticas en **PDF**, catálogo e inventario en **CSV**, preguntas frecuentes en **JSON** |
| Segmentación | Estructural (por subsección) + recursiva, 500 caracteres con 15% de solapamiento |

Los pedidos **no** se indexan: se consultan con una herramienta de búsqueda exacta, porque cambian constantemente y son datos privados de cada cliente.

## Estructura

```
├── data/
│   ├── documentos/          # Base de conocimiento: PDF, CSV y JSON
│   ├── fuentes/             # Texto fuente del PDF de políticas
│   └── pedidos.json         # Datos transaccionales (se consultan con una herramienta)
├── docs/                    # Respuestas de las fases 1, 2 y 3
├── src/
│   ├── config.py            # Parámetros configurables
│   ├── extraccion.py        # Paso 1: PDF / CSV / JSON → Documents
│   ├── segmentacion.py      # Pasos 2-3: chunking y metadatos
│   ├── indexacion.py        # Pasos 4-5: embeddings bge-m3 y carga en Qdrant
│   ├── recuperacion.py      # Búsqueda, filtros y umbral de relevancia
│   ├── herramientas.py      # Consulta de pedidos
│   ├── llm.py               # Modelo de generación y cadenas LCEL
│   ├── prompts.py           # Plantillas de prompts
│   └── asistente.py         # Orquestador: une todas las piezas
├── herramientas/generar_documentos.py   # Regenera el PDF a partir de su fuente
├── indexar.py               # Construye la base de conocimiento
├── buscar.py                # Prueba solo la recuperación
├── chat_ecomarket.py        # Chat completo
├── experimentos.py          # Experimentos de modificación (sin/con RAG, chunking, prompts)
└── resultados/              # Reportes generados al ejecutar
```

## Instalación

1. Instala [Ollama](https://ollama.com/download) y descarga los dos modelos:

   ```bash
   ollama pull qwen3.5:2b    # generación
   ollama pull bge-m3      # embeddings
   ```

2. Crea un entorno virtual e instala las dependencias (Python 3.10 o superior):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Ejecución

Con Ollama abierto, desde la raíz del repositorio:

```bash
# 1. Construir la base de conocimiento (extracción → chunking → embeddings → Qdrant)
python indexar.py --mostrar 3

# 2. Probar solo la búsqueda (ver qué fragmentos encuentra y con qué similitud)
python buscar.py "¿puedo devolver un champú?"
python buscar.py "garantía" --tema garantias

# 3. Chat
python chat_ecomarket.py --debug      # muestra clasificación y fuentes de cada respuesta
python chat_ecomarket.py --demo       # conversación de prueba → resultados/chat_demo.md

# 4. Experimentos → resultados/experimento_1.md, _2.md, _3.md
python experimentos.py
```

> **Calibrar el umbral:** antes de los experimentos, prueba con `buscar.py` algunas preguntas que sí están en la base y otras que no. Si las que sí están quedan por debajo de 0,45 (o las que no están quedan por encima), ajusta el umbral con `RAG_UMBRAL`.

## Configuración

| Variable | Por defecto | Uso |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3.5:2b` | Modelo de generación (`qwen3.5:2b` da mejor calidad si el equipo lo permite) |
| `OLLAMA_EMBEDDINGS` | `bge-m3` | Modelo de embeddings (si se cambia, hay que reindexar) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `500` / `75` | Tamaño y solapamiento de los fragmentos (hay que reindexar) |
| `RAG_K` | `4` | Fragmentos recuperados por consulta |
| `RAG_UMBRAL` | `0.45` | Similitud mínima para considerar relevante un fragmento |
| `QDRANT_URL` / `QDRANT_API_KEY` | — | Usar un servidor Qdrant o Qdrant Cloud en lugar del modo local |
| `OLLAMA_THINK` | `false` | `true` activa el modo de razonamiento de Qwen3 (más lento) |
| `FECHA_REFERENCIA` | `2026-10-10` | Fecha "de hoy" para calcular plazos de devolución |

Ejemplo: `CHUNK_SIZE=300 CHUNK_OVERLAP=45 python indexar.py` (en Windows PowerShell: `$env:CHUNK_SIZE="300"`).

Para usar Qdrant en Docker en lugar del modo local:

```bash
docker run -p 6333:6333 qdrant/qdrant
QDRANT_URL=http://localhost:6333 python indexar.py
```

> Los datos, clientes y enlaces (`ecomarket.example`) son ficticios.
