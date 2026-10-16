"""Herramientas para datos TRANSACCIONALES (heredadas del Taller 1).

El estado de un pedido cambia constantemente y es información privada de un cliente:
no tiene sentido vectorizarlo ni dejar que el modelo lo "busque por similitud"
(el pedido ECO-10005 y el ECO-10006 se parecen muchísimo como texto y son de
personas distintas). Por eso se consulta con una búsqueda exacta por número, que en
producción sería una consulta parametrizada a la base de datos de pedidos.
"""

import json
import re
import unicodedata
from datetime import date

from src.config import ARCHIVO_PEDIDOS, FECHA_HOY
from src.extraccion import productos_por_id

PEDIDOS: list[dict] = json.loads(ARCHIVO_PEDIDOS.read_text(encoding="utf-8"))
PRODUCTOS: dict[str, dict] = productos_por_id()

RE_SEGUIMIENTO = re.compile(r"\bECO[-\s]?(\d{5})\b", re.IGNORECASE)


def extraer_numero_seguimiento(texto: str) -> str | None:
    coincidencia = RE_SEGUIMIENTO.search(texto or "")
    return f"ECO-{coincidencia.group(1)}" if coincidencia else None


def consultar_pedido(numero: str) -> dict | None:
    """Herramienta: búsqueda EXACTA por número de seguimiento."""
    numero = (numero or "").strip().upper()
    return next((p for p in PEDIDOS if p["numero_seguimiento"] == numero), None)


def productos_del_pedido(pedido: dict) -> list[dict]:
    return [{**PRODUCTOS[item["id_producto"]], "cantidad": item["cantidad"]}
            for item in pedido["productos"] if item["id_producto"] in PRODUCTOS]


def formatear_pedido(pedido: dict | None) -> str:
    if pedido is None:
        return "(no existe ningún pedido con ese número de seguimiento)"
    productos = "; ".join(f"{p['nombre']} (x{p['cantidad']})" for p in productos_del_pedido(pedido))
    campos = [
        ("Número de seguimiento", pedido["numero_seguimiento"]), ("Cliente", pedido["cliente"]),
        ("Ciudad de destino", pedido["ciudad"]), ("Fecha de compra", pedido["fecha_compra"]),
        ("Productos", productos), ("Estado", pedido["estado"]),
        ("Transportadora", pedido["transportadora"]),
        ("Fecha estimada de entrega", pedido["fecha_estimada_entrega"]),
        ("Fecha de entrega", pedido["fecha_entrega"]), ("Enlace de rastreo", pedido["enlace_rastreo"]),
        ("Nota", pedido["nota"]),
    ]
    return "\n".join(f"{nombre}: {valor if valor else '—'}" for nombre, valor in campos)


def _palabras(texto: str) -> set[str]:
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return {p for p in re.findall(r"[a-z0-9]+", texto) if len(p) > 3}


def identificar_producto(pedido: dict, texto: str) -> dict | None:
    """Encuentra, dentro del pedido, el producto que menciona el cliente."""
    consulta = _palabras(texto)
    puntuados = [(len(consulta & _palabras(p["nombre"])), p) for p in productos_del_pedido(pedido)]
    puntuados = [par for par in puntuados if par[0] > 0]
    return max(puntuados, key=lambda par: par[0])[1] if puntuados else None


def hechos_devolucion(pedido: dict | None, producto: dict | None) -> str:
    """Hechos del caso calculados en código: el LLM no debe hacer aritmética de fechas."""
    if pedido is None:
        return "No se encontró ningún pedido con el número de seguimiento indicado."
    dias = (FECHA_HOY - date.fromisoformat(pedido["fecha_entrega"])).days if pedido["fecha_entrega"] else None
    lineas = [
        f"Fecha de hoy: {FECHA_HOY.isoformat()}",
        f"Número de seguimiento: {pedido['numero_seguimiento']}",
        f"Cliente: {pedido['cliente']}",
        f"Estado del pedido: {pedido['estado']}",
        f"Días transcurridos desde la entrega: {dias if dias is not None else 'no aplica (no entregado)'}",
    ]
    if producto:
        lineas += [f"Producto: {producto['nombre']}", f"Categoría del producto: {producto['categoria']}"]
    else:
        nombres = ", ".join(p["nombre"] for p in productos_del_pedido(pedido))
        lineas.append(f"Producto: no identificado (el pedido contiene: {nombres})")
    return "\n".join(lineas)
