# Validacion automatica de la corrida actual

## Resumen

- Cuadros procesados: 8401
- Cuadros con al menos una linea Hough detectada: 8384 (99.8%)
- Cuadros con lineas utiles despues del filtro: 7975 (94.9%)
- Cuadros guiados directamente por Hough: 7975 (94.9%)
- Cuadros que usaron retencion temporal ('steering_hold'): 247 (2.9%)
- Cuadros con error estable (+/-6 px) usando Hough: 7012 (83.5%)
- Cuadros con pixeles amarillos visibles: 2578 (30.7%)
- Primer cuadro con guia Hough: frame 1
- Racha mas larga de cuadros guiados por Hough: 1390
- Maximo de lineas Hough detectadas en un cuadro: 21
- Maximo de lineas utiles en un cuadro: 15

## Interpretacion

- 'Lineas detectadas' cuenta cualquier segmento regresado por Hough dentro de la ROI.
- 'Lineas utiles' ya excluye segmentos mayormente horizontales para evitar contaminar el PID.
- 'steering_hold' indica cuadros en los que la linea desaparecio temporalmente y el vehiculo siguio con la ultima referencia valida.
