# Limitaciones y suposiciones

El taller pide detallar las limitaciones de recursos para ejecutar la propuesta y las suposiciones necesarias para entender la arquitectura. Este documento separa lo que el prototipo hace de lo que haría el sistema en producción.

## 1. Limitaciones del prototipo

### Recursos de cómputo

| Limitación | Por qué | Efecto | En producción |
|---|---|---|---|
| Modelo de generación pequeño (`qwen3:4b`) | Debe correr en un computador personal, sin GPU dedicada | Puede equivocarse al clasificar intenciones, no seguir todas las reglas del prompt o generar JSON incompleto | Qwen3.5-35B-A3B (MoE) o similar, servido con vLLM en GPU, como se propuso en el Taller 1 |
| Inferencia en CPU | Mismo motivo | Cada respuesta puede tardar varios segundos; el chat completo hace entre 2 y 3 llamadas al modelo por mensaje | GPU y servidor de inferencia con procesamiento por lotes |
| BGE-M3 solo con vector denso | Ollama expone únicamente el vector denso del modelo | No se usa la búsqueda híbrida (densa + dispersa), que ayudaría con códigos y términos exactos como "IPX4" o "USB-C" | Servir BGE-M3 con `FlagEmbedding` y usar la búsqueda híbrida de Qdrant |
| Qdrant en modo local | Evita instalar Docker o crear una cuenta en la nube | Un solo proceso puede abrir la base a la vez (no se pueden correr dos scripts simultáneamente) y no hay índices sobre los metadatos | Servidor Qdrant en Docker o Qdrant Cloud: basta definir `QDRANT_URL` |

### Datos

- **Los datos son ficticios.** Políticas, productos, pedidos y clientes fueron creados para el taller. Los enlaces usan el dominio de prueba `ecomarket.example`.
- **La base es pequeña** (55 fragmentos). Con pocos documentos, la búsqueda es más fácil que con miles; los resultados de los experimentos podrían ser más optimistas que en un caso real.
- **El inventario está congelado** en la fecha de creación del CSV. En producción, el stock exacto se consultaría con una herramienta en tiempo real.
- **Un párrafo que cruza de una página a otra del PDF** quedaría dividido en dos. No ocurre en el documento actual, pero podría pasar con otros PDF.

### Funcionalidad

- **El umbral de relevancia (0,45) es un valor inicial**, no calibrado con datos reales. Depende del modelo de embeddings y del tipo de preguntas. Se debe ajustar con `buscar.py` y el experimento 3: demasiado alto, y el asistente dirá "no sé" a preguntas que sí puede responder; demasiado bajo, y recibirá fragmentos irrelevantes.
- **La evaluación es limitada**: 14 preguntas para la recuperación y unos pocos casos para la generación. Una evaluación seria necesitaría cientos de preguntas reales, revisadas por personas, y métricas de fidelidad de la respuesta (por ejemplo, con un marco como RAGAS).
- **Sin verificación de identidad**: cualquiera que conozca un número de seguimiento puede consultar ese pedido. En producción se pediría un segundo dato (como el correo registrado).
- **Memoria corta**: el orquestador ve los últimos 6 turnos de la conversación.
- **Los tickets de escalamiento** se guardan en un archivo (`resultados/tickets_escalados.jsonl`), no se envían a un sistema de soporte real.
- **Un solo canal** (consola). La propuesta contempla chat, correo y redes sociales.

## 2. Suposiciones

1. **Ollama disponible localmente**, con los modelos `qwen3:4b` y `bge-m3` descargados (~3,5 GB en total).
2. **El volumen de EcoMarket es moderado** (miles de consultas diarias y una base de conocimiento de miles de documentos, no de millones). Esto justifica que la escalabilidad de la base vectorial no sea la restricción principal.
3. **Los documentos fuente tienen estructura reconocible** (títulos y subsecciones numeradas). Si llegaran PDF escaneados o sin estructura, habría que agregar OCR y usar solo la segmentación recursiva.
4. **Existe un responsable de mantener los documentos** actualizados y sin contradicciones, y de reindexar cuando cambian.
5. **Los pedidos viven en una base de datos transaccional** con una consulta por número de seguimiento; aquí se simula con un archivo JSON.
6. **La fecha de referencia es fija** (24 de septiembre de 2026, configurable con `FECHA_REFERENCIA`) para que los plazos de devolución den siempre el mismo resultado.
7. **Los clientes escriben en español.** BGE-M3 y Qwen3 son multilingües, pero los prompts y los documentos están en español.

## 3. Por qué el prototipo sigue siendo representativo

Aunque se use un modelo pequeño y Qdrant en modo local, **la arquitectura es la misma que en producción**: los mismos pasos de indexación, el mismo flujo de recuperación con filtros y umbral, las mismas cadenas y prompts. Lo que cambia al llevarlo a producción es dónde corren las piezas (variables de entorno `OLLAMA_MODEL`, `QDRANT_URL`), no cómo se conectan. Por eso los experimentos sirven para entender el efecto de cada decisión, aunque los números exactos cambiarían con modelos más grandes y más datos.
