"""Construye la base de conocimiento de EcoMarket (se ejecuta una vez, o cuando cambian los documentos).

    1. Extracción     PDF, CSV y JSON  -> Documents con metadatos
    2. Segmentación   estructural + recursiva -> fragmentos (chunks)
    3. Metadatos      identificador, longitud, fecha de indexación
    4. Embeddings     bge-m3 vía Ollama, por lotes -> vectores de 1024 dimensiones
    5. Carga          colección en Qdrant: vector + texto + metadatos

Uso:
    python indexar.py              # indexa todo
    python indexar.py --mostrar 5  # además imprime 5 fragmentos de ejemplo
"""

import sys
from collections import Counter
from statistics import mean

from src import config
from src.extraccion import cargar_todo
from src.indexacion import crear_indice
from src.segmentacion import segmentar_todo


def main() -> None:
    print("1/5 Extrayendo documentos...")
    documentos = cargar_todo()
    for nombre, docs in documentos.items():
        print(f"    {nombre:<10} {len(docs):>3} unidades  ({docs[0].metadata['fuente']})")

    print(f"2/5 Segmentando (chunk={config.TAMANO_CHUNK} caracteres, solapamiento={config.SOLAPAMIENTO})...")
    print("3/5 Enriqueciendo metadatos...")
    fragmentos = segmentar_todo(documentos)
    por_tipo = Counter(f.metadata["tipo_documento"] for f in fragmentos)
    longitudes = [f.metadata["num_caracteres"] for f in fragmentos]
    print(f"    {len(fragmentos)} fragmentos: {dict(por_tipo)}")
    print(f"    longitud promedio {mean(longitudes):.0f} caracteres (mín. {min(longitudes)}, máx. {max(longitudes)})")

    print(f"4/5 Generando embeddings con '{config.MODELO_EMBEDDINGS}' en lotes de {config.TAMANO_LOTE_EMBEDDINGS}...")
    print("5/5 Cargando en Qdrant...")
    almacen, segundos = crear_indice(fragmentos)
    destino = config.QDRANT_URL or config.CARPETA_QDRANT.relative_to(config.RAIZ)
    total = almacen.client.count(config.COLECCION).count
    print(f"\n✅ {total} vectores en la colección '{config.COLECCION}' ({destino}) en {segundos:.1f} s.")

    if "--mostrar" in sys.argv:
        posicion = sys.argv.index("--mostrar")
        n = int(sys.argv[posicion + 1]) if len(sys.argv) > posicion + 1 else 3
        paso = max(1, len(fragmentos) // n)
        for fragmento in fragmentos[::paso][:n]:
            print("\n" + "-" * 72)
            print({k: v for k, v in fragmento.metadata.items() if k not in ("fecha_indexacion",)})
            print(fragmento.page_content)


if __name__ == "__main__":
    main()
