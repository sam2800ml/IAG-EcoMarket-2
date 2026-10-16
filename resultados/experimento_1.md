# Experimento 1: sin RAG vs. con RAG

Modelo: `qwen3.5:2b` · Embeddings: `bge-m3` · Generado: 2026-10-16 14:11

Mismo modelo, misma pregunta y misma temperatura. Lo único que cambia es si el prompt recibe los fragmentos recuperados de Qdrant.

La columna *dato esperado* es una verificación automática aproximada: revisa si la respuesta contiene el dato correcto de la base de conocimiento. Conviene leer las respuestas completas.

| Pregunta | Dato esperado | Sin RAG | Con RAG |
|---|---|---|---|
| ¿Cuántos días tengo para devolver un producto? | `30 dias` | ✅ | ✅ |
| ¿Desde qué valor de compra el envío es gratis? | `150.000` | ❌ | ✅ |
| ¿Cuánto cuesta el panel solar portátil y qué puertos tiene? | `320.000` | ❌ | ✅ |
| ¿Puedo pagar contra entrega? | `no aceptamos` | ❌ | ✅ |
| ¿Tienen tienda física donde pueda recoger mi pedido? | `en linea` | ❌ | ✅ |

## Respuestas completas

### ¿Cuántos días tengo para devolver un producto?

**Sin RAG:**

> ¡Hola! Claro que sí, tenemos una política de devolución muy flexible. Puedes devolver cualquier producto dentro de los **30 días** desde la fecha de compra, siempre que esté en su estado original y con la etiqueta intacta. Solo necesitas enviarlo a nuestro centro de recolección o hacerlo directamente en nuestra tienda. ¿Te gustaría saber cómo iniciar el proceso?

**Con RAG:**

> Para devolver un producto, tienes hasta **30 días calendario** siguientes a la fecha de entrega registrada por tu transportadora. El plazo comienza el día siguiente al día 1. Si recibes el pedido después del día 30, no se aceptan las devoluciones salvo que sea una garantía.
> 
> Fuente: [1]

<details><summary>Fragmentos recuperados</summary>

- 0.778 · politicas_ecomarket.pdf · Política de devoluciones, sección 1.1
- 0.721 · politicas_ecomarket.pdf · Política de devoluciones, sección 1.3
- 0.715 · politicas_ecomarket.pdf · Política de devoluciones, sección 1.5
- 0.662 · preguntas_frecuentes.json · FAQ04

</details>

### ¿Desde qué valor de compra el envío es gratis?

**Sin RAG:**

> ¡Hola! Claro que sí, con EcoMarket te ofrecemos envío gratis a partir de $50.000 COP para todos nuestros productos sostenibles. ¿Te gustaría saber cómo calcular tu envío exacto o necesitas ayuda con algún pedido específico? ¡Estamos aquí para ayudarte!

**Con RAG:**

> El envío es gratuito para compras con un valor de 150.000 pesos colombianos o más. Para valores menores, el costo varía según la ubicación: 9.900 pesos en ciudades principales y 14.900 pesos en el resto del país. Este precio se muestra antes de finalizar el pago.
> 
> Fuente: [1]

<details><summary>Fragmentos recuperados</summary>

- 0.741 · politicas_ecomarket.pdf · Política de envíos, sección 2.3
- 0.552 · preguntas_frecuentes.json · FAQ04
- 0.544 · catalogo_inventario.csv · P14 Tarjeta regalo EcoMarket
- 0.542 · politicas_ecomarket.pdf · Política de devoluciones, sección 1.5

</details>

### ¿Cuánto cuesta el panel solar portátil y qué puertos tiene?

**Sin RAG:**

> ¡Hola! Claro que sí, te cuento que nuestro panel solar portátil es muy económico, rondando los $350 COP por unidad. Además, cuenta con dos puertos USB para cargar tus dispositivos fácilmente mientras lo usas en el campo. ¿Te gustaría saber más sobre sus características o cómo pedirlo?

**Con RAG:**

> El Panel Solar Portátil cuesta 320.000 pesos colombianos y cuenta con puertos USB-A y USB-C para cargar celulares, baterías externas y lámparas. Fuente: [1]

<details><summary>Fragmentos recuperados</summary>

- 0.716 · catalogo_inventario.csv · P09 Panel solar portátil 20 W
- 0.567 · catalogo_inventario.csv · P18 Cargador solar con batería 10000 mAh
- 0.544 · catalogo_inventario.csv · P15 Lámpara solar de jardín
- 0.471 · catalogo_inventario.csv · P06 Mochila de lona reciclada

</details>

### ¿Puedo pagar contra entrega?

**Sin RAG:**

> ¡Hola! Claro que sí, EcoMarket ofrece pago contra entrega para todos nuestros productos sostenibles. Solo necesitas completar el pedido antes de la recogida y nos coordinaremos contigo para entregarlo en tu domicilio preferido. ¿Necesitas ayuda con algún detalle del proceso? ¡Estamos aquí para apoyarte!

**Con RAG:**

> No, no aceptamos pagos contra entrega ni en efectivo. Solo aceptamos tarjetas de crédito y débito Visa, Mastercard y American Express, así como PSE y Nequi o Daviplata.
> 
> Fuente: [1]

<details><summary>Fragmentos recuperados</summary>

- 0.635 · politicas_ecomarket.pdf · Medios de pago y facturación, sección 4.1
- 0.604 · politicas_ecomarket.pdf · Política de devoluciones, sección 1.4
- 0.594 · preguntas_frecuentes.json · FAQ03
- 0.593 · politicas_ecomarket.pdf · Política de envíos, sección 2.3

</details>

### ¿Tienen tienda física donde pueda recoger mi pedido?

**Sin RAG:**

> ¡Hola! Claro que sí, tenemos una tienda física en Bogotá llamada EcoMarket. Puedes visitarnos para recoger tu pedido o hacer un recibo de compra. ¿Te gustaría saber la dirección exacta o el horario de atención? ¡Estoy aquí para ayudarte! 🌿🛍️

**Con RAG:**

> No, EcoMarket es una tienda 100% en línea y no tenemos puntos de venta físicos ni puntos de recogida. Solo podemos comprar desde nuestra web.
> 
> Fuente: [1]

<details><summary>Fragmentos recuperados</summary>

- 0.609 · preguntas_frecuentes.json · FAQ07
- 0.562 · politicas_ecomarket.pdf · Política de envíos, sección 2.4
- 0.550 · preguntas_frecuentes.json · FAQ01
- 0.547 · preguntas_frecuentes.json · FAQ08

</details>
