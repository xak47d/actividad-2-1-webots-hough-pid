---
title: "Actividad 2.1 - Detección de carriles usando transformada de Hough"
source: "https://experiencia21.tec.mx/courses/663304/assignments/22121919?module_item_id=41364549"
author:
published: 2026-05-10
created: 2026-05-06
description:
tags:
  - "clippings"
---
Disponible hasta 10 de may de 2026 23:59

## Objetivo

---

Identificar las etapas necesarias de procesamiento de imágenes con OpenCV para la detección de carriles en vehículos autónomos.

## Instrucciones

---

1. Abre Webots y carga el mundo (world) desarrollado en la active class. Habilita los displays de la cámara para que se pueda observar la imagen capturada por la cámara. Toma en cuenta que este mundo tiene intersecciones, por lo cual hay tramos de carretera sin línea amarilla.
2. Usando el script de Python explicado en la active class previa, agrega el código que incorpore todos los pasos necesarios para la detección de carriles, siguiendo la secuencia presentada en los materiales de aprendizaje de este módulo:
	1. Colocación del vehículo autónomo sobre la línea amarilla central de las carreteras del mundo.
		2. Obtención de la imagen a partir de la cámara a bordo.
		3. Obtención de la imagen en escala de grises.
		4. Detección de bordes usando el algoritmo de Canny.
		5. Definición y aplicación de una región de interés usando la función fillPoly.
		6. Detección de líneas rectas usando la transformada de Hough (HoughLinesP).
3. La salida del código del código anterior debe ser una lista de líneas detectadas, las cuales se deben convertir en la entrada de un controlador PID. Para desarrollar el código necesario del controlador PID, puedes consultar el siguiente material:
	1. [https://medium.com/@aleksej.gudkov/python-pid-controller-example-a-complete-guide-5f35589eec86 Enlaces a un sitio externo.](https://medium.com/@aleksej.gudkov/python-pid-controller-example-a-complete-guide-5f35589eec86)
		2. [https://la.mathworks.com/videos/understanding-pid-control-part-1-what-is-pid-control--1527089264373.html Enlaces a un sitio externo.](https://la.mathworks.com/videos/understanding-pid-control-part-1-what-is-pid-control--1527089264373.html)
4. El controlador PID debe tener las siguientes características:
	1. El setpoint o punto de referencia debe ser el valor medio del ancho de la imagen regresada por la cámara, por ejemplo, para una cámara de 256 pixeles de ancho, el setpoint es igual a 128. Las dimensiones deseadas de la imagen se pueden modificar en el mundo de Webots, modificando el ancho y alto de la cámara.
		2. La salida del controlador debe ser el ángulo de conducción del vehículo. La velocidad puede mantenerse constante a lo largo del recorrido.
		3. El error del controlador se puede obtener a partir del error más pequeño que se obtenga calculando la distancia entre el punto medio horizontal de cada línea y el setpoint.
		4. Se recomienda no incorporar líneas mayormente horizontales en el cálculo del error para no alterar el comportamiento esperado del controlador.
5. En caso de que la imagen no proporcione alguna línea que se pueda detectar, se sugiere que se defina un ángulo por omisión, por ejemplo, conducir recto.
6. El código resultante de esta actividad se debe validar para una velocidad mínima de 50 kmh.
7. Agrega los comentarios necesarios a tu script de Python para explicar cada uno de los pasos, entre ellos, la definición de la Región de Interés, el número de líneas generadas por la Transformada de Hough, cálculo del error más pequeño a partir de las líneas detectadas, etc.
8. Verifica que tu script funcione correctamente en el mundo y que la detección de la línea suceda en cada una de las imágenes regresadas por la cámara, por supuesto, donde haya línea amarilla.
9. Realiza las pruebas suficientes para poder estimar cada una de las ganancias del controlador PID.
10. Durante la prueba de tu código en el mundo, haz uso de las herramientas de Webots para crear un video demostrativo. Sube tu video a tu canal de YouTube y guarda el enlace.
11. Como reporte, crea un documento que incluya tu script con los comentarios y el enlace de tu video en YouTube. Tanto el código como los comentarios son importantes para el documento.

## Especificaciones de entrega

---

- **Modalidad:** En equipos.
- **Medio de realización/entrega:** A través del botón "Entregar Tarea" de esta actividad.
- **Formato:** DOC/DOCX o PDF.
- **Nombre del entregable:** Actividad\_2.1\_Detección\_de\_Carriles\_EquipoXX
- La evaluación de la actividad se podrá revisar en la sección de "Calificaciones" en Canvas.

**IMPORTANTE:**

- El uso de herramientas de inteligencia artificial deberá declararse de manera explícita; en ningún caso se deberá presentar como propio un producto generado total o parcialmente por dichas herramientas. Cuando se utilicen, deberá indicarse la herramienta y el modelo empleado en la entrega, así como la finalidad de su uso (generación de código / depuración / optimización).
- Ejemplo: OpenAI. (2026). *ChatGPT (basado en GPT-4)* \[Modelo de lenguaje grande\], utilizado para generación de código y depuración. [https://chat.openai.com/ Enlaces a un sitio externo.](https://nam04.safelinks.protection.outlook.com/?url=https%3A%2F%2Fchat.openai.com%2F&data=05%7C02%7Cdavidant%40tec.mx%7C827e2a68f8ac4a47cea608de9b4cd903%7Cc65a3ea60f7c400b89345a6dc1705645%7C0%7C0%7C639118951517906122%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=e6gWi3JtzOsbIiAYmErCc541L1a72mb48a8FdKWOc10%3D&reserved=0 "Original URL: https://chat.openai.com/. Click or tap if you trust this link.")
- La responsabilidad final sobre el contenido entregado recae en el autor. El estudiante deberá asegurar que las soluciones presentadas se ajusten estrictamente a lo solicitado, evitando la inclusión de código innecesario, excesivamente complejo o no requerido. El incumplimiento de este criterio podrá derivar en penalizaciones en la evaluación de la actividad.

## Recursos de apoyo

---

Revisa nuevamente los Jupyter Notebooks de este módulo y selecciona las porciones de código adecuadas para la solución de esta actividad.

Rúbrica: Actividad 2.1

| Criterios | Calificaciones | Puntos |
| --- | --- | --- |
| Portada |  | /10 pts |
| Código y comentarios |  | /60 pts |
| Video demostrativo |  | /30 pts |

Recuerde que esta entrega contará para todos en su grupo Project Groups.

Elegir un tipo de presentación

o