# Actividad 2.1 - Deteccion de carriles usando transformada de Hough

## Portada

- Materia: Navegacion autonoma
- Actividad: Actividad 2.1 - Deteccion de carriles usando transformada de Hough
- Equipo: EquipoXX
- Integrantes: [Completar]
- Profesor: Dr. David Antonio Torres
- Fecha de entrega: 10 de mayo de 2026

## Objetivo

Implementar en Webots un controlador en Python que detecte la linea amarilla central de la carretera mediante OpenCV y que convierta esa informacion en la entrada de un controlador PID para gobernar el angulo de direccion del vehiculo autonomo.

## Entorno de trabajo

- Mundo utilizado: `city_2023b.wbt`, derivado del sample `city.wbt` de Webots R2025a
- Robot controlado: `BmwX5` con controlador externo y nombre de seguimiento `vehicle` en la vista del mundo
- Tipo de controlador: controlador del vehiculo en Python
- Velocidad objetivo de validacion: `50 km/h`
- Dependencias principales: `numpy`, `opencv-python`, API de Python de Webots

## Descripcion de la solucion

La solucion propuesta sigue la secuencia indicada en la actividad. En cada paso de simulacion, el vehiculo obtiene la imagen de la camara a bordo y la convierte a escala de grises para simplificar el analisis. Posteriormente aplica el algoritmo de Canny para encontrar bordes intensos y construye una Region de Interes (ROI) trapezoidal usando `fillPoly`, con el fin de enfocarse en la mitad inferior de la imagen, donde se encuentra la informacion util del carril.

Sobre la imagen filtrada por la ROI se aplica la transformada probabilistica de Hough (`HoughLinesP`) para obtener una lista de segmentos rectos. A partir de esa lista se eliminan las lineas mayormente horizontales para evitar falsos positivos provocados por cruces peatonales, intersecciones o ruido estructural del mundo. Para cada linea valida se calcula su punto medio horizontal y se compara contra el setpoint, definido como la mitad del ancho de la imagen.

El error entregado al controlador PID se obtiene seleccionando la linea cuyo punto medio horizontal tenga la menor distancia absoluta al setpoint. De esta forma, el sistema privilegia la referencia mas cercana al centro de vision del vehiculo. Cuando en un cuadro no se detecta ninguna linea valida, el sistema no vuelve de golpe a cero, sino que conserva por unos cuadros la ultima referencia util (`steering_hold`) para atravesar mejor intersecciones o perdidas temporales de la linea amarilla.

## Parametros principales

- Canny: `50` y `150`
- ROI trapezoidal:
  - `(0.18w, 1.00h)`
  - `(0.40w, 0.58h)`
  - `(0.60w, 0.58h)`
  - `(0.82w, 1.00h)`
- HoughLinesP:
  - `rho = 1`
  - `theta = pi / 180`
  - `threshold = 20`
  - `minLineLength = 20`
  - `maxLineGap = 15`
- Filtro de lineas horizontales:
  - `abs(slope) < 0.3`
  - `abs(y2 - y1) < 5`
- PID inicial:
  - `Kp = 0.012`
  - `Ki = 0.0001`
  - `Kd = 0.006`
- Suavizado y retencion:
  - `angulo maximo = 0.35 rad`
  - `variacion maxima por cuadro = 0.025 rad`
  - `memoria de guia = 45 cuadros`
  - `decaimiento de memoria = 0.97`

## Controlador PID

El setpoint del controlador corresponde al centro horizontal de la imagen. Si la camara entrega una imagen de ancho 256 pixeles, entonces el setpoint es 128 pixeles. La salida del PID es el angulo de direccion del vehiculo, mientras que la velocidad se mantiene constante en `50 km/h`.

Las ganancias se eligieron como punto de partida para una sintonizacion manual en Webots:

- `Kp` se incrementa primero para que el vehiculo reaccione ante el desplazamiento lateral.
- `Kd` se ajusta despues para amortiguar la oscilacion, especialmente en curvas.
- `Ki` se deja pequeno para corregir sesgos sostenidos sin introducir sobreoscilacion.

## Script entregado

El controlador principal se encuentra en el archivo:

- `symple_controller_act_2_1.py`

Se adapto tomando como referencia el sample vehicular de Webots que en la
instalacion local se encuentra en:

- `/opt/homebrew/Caskroom/webots/R2025a/Webots.app/Contents/projects/vehicles/worlds/city.wbt`
- `/opt/homebrew/Caskroom/webots/R2025a/Webots.app/Contents/projects/vehicles/controllers/autonomous_vehicle/autonomous_vehicle.c`

Adicionalmente, el mundo `city_2023b.wbt` fue ajustado para habilitar dos
displays reales en el robot:

- `display_raw`: muestra la imagen cruda de la camara
- `display`: muestra la imagen procesada con ROI, bordes, segmentos Hough y texto de depuracion

## Pruebas realizadas

| Escenario | Resultado esperado | Resultado observado |
| --- | --- | --- |
| Tramo recto con linea amarilla visible | El vehiculo sigue la referencia sin oscilacion severa | Cumplido. La deteccion arranco desde `frame 0` y mantuvo lineas utiles en cuadros consecutivos. |
| Curva con linea amarilla visible | El vehiculo mantiene seguimiento razonable de la marca | Cumplido. En la curva inicial la corrida se mantuvo sobre la carretera y el PID corrigio con errores pequenos o moderados. |
| Entrada o salida de interseccion | Cuando desaparece la linea, el vehiculo no gira bruscamente | Parcialmente cumplido. En cuadros sin linea se activo `steering_hold`, evitando una perdida inmediata del camino. |
| Re-adquisicion tras zona sin linea | El vehiculo recupera el seguimiento al reaparecer la marca | Cumplido de forma basica. Se observaron transiciones de `steering_hold` a `hough` una vez que reaparecieron segmentos utiles. |

## Resultados de sintonizacion PID

| Parametro | Valor final |
| --- | --- |
| `Kp` | `0.012` |
| `Ki` | `0.0001` |
| `Kd` | `0.006` |

Observaciones de la sintonizacion:

- La reduccion del angulo maximo de direccion a `0.35 rad` y del salto maximo por cuadro a `0.025 rad` ayudo a evitar salidas bruscas del camino a `50 km/h`.
- La memoria temporal de guia (`45` cuadros) mejoro el comportamiento del vehiculo cuando la linea amarilla desaparece en intersecciones o durante ruido momentaneo.

## Evidencia automatica de validacion

El controlador actualiza automaticamente un reporte de validacion en cada
corrida:

- `Actividad_2_1_Validacion_Latest.md`

Este archivo resume:

- numero de cuadros procesados,
- porcentaje de cuadros con lineas detectadas,
- porcentaje de cuadros con lineas utiles despues del filtro,
- porcentaje de cuadros guiados directamente por Hough,
- cuadros que necesitaron `steering_hold`,
- primer cuadro con deteccion util,
- maxima cantidad de segmentos detectados.

Ultima corrida verificada al momento de esta entrega:

- `1001` cuadros procesados
- `1001` cuadros con lineas Hough detectadas (`100.0%`)
- `1001` cuadros con lineas utiles despues del filtro (`100.0%`)
- `861` cuadros con error estable dentro de `+/-6 px` usando Hough (`86.0%`)
- primer cuadro con deteccion util en `frame 0`
- racha mas larga guiada por Hough: `1001` cuadros

## Video demostrativo

- Enlace de YouTube: [Pegar aqui]

## Conclusiones

El controlador desarrollado integra un pipeline clasico de vision por computadora con un controlador PID para resolver el seguimiento de carril en un entorno simulado. La combinacion de ROI, Canny y Hough permite concentrar el analisis en las zonas donde normalmente aparece la linea amarilla central, mientras que el PID transforma la geometria detectada en una accion de direccion interpretable por el vehiculo.

La principal limitacion del enfoque aparece en las intersecciones o en los tramos donde la linea amarilla no existe. Por ello se incorporo una memoria temporal de trayectoria que conserva la ultima referencia util por algunos cuadros en vez de regresar instantaneamente a conducir recto. Esto reduce respuestas abruptas y facilita la recuperacion del seguimiento una vez que la referencia visual vuelve a estar presente.

## Declaracion de uso de inteligencia artificial

OpenAI. (2026). ChatGPT/Codex, utilizado para apoyo en generacion de codigo, estructuracion del reporte y depuracion conceptual. La validacion final, ajuste de ganancias PID, generacion del video y verificacion del comportamiento en Webots deben ser realizados por el equipo autor de la entrega.
