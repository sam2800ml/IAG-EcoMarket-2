"""Modelo de lenguaje (generación) servido localmente por Ollama, vía LangChain.

Se reutiliza el modelo del Taller 1 (qwen3:4b por defecto). La pieza que cambia en
este taller es lo que recibe en el prompt: ahora el contexto viene de la búsqueda
en la base de conocimiento (RAG) en lugar de estar pegado a mano.
"""

import json
import re
import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

from src import config

_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def crear_llm(temperatura: float = 0.3, json_mode: bool = False) -> ChatOllama:
    parametros = {"model": config.MODELO_LLM, "base_url": config.OLLAMA_URL, "temperature": temperatura}
    if json_mode:
        parametros["format"] = "json"
    # Los modelos con modo de razonamiento (Qwen3) responden más rápido con él apagado.
    if "qwen3" in config.MODELO_LLM or "deepseek-r1" in config.MODELO_LLM:
        parametros["reasoning"] = config.RAZONAMIENTO
    return ChatOllama(**parametros)


def _limpiar(texto: str) -> str:
    return _RE_THINK.sub("", texto or "").strip()


def _a_json(texto: str) -> dict:
    texto = _limpiar(texto)
    for candidato in (texto, (re.search(r"\{.*\}", texto, re.DOTALL) or [None])[0]):
        if candidato:
            try:
                return json.loads(candidato)
            except json.JSONDecodeError:
                pass
    return {}


def cadena_texto(prompt: ChatPromptTemplate, temperatura: float = 0.3):
    """prompt | modelo | parser  -> devuelve texto limpio (sintaxis LCEL de LangChain)."""
    return prompt | crear_llm(temperatura) | StrOutputParser() | RunnableLambda(_limpiar)


def cadena_json(prompt: ChatPromptTemplate, temperatura: float = 0.0):
    """prompt | modelo en modo JSON | parser -> devuelve un diccionario."""
    return prompt | crear_llm(temperatura, json_mode=True) | StrOutputParser() | RunnableLambda(_a_json)


def ejecutar(cadena, variables: dict):
    """Invoca una cadena con mensajes de error claros si Ollama no está disponible."""
    try:
        return cadena.invoke(variables)
    except Exception as error:  # noqa: BLE001
        mensaje = str(error).lower()
        if "not found" in mensaje or "404" in mensaje:
            sys.exit(f"El modelo '{config.MODELO_LLM}' no está descargado. Ejecuta: ollama pull {config.MODELO_LLM}")
        if "connect" in mensaje or "refused" in mensaje:
            sys.exit("No se pudo conectar con Ollama. Verifica que esté abierto o ejecuta: ollama serve")
        raise
