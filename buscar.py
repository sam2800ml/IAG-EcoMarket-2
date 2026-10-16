"""Prueba solo la RECUPERACIÓN (sin generar respuesta): qué fragmentos encuentra Qdrant y con qué puntaje.

Sirve para entender la búsqueda semántica y calibrar el umbral de relevancia.

Uso:
    python buscar.py "¿puedo devolver un champú?"
    python buscar.py "¿cuánto cuesta el envío?" --k 3
    python buscar.py "garantía" --tema garantias        # filtro por metadatos
    python buscar.py "algo para cargar el celular" --tipo producto
"""

import argparse

from src import config
from src.indexacion import cargar_almacen
from src.recuperacion import buscar


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("consulta")
    parser.add_argument("--k", type=int, default=config.K_RESULTADOS)
    parser.add_argument("--tema", action="append", help="filtrar por metadato 'tema' (se puede repetir)")
    parser.add_argument("--tipo", action="append", choices=["politica", "producto", "faq"])
    args = parser.parse_args()

    resultados = buscar(cargar_almacen(), args.consulta, k=args.k, temas=args.tema, tipos=args.tipo)
    print(f'\nConsulta: "{args.consulta}"   (umbral de relevancia: {config.UMBRAL_RELEVANCIA})')
    for i, r in enumerate(resultados, start=1):
        marca = "✅" if r.puntaje >= config.UMBRAL_RELEVANCIA else "⛔ bajo el umbral"
        print(f"\n[{i}] similitud {r.puntaje:.3f} {marca}\n    {r.cita}")
        print("    " + r.documento.page_content.replace("\n", "\n    "))
    if not resultados:
        print("Sin resultados (revisa los filtros).")


if __name__ == "__main__":
    main()
