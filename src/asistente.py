"""Asistente de EcoMarket: el modelo del Taller 1 + el sistema RAG de este taller.

    mensaje del cliente
          │
          ▼
    [Orquestador] ── intención, temas, consulta reformulada, ¿requiere humano?
          │
          ├─ requiere humano / queja ─────> [Escalamiento] ─> ticket con resumen
          ├─ estado_pedido ──> herramienta consultar_pedido  + RAG (política de envíos) ─> [Pedido]
          ├─ devolucion ─────> herramienta (hechos del caso) + RAG (política) ─> [Evaluador] ─> [Redactor]
          ├─ consulta_informacion / fuera_de_alcance
          │        └─> RAG: buscar en Qdrant ─┬─ hay fragmentos relevantes ─> [Respuesta con RAG]
          │                                   └─ no hay ─────────────────────> "no tengo esa información"
          └─ saludo ─────> [General]
"""

import json
from dataclasses import dataclass, field
from datetime import datetime

from src import config, herramientas, prompts
from src.indexacion import cargar_almacen
from src.llm import cadena_json, cadena_texto, ejecutar
from src.recuperacion import Resultado, buscar, formatear_contexto, recuperar

INTENCIONES = {"estado_pedido", "devolucion", "consulta_informacion", "queja", "saludo", "fuera_de_alcance"}


@dataclass
class Respuesta:
    texto: str
    intencion: str
    clasificacion: dict
    fuentes: list[Resultado] = field(default_factory=list)
    ticket: dict | None = None
    decision: dict | None = None


class AsistenteEcoMarket:
    def __init__(self, almacen=None):
        self.almacen = almacen or cargar_almacen()
        self.historial: list[tuple[str, str]] = []
        self.ultimo_numero: str | None = None
        self.veces_pidio_numero: int = 0 # evita repetir la misma pregunta en bucle
        # Las cadenas se construyen una vez: prompt | modelo | parser
        self._orquestador = cadena_json(prompts.ORQUESTADOR)
        self._rag = cadena_texto(prompts.RAG_RESPUESTA, temperatura=0.2)
        self._pedido = cadena_texto(prompts.PEDIDO, temperatura=0.2)
        self._evaluador = cadena_json(prompts.EVALUADOR_DEVOLUCION)
        self._redactor = cadena_texto(prompts.REDACTOR_DEVOLUCION, temperatura=0.4)
        self._escalamiento = cadena_json(prompts.ESCALAMIENTO, temperatura=0.1)
        self._general = cadena_texto(prompts.GENERAL, temperatura=0.5)

    # ------------------------------------------------------------------ utilidades
    def _historial_texto(self, ultimos: int = 6) -> str:
        return "\n".join(f"{rol}: {texto}" for rol, texto in self.historial[-ultimos:]) or "(sin mensajes previos)"

    def clasificar(self, mensaje: str) -> dict:
        c = ejecutar(self._orquestador, {"historial": self._historial_texto(), "mensaje": mensaje})
        if c.get("intencion") not in INTENCIONES:
            c["intencion"] = "consulta_informacion"  # ante la duda, buscar en la base de conocimiento
        if not isinstance(c.get("temas"), list):
            c["temas"] = []
        c["consulta_busqueda"] = c.get("consulta_busqueda") or mensaje
        # Regla determinista para el número de seguimiento (más fiable que el modelo).
        c["numero_seguimiento"] = (herramientas.extraer_numero_seguimiento(mensaje)
                                   or herramientas.extraer_numero_seguimiento(str(c.get("numero_seguimiento")))
                                   or self.ultimo_numero)
        return c

    # ------------------------------------------------------------------ rutas
    def _responder_con_rag(self, mensaje: str, c: dict) -> tuple[str, list[Resultado]]:
        fuentes = recuperar(self.almacen, c["consulta_busqueda"], temas=c["temas"])
        if not fuentes:
            return prompts.SIN_INFORMACION, []
        texto = ejecutar(self._rag, {"contexto": formatear_contexto(fuentes), "pregunta": mensaje})
        return texto, fuentes

    def _responder_pedido(self, mensaje: str, numero: str | None) -> tuple[str, list[Resultado]]:
        if not numero:
            return "¡Con gusto te ayudo! ¿Me compartes tu número de seguimiento? Tiene el formato ECO-XXXXX.", []
        pedido = herramientas.consultar_pedido(numero)
        fuentes = []
        if pedido and pedido["estado"] == "Retrasado":
            fuentes = recuperar(self.almacen, "retrasos en la entrega de un pedido", temas=["envios"], k=2)
        texto = ejecutar(self._pedido, {"pedido": herramientas.formatear_pedido(pedido),
                                        "contexto": formatear_contexto(fuentes), "pregunta": mensaje})
        return texto, fuentes

    def responder_devolucion(self, mensaje: str, numero: str | None,
                             producto_mencionado: str | None = None) -> tuple[str, list[Resultado], dict]:
        if not numero:
            return self._devolucion_sin_numero(mensaje, producto_mencionado)
        pedido = herramientas.consultar_pedido(numero)
        producto = herramientas.identificar_producto(pedido, f"{producto_mencionado or ''} {mensaje}") if pedido else None
        hechos = herramientas.hechos_devolucion(pedido, producto)

        # RAG: la política ya no se pega completa; se recuperan las secciones pertinentes.
        # Aquí se filtra por tema y no se aplica umbral: el evaluador necesita ver también las
        # excepciones (producto dañado, garantía) aunque la pregunta no se parezca a ellas.
        consulta = f"devolución de {producto['nombre'] if producto else 'un producto'}: {mensaje}"
        fuentes = buscar(self.almacen, consulta, k=7, temas=["devoluciones", "garantias"])
        contexto = formatear_contexto(fuentes)

        decision = ejecutar(self._evaluador, {"contexto": contexto, "hechos": hechos, "pregunta": mensaje}) or {
            "tipo": "producto_no_identificado", "elegible": False}
        texto = ejecutar(self._redactor, {"contexto": contexto, "hechos": hechos, "pregunta": mensaje,
                                          "decision": json.dumps(decision, ensure_ascii=False)})
        return texto, fuentes, decision

    def _devolucion_sin_numero(self, mensaje: str,
                               producto_mencionado: str | None) -> tuple[str, list[Resultado], dict]:
        """Devolución sin número de seguimiento: primero se responde con la política (RAG).

        Sin número no se puede evaluar el caso concreto (fecha de entrega, producto exacto),
        pero sí se puede explicar qué dice la política para ese tipo de producto. Así el
        cliente recibe una respuesta útil en lugar de una pregunta repetida.
        """
        consulta = (f"¿Se puede devolver {producto_mencionado}? Política de devoluciones"
                    if producto_mencionado else f"Política de devoluciones: {mensaje}")
        fuentes = recuperar(self.almacen, consulta, temas=["devoluciones"], k=5)
        if fuentes:
            texto = ejecutar(self._rag, {"contexto": formatear_contexto(fuentes), "pregunta": mensaje})
        else:
            texto = "Con gusto te explico nuestra política de devoluciones."

        self.veces_pidio_numero += 1
        if self.veces_pidio_numero == 1:
            texto += ("\n\nSi quieres iniciar la devolución, compárteme el número de seguimiento del pedido "
                      "(formato ECO-XXXXX).")
        else:
            # El cliente ya dijo que no lo tiene: se le dice dónde encontrarlo y se ofrece una salida.
            texto += ("\n\nEl número de seguimiento te llegó por correo y por WhatsApp cuando el pedido salió "
                      "de bodega (empieza por ECO). Si no lo encuentras, puedo comunicarte con una persona "
                      "de nuestro equipo para que lo busque con tus datos.")
        return texto, fuentes, {}

    def _escalar(self, mensaje: str, numero: str | None) -> dict:
        conversacion = f"{self._historial_texto(10)}\nCliente: {mensaje}"
        ticket = ejecutar(self._escalamiento, {
            "conversacion": conversacion,
            "pedido": herramientas.formatear_pedido(herramientas.consultar_pedido(numero)) if numero else "(ninguno)",
        })
        ticket.setdefault("mensaje_cliente", "Entiendo tu situación. Te comunico con una persona de nuestro "
                                             "equipo, que ya tendrá el resumen de tu caso.")
        ticket.update({"fecha": datetime.now().isoformat(timespec="seconds"), "conversacion": conversacion})
        config.CARPETA_RESULTADOS.mkdir(exist_ok=True)
        with open(config.CARPETA_RESULTADOS / "tickets_escalados.jsonl", "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(ticket, ensure_ascii=False) + "\n")
        return ticket

    # ------------------------------------------------------------------ punto de entrada
    def responder(self, mensaje: str) -> Respuesta:
        c = self.clasificar(mensaje)
        numero, intencion = c["numero_seguimiento"], c["intencion"]
        if numero:
            self.ultimo_numero = numero
        respuesta = Respuesta(texto="", intencion=intencion, clasificacion=c)

        if c.get("requiere_humano") or intencion == "queja":
            respuesta.ticket = self._escalar(mensaje, numero)
            respuesta.texto = respuesta.ticket["mensaje_cliente"]
        elif intencion == "estado_pedido":
            respuesta.texto, respuesta.fuentes = self._responder_pedido(mensaje, numero)
        elif intencion == "devolucion":
            respuesta.texto, respuesta.fuentes, respuesta.decision = self.responder_devolucion(
                mensaje, numero, c.get("producto_mencionado"))
        elif intencion == "saludo":
            respuesta.texto = ejecutar(self._general, {"pregunta": mensaje})
        else:  # consulta_informacion o fuera_de_alcance: siempre se intenta la base de conocimiento
            respuesta.texto, respuesta.fuentes = self._responder_con_rag(mensaje, c)

        self.historial += [("Cliente", mensaje), (prompts.NOMBRE_AGENTE, respuesta.texto)]
        return respuesta
