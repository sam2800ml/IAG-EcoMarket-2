"""Chat de atención al cliente de EcoMarket con RAG.

Uso:
    python chat_ecomarket.py            # conversación interactiva
    python chat_ecomarket.py --debug    # muestra la clasificación y los fragmentos recuperados
    python chat_ecomarket.py --demo     # conversación de ejemplo que se guarda en resultados/
"""

import json
import sys
from datetime import datetime

from src import config
from src.asistente import AsistenteEcoMarket, Respuesta

CONVERSACION_DEMO = [
    "Hola, buenas",
    "¿Cuánto cuesta el envío a Pasto y cuánto se demora?",
    "¿Y desde qué valor es gratis?",
    "¿Tienen algo para cargar el celular con energía solar?",
    "¿Ese tiene garantía?",
    "¿Cómo va mi pedido ECO-10005?",
    "Quiero devolver el café del pedido ECO-10008, lo pedí en grano y lo quería molido",
    "¿Tienen tienda física en Cali?",
    "¿Me recomiendas una película para ver hoy?",
    "Me cobraron dos veces la compra, necesito hablar con alguien ya",
]


def detalle(r: Respuesta) -> str:
    c = r.clasificacion
    lineas = [f"   [orquestador] intención={c['intencion']} temas={c.get('temas')} "
              f"búsqueda=\"{c.get('consulta_busqueda')}\" humano={c.get('requiere_humano')}"]
    for f in r.fuentes:
        lineas.append(f"   [fuente] {f.puntaje:.3f} · {f.cita}")
    if r.decision:
        lineas.append(f"   [decisión devolución] {json.dumps(r.decision, ensure_ascii=False)}")
    if r.ticket:
        ticket = {k: v for k, v in r.ticket.items() if k != "conversacion"}
        lineas.append(f"   [ticket] {json.dumps(ticket, ensure_ascii=False)}")
    return "\n".join(lineas)


def modo_demo() -> None:
    asistente = AsistenteEcoMarket()
    md = [f"# Demo del chat con RAG\n\nModelo: `{config.MODELO_LLM}` · Embeddings: `{config.MODELO_EMBEDDINGS}` · "
          f"Generado: {datetime.now():%Y-%m-%d %H:%M}\n"]
    for mensaje in CONVERSACION_DEMO:
        print(f"\n🧑 Cliente: {mensaje}")
        r = asistente.responder(mensaje)
        print(f"🌱 Eco: {r.texto}\n{detalle(r)}")
        md += [f"**🧑 Cliente:** {mensaje}\n", f"**🌱 Eco:** {r.texto}\n",
               "```text\n" + detalle(r).replace("   ", "") + "\n```\n"]
    config.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    ruta = config.CARPETA_RESULTADOS / "chat_demo.md"
    ruta.write_text("\n".join(md), encoding="utf-8")
    print(f"\n✅ Conversación guardada en {ruta.relative_to(config.RAIZ)}")


def modo_interactivo(debug: bool) -> None:
    asistente = AsistenteEcoMarket()
    print(f"Chat EcoMarket · {config.MODELO_LLM} + RAG ({config.MODELO_EMBEDDINGS} / Qdrant). Escribe 'salir' para terminar.")
    print("🌱 Eco: ¡Hola! Soy Eco, el asistente virtual de EcoMarket. ¿En qué te ayudo?")
    while True:
        try:
            mensaje = input("\n🧑 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if mensaje.lower() in {"salir", "exit", "quit"}:
            break
        if mensaje:
            r = asistente.responder(mensaje)
            print(f"🌱 Eco: {r.texto}")
            if debug:
                print(detalle(r))
    print("\n🌱 Eco: ¡Gracias por comprar sostenible! Hasta pronto.")


if __name__ == "__main__":
    modo_demo() if "--demo" in sys.argv else modo_interactivo("--debug" in sys.argv)
