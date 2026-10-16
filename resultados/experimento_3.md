# Experimento 3: prompt estricto vs. permisivo

Modelo: `qwen3.5:2b` · Embeddings: `bge-m3` · Generado: 2026-10-16 14:13

Preguntas cuya respuesta **no está** en la base de conocimiento (la última es un control que sí está).

- **Estricto**: prompt principal con reglas de anclaje + umbral de similitud (0.45); si ningún fragmento lo supera, se responde "no tengo esa información" sin llamar al modelo.
- **Permisivo**: prompt sin reglas ("usa este contexto como ayuda") y sin umbral: el modelo recibe los 4 fragmentos más parecidos, aunque no tengan que ver.

## ¿Tienen descuento para estudiantes?

Mejor similitud encontrada: **0.534** (preguntas_frecuentes.json · FAQ09) · fragmentos sobre el umbral: 4

**Estricto:**

> No tenemos información sobre descuentos específicos para estudiantes en nuestro catálogo o preguntas frecuentes. Si deseas saber más, puedes contactarnos con un agente humano.
> 
> Fuente: [1], [2], [3], [4]

**Permisivo:**

> ¡Hola! Claro que sí, ¡te esperamos en EcoMarket! 🌿✨
> 
> Aunque no tenemos un descuento específico solo por ser estudiante, **siempre puedes aprovechar ofertas especiales** a través de nuestro programa de fidelidad. Cuando completes tu primera compra, te invitamos a crear una cuenta para recibir notificaciones sobre promociones exclusivas y descuentos en productos seleccionados.
> 
> ¿Te gustaría que te ayude a configurar tu perfil de invitado o quieres saber más sobre nuestras campañas actuales? ¡Cuéntanos qué buscas! 🛒💚

## ¿Hacen entregas el mismo día en Bogotá?

Mejor similitud encontrada: **0.684** (politicas_ecomarket.pdf · Política de envíos, sección 2.2) · fragmentos sobre el umbral: 4

**Estricto:**

> Sí, en Bogotá las entregas tardan entre 2 y 4 días hábiles desde que el pedido sale de la bodega. Fuente: [1]

**Permisivo:**

> ¡Hola! Claro que sí, en Bogotá **sí hacemos entregas el mismo día** si tu pedido sale antes de las 12:00 PM (mediodía). 🚚🌿
> 
> Según nuestra política de envíos, los tiempos de entrega en Bogotá son de **2 a 4 días hábiles**. Esto significa que, una vez que recibimos tu compra y procesamos el envío, la transportadora te contactará para confirmar la fecha exacta. Si tu pedido sale antes del mediodía, es muy probable que llegue al día siguiente o incluso el mismo día dependiendo del tráfico y las condiciones de la ciudad.
> 
> ¿Te gustaría saber cómo reportar un retraso si no llega a tiempo? ¡Estoy aquí para ayudarte! 😊

## ¿Venden paneles solares de 100 W para el techo?

Mejor similitud encontrada: **0.570** (catalogo_inventario.csv · P09 Panel solar portátil 20 W) · fragmentos sobre el umbral: 4

**Estricto:**

> No tenemos información sobre paneles solares de 100 W en nuestro catálogo actual. Solo disponemos de productos como el Panel solar portátil de 20 W y la Lámpara solar de jardín, ambas con potencia menor a 100 W. Si necesitas más detalles, te contactaremos con un agente humano.
> 
> Fuente: [1], [2]

**Permisivo:**

> ¡Hola! 👋 Claro que sí, te puedo ayudar con eso.
> 
> En nuestro catálogo tenemos varios modelos de **paneles solares portátiles** (como el modelo P09 de 20 W) y también una lámpara solar de jardín, pero no encontramos paneles solares de techo específicos en nuestra lista actual. Sin embargo, para darte la mejor opción:
> 
> ¿Te gustaría que te muestre los modelos **portátiles** disponibles ahora? Son ideales si solo necesitas energía para cargar dispositivos o iluminación temporal. También puedo buscar opciones de **paneles solares grandes** (como los de 100 W) en nuestra base de datos, aunque quizás necesites contactar directamente a nuestro equipo de ventas por teléfono para ver disponibilidad y precios exactos.
> 
> ¿Qué te parece? ¿Prefieres que busque paneles portátiles o modelos más grandes para el techo? 🌞✨

## ¿Cuál es la capital de Australia?

Mejor similitud encontrada: **0.260** (politicas_ecomarket.pdf · Política de envíos, sección 2.2) · fragmentos sobre el umbral: 0

**Estricto:**

> Lo siento, no tengo información sobre eso en mi base de conocimiento, y prefiero no darte un dato que no pueda confirmar. Puedo ayudarte con el estado de tus pedidos, devoluciones, envíos, garantías, medios de pago y nuestros productos. Si quieres, también te comunico con una persona de nuestro equipo.

**Permisivo:**

> ¡Hola! Bienvenido a EcoMarket, tu aliado para productos sostenibles. 😊
> 
> Sin embargo, tengo que decirte algo importante: **Australia no tiene capital**. Como país independiente, su capital es el **Canberra**, donde se encuentra la sede del gobierno federal y de sus tres estados principales (Queensland, Nueva Gales del Sur y el Territorio del Norte).
> 
> ¿Te gustaría saber más sobre nuestros productos ecológicos o alguna otra duda? ¡Estoy aquí para ayudarte! 🌿🇦🇺

## ¿Los productos de higiene personal se pueden devolver?

Mejor similitud encontrada: **0.740** (politicas_ecomarket.pdf · Política de devoluciones, sección 1.2) · fragmentos sobre el umbral: 4

**Estricto:**

> No, los productos de higiene personal no se aceptan para devoluciones porque su función es proteger la salud de todos nuestros clientes. Solo se pueden devolver si el producto está defectuoso o dañado en los primeros 5 días calendario desde la entrega.
> 
> Fuente: [1], [4]

**Permisivo:**

> ¡Hola! Claro que sí, te respondo con gusto para ayudarte.
> 
> Sin embargo, **no se aceptan devoluciones de productos de higiene personal**, como cepillos de dientes, champús y desodorantes. Esto es porque no se reciben por razones de salud e higiene en nuestra tienda.
> 
> ¿Te gustaría saber más sobre las otras categorías que sí pueden ser devueltas o cómo proceder si tu producto tiene algún problema?
