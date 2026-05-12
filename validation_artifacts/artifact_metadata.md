# Artefactos de validacion del pipeline

- Frame exportado: 0
- Resolucion: 128x64
- Hough total: 6
- Lineas utiles: 4
- Lineas horizontales filtradas: 2
- Fuente de guia: hough
- Error seleccionado: -4.00 px
- ROI: [[[23, 64], [51, 37], [76, 37], [104, 64]]]

## Archivos

- `01_raw_camera.png`: imagen capturada por la camara a bordo
- `02_grayscale.png`: conversion a escala de grises
- `03_canny_edges.png`: bordes detectados con Canny
- `04_roi_mask.png`: mascara creada con fillPoly
- `05_roi_applied.png`: bordes luego de aplicar la ROI
- `06_hough_lines.png`: lineas rectas detectadas por Hough sobre la imagen procesada
