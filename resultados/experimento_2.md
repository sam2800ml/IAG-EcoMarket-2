# Experimento 2: estrategias de segmentación

Modelo: `qwen3.5:2b` · Embeddings: `bge-m3` · Generado: 2026-10-16 14:11

Se indexa solo el PDF de políticas con cada estrategia y se hacen las mismas 14 preguntas. Un **acierto** significa que la frase exacta que contiene la respuesta aparece completa en un fragmento recuperado. Si la estrategia la partió en dos, el modelo de lenguaje no puede responder bien aunque la búsqueda "casi" acierte.

- **Acierto@1**: la frase está en el primer resultado.
- **Acierto@3**: la frase está en alguno de los 3 primeros.
- **MRR**: promedio de 1/posición del primer acierto (1 = siempre primero).

## Comparación de estrategias

| Estrategia | Fragmentos | Long. promedio | Acierto@1 | Acierto@3 | MRR |
|---|---|---|---|---|---|
| Tamaño fijo (500, sin solapamiento) | 14 | 479 | 86% | 93% | 0.89 |
| Por párrafos | 59 | 112 | 79% | 93% | 0.86 |
| Recursiva (500/75) sin estructura | 19 | 378 | 86% | 100% | 0.92 |
| Estructural + recursiva (500/75) · ELEGIDA | 24 | 301 | 100% | 100% | 1.00 |

Preguntas sin acierto en el top 3:

- **Tamaño fijo (500, sin solapamiento):** ¿Las tarjetas regalo se pueden devolver?
- **Por párrafos:** ¿Puedo devolver un desodorante que no me gustó?

## Efecto del tamaño de chunk (estrategia elegida)

| Estrategia | Fragmentos | Long. promedio | Acierto@1 | Acierto@3 | MRR |
|---|---|---|---|---|---|
| Estructural + recursiva (150/22) | 60 | 155 | 100% | 100% | 1.00 |
| Estructural + recursiva (300/45) | 30 | 252 | 100% | 100% | 1.00 |
| Estructural + recursiva (1000/150) | 23 | 311 | 100% | 100% | 1.00 |
| Estructural + recursiva (500/75) · ELEGIDA | 24 | 301 | 100% | 100% | 1.00 |

## Ejemplo de por qué falla el tamaño fijo

Final de un fragmento y comienzo del siguiente con la estrategia de tamaño fijo:

```text
…ientes a la entrega y adjuntar una foto del producto y del empaque.

1.4 Pedidos que aún no se han entregado

Si el pedido está en preparación, el cliente puede
--- corte ---
 cancelarlo sin costo en lugar de devolverlo. Si ya fue enviado, está en tránsito o retrasado, debe esperar a recibirlo para iniciar la devolución.

1.5 Proceso…
```