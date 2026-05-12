# Validacion automatica de la corrida actual

## Resumen

- Cuadros procesados: 1401
- Cuadros con al menos una linea Hough detectada: 1368 (97.6%)
- Cuadros con lineas utiles despues del filtro: 1332 (95.1%)
- Cuadros guiados directamente por Hough: 1332 (95.1%)
- Cuadros que usaron retencion temporal ('steering_hold'): 59 (4.2%)
- Cuadros con error estable (+/-6 px) usando Hough: 1093 (78.0%)
- Cuadros con pixeles amarillos visibles: 1219 (87.0%)
- Primer cuadro con guia Hough: frame 0
- Racha mas larga de cuadros guiados por Hough: 1116
- Maximo de lineas Hough detectadas en un cuadro: 10
- Maximo de lineas utiles en un cuadro: 7

## Interpretacion

- 'Lineas detectadas' cuenta cualquier segmento regresado por Hough dentro de la ROI.
- 'Lineas utiles' ya excluye segmentos mayormente horizontales para evitar contaminar el PID.
- 'steering_hold' indica cuadros en los que la linea desaparecio temporalmente y el vehiculo siguio con la ultima referencia valida.
