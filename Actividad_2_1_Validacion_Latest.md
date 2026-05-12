# Validacion automatica de la corrida actual

## Resumen

- Cuadros procesados: 81901
- Cuadros con al menos una linea Hough detectada: 81855 (99.9%)
- Cuadros con lineas utiles despues del filtro: 81729 (99.8%)
- Cuadros guiados directamente por Hough: 81729 (99.8%)
- Cuadros que usaron retencion temporal ('steering_hold'): 161 (0.2%)
- Cuadros con error estable (+/-6 px) usando Hough: 2654 (3.2%)
- Cuadros con pixeles amarillos visibles: 2480 (3.0%)
- Primer cuadro con guia Hough: frame 0
- Racha mas larga de cuadros guiados por Hough: 78650
- Maximo de lineas Hough detectadas en un cuadro: 19
- Maximo de lineas utiles en un cuadro: 16

## Interpretacion

- 'Lineas detectadas' cuenta cualquier segmento regresado por Hough dentro de la ROI.
- 'Lineas utiles' ya excluye segmentos mayormente horizontales para evitar contaminar el PID.
- 'steering_hold' indica cuadros en los que la linea desaparecio temporalmente y el vehiculo siguio con la ultima referencia valida.
