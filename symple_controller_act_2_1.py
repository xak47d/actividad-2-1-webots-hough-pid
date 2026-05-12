"""Actividad 2.1 - Deteccion de carriles con Hough + controlador PID en Webots.

Este controlador fue pensado para ejecutarse sobre el sample stock
`city.wbt` de Webots R2025a o sobre una copia derivada como `city_2023b.wbt`
usando el robot `vehicle` o el BmwX5 del mundo base. El flujo sigue
exactamente la secuencia solicitada en la actividad:

1. Captura de imagen desde la camara a bordo.
2. Conversion a escala de grises.
3. Deteccion de bordes con Canny.
4. Aplicacion de una region de interes (ROI) con fillPoly.
5. Deteccion de lineas con HoughLinesP.
6. Seleccion del error minimo respecto al centro horizontal de la imagen.
7. Conversion del error a un angulo de direccion usando un PID discreto.

Notas importantes para usarlo en Webots:
- Debe existir al menos una camara en el robot.
- El mundo `city.wbt` stock trae un `Display` llamado `display`.
- Si agregas un segundo `Display`, este script puede mostrar imagen cruda y
  procesada por separado; si no, al menos muestra la vista procesada.
- Si los nombres de los dispositivos no coinciden con los candidatos
  definidos abajo, basta con ajustar las listas de nombres.
- La velocidad objetivo se mantiene en 50 km/h, como solicita la consigna.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - depende del entorno Webots.
    raise SystemExit(
        "No se encontro OpenCV. Instala la dependencia 'opencv-python' en el "
        "Python configurado para Webots antes de ejecutar este controlador."
    ) from exc

try:
    from controller import Display
    from vehicle import Driver
except ImportError as exc:  # pragma: no cover - depende del entorno Webots.
    raise SystemExit(
        "Este script debe ejecutarse desde el entorno de Webots con acceso a "
        "los modulos 'controller' y 'vehicle'."
    ) from exc


# Candidatos de nombres para facilitar el acoplamiento con el mundo recibido.
CAMERA_DEVICE_CANDIDATES = ("camera", "front_camera", "vehicle_camera")
RAW_DISPLAY_CANDIDATES = ("display_raw", "camera_display_raw", "raw_display")
PROCESSED_DISPLAY_CANDIDATES = (
    "display",
    "display_processed",
    "camera_display_processed",
    "processed_display",
    "display2",
)

# Parametros de la actividad.
TARGET_SPEED_KMH = 50.0
MAX_STEERING_ANGLE = 0.35
MAX_STEERING_DELTA = 0.025
INTEGRAL_LIMIT = 3000.0
DEBUG_EVERY_N_STEPS = 10
VALIDATION_WRITE_EVERY_N_STEPS = 100
GUIDANCE_MEMORY_FRAMES = 45
GUIDANCE_DECAY = 0.97
STEERING_HOLD_DECAY = 0.985
ERROR_SMOOTHING_ALPHA = 0.30
STABLE_ERROR_THRESHOLD_PX = 6.0
VALIDATION_REPORT_PATH = Path(__file__).with_name("Actividad_2_1_Validacion_Latest.md")
ARTIFACTS_DIR = Path(__file__).with_name("validation_artifacts")

# Parametros base de la deteccion de lineas.
CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150
HOUGH_RHO = 1
HOUGH_THETA = np.pi / 180.0
HOUGH_THRESHOLD = 12
HOUGH_MIN_LINE_LENGTH = 12
HOUGH_MAX_LINE_GAP = 18
MIN_ABS_SLOPE = 0.12
MIN_DELTA_Y = 3

# Parametros de una guia auxiliar basada en color amarillo. Esta guia no
# reemplaza la deteccion principal por Hough; solo sirve para mantener al
# vehiculo sobre el camino cuando al inicio aun no existen lineas Hough
# estables o cuando la linea se pierde durante unos pocos cuadros.
YELLOW_BGR_REFERENCE = np.array([95, 187, 203], dtype=np.int16)
YELLOW_DIFF_THRESHOLD = 65
YELLOW_MIN_PIXELS = 8


def clamp(value: float, lower: float, upper: float) -> float:
    """Limita un valor a un rango cerrado."""
    return max(lower, min(upper, value))


def limit_steering_step(target_angle: float, previous_angle: float) -> float:
    """Suaviza la direccion para evitar giros demasiado bruscos.

    El controlador stock de Webots no aplica el angulo calculado de golpe:
    limita la variacion entre cuadros. Aqui se replica esa idea porque, a
    50 km/h, un salto instantaneo hacia +/-0.5 rad puede sacar el vehiculo
    del camino antes de que la vision recupere la linea amarilla.
    """
    delta = clamp(target_angle - previous_angle, -MAX_STEERING_DELTA, MAX_STEERING_DELTA)
    return clamp(previous_angle + delta, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE)


def try_get_device(driver: Driver, names: Iterable[str]):
    """Intenta obtener el primer dispositivo cuyo nombre exista en el robot."""
    for name in names:
        try:
            return driver.getDevice(name)
        except BaseException:
            continue
    return None


def camera_bgra_to_bgr(camera_image: bytes, width: int, height: int) -> np.ndarray:
    """Convierte la imagen BGRA de Webots a un arreglo BGR utilizable en OpenCV."""
    frame_bgra = np.frombuffer(camera_image, dtype=np.uint8).reshape((height, width, 4))
    return frame_bgra[:, :, :3].copy()


def bgr_to_display_bytes(image_bgr: np.ndarray) -> bytes:
    """Convierte una imagen BGR de OpenCV a bytes BGRA para pegarla en un Display."""
    image_bgra = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2BGRA)
    return image_bgra.tobytes()


def scale_to_display(image_bgr: np.ndarray, disp_w: int, disp_h: int) -> np.ndarray:
    """Escala la imagen al tamaño exacto del Display para que no queden bordes negros."""
    if image_bgr.shape[1] == disp_w and image_bgr.shape[0] == disp_h:
        return image_bgr
    return cv2.resize(image_bgr, (disp_w, disp_h), interpolation=cv2.INTER_LINEAR)


def build_roi_polygon(width: int, height: int) -> np.ndarray:
    """Construye la ROI trapezoidal pedida en la actividad.

    La ROI se limita a la mitad inferior porque ahi aparece la linea util para
    la conduccion inmediata. La parte superior contiene horizonte, edificios y
    elementos que agregan ruido a Canny y Hough.
    """
    return np.array(
        [
            [
                (int(0.18 * width), int(1.00 * height)),
                (int(0.40 * width), int(0.58 * height)),
                (int(0.60 * width), int(0.58 * height)),
                (int(0.82 * width), int(1.00 * height)),
            ]
        ],
        dtype=np.int32,
    )


@dataclass
class DetectionResult:
    """Contiene las salidas intermedias y finales del pipeline de vision."""

    processed_bgr: np.ndarray
    gray: np.ndarray
    edges: np.ndarray
    roi_mask: np.ndarray
    masked_edges: np.ndarray
    roi_polygon: np.ndarray
    detected_segments: list[tuple[int, int, int, int]]
    usable_segments: list[tuple[int, int, int, int]]
    rejected_horizontal_segments: int
    setpoint: float
    chosen_error: float
    guidance_source: str
    yellow_pixels: int


@dataclass
class ValidationStats:
    """Acumula evidencia objetiva de una corrida de validacion."""

    total_frames: int = 0
    frames_with_detected_segments: int = 0
    frames_with_usable_segments: int = 0
    frames_with_hough_guidance: int = 0
    frames_with_hold_guidance: int = 0
    frames_with_yellow_pixels: int = 0
    frames_with_stable_error: int = 0
    max_detected_segments: int = 0
    max_usable_segments: int = 0
    first_hough_frame: int | None = None
    longest_hough_streak: int = 0
    current_hough_streak: int = 0

    def observe(
        self,
        frame_index: int,
        detection: DetectionResult,
        applied_source: str,
        control_error: float,
    ) -> None:
        """Registra el estado de un cuadro para documentar la validacion."""
        self.total_frames += 1
        detected_count = len(detection.detected_segments)
        usable_count = len(detection.usable_segments)

        if detected_count > 0:
            self.frames_with_detected_segments += 1
        if usable_count > 0:
            self.frames_with_usable_segments += 1
        if detection.yellow_pixels > 0:
            self.frames_with_yellow_pixels += 1

        self.max_detected_segments = max(self.max_detected_segments, detected_count)
        self.max_usable_segments = max(self.max_usable_segments, usable_count)

        if applied_source == "hough":
            self.frames_with_hough_guidance += 1
            self.current_hough_streak += 1
            if self.first_hough_frame is None:
                self.first_hough_frame = frame_index
            self.longest_hough_streak = max(self.longest_hough_streak, self.current_hough_streak)
        else:
            self.current_hough_streak = 0

        if applied_source == "steering_hold":
            self.frames_with_hold_guidance += 1

        if applied_source == "hough" and abs(control_error) <= STABLE_ERROR_THRESHOLD_PX:
            self.frames_with_stable_error += 1


def ratio_text(count: int, total: int) -> str:
    """Devuelve una razon como porcentaje amigable para el reporte."""
    if total <= 0:
        return "0.0%"
    return f"{(100.0 * count / total):.1f}%"


def build_validation_summary(stats: ValidationStats) -> str:
    """Construye un resumen Markdown con la evidencia de validacion."""
    first_hough_text = "no detectado"
    if stats.first_hough_frame is not None:
        first_hough_text = f"frame {stats.first_hough_frame}"

    return "\n".join(
        [
            "# Validacion automatica de la corrida actual",
            "",
            "## Resumen",
            "",
            f"- Cuadros procesados: {stats.total_frames}",
            (
                f"- Cuadros con al menos una linea Hough detectada: "
                f"{stats.frames_with_detected_segments} ({ratio_text(stats.frames_with_detected_segments, stats.total_frames)})"
            ),
            (
                f"- Cuadros con lineas utiles despues del filtro: "
                f"{stats.frames_with_usable_segments} ({ratio_text(stats.frames_with_usable_segments, stats.total_frames)})"
            ),
            (
                f"- Cuadros guiados directamente por Hough: "
                f"{stats.frames_with_hough_guidance} ({ratio_text(stats.frames_with_hough_guidance, stats.total_frames)})"
            ),
            (
                f"- Cuadros que usaron retencion temporal ('steering_hold'): "
                f"{stats.frames_with_hold_guidance} ({ratio_text(stats.frames_with_hold_guidance, stats.total_frames)})"
            ),
            (
                f"- Cuadros con error estable (+/-{STABLE_ERROR_THRESHOLD_PX:.0f} px) usando Hough: "
                f"{stats.frames_with_stable_error} ({ratio_text(stats.frames_with_stable_error, stats.total_frames)})"
            ),
            (
                f"- Cuadros con pixeles amarillos visibles: "
                f"{stats.frames_with_yellow_pixels} ({ratio_text(stats.frames_with_yellow_pixels, stats.total_frames)})"
            ),
            f"- Primer cuadro con guia Hough: {first_hough_text}",
            f"- Racha mas larga de cuadros guiados por Hough: {stats.longest_hough_streak}",
            f"- Maximo de lineas Hough detectadas en un cuadro: {stats.max_detected_segments}",
            f"- Maximo de lineas utiles en un cuadro: {stats.max_usable_segments}",
            "",
            "## Interpretacion",
            "",
            "- 'Lineas detectadas' cuenta cualquier segmento regresado por Hough dentro de la ROI.",
            "- 'Lineas utiles' ya excluye segmentos mayormente horizontales para evitar contaminar el PID.",
            "- 'steering_hold' indica cuadros en los que la linea desaparecio temporalmente y el vehiculo siguio con la ultima referencia valida.",
        ]
    ) + "\n"


def write_validation_summary(stats: ValidationStats) -> None:
    """Guarda en disco un resumen que se actualiza durante cada corrida."""
    VALIDATION_REPORT_PATH.write_text(build_validation_summary(stats), encoding="utf-8")


def export_pipeline_artifacts(
    frame_bgr: np.ndarray,
    detection: DetectionResult,
    frame_index: int,
) -> None:
    """Guarda artefactos visuales para validar cada etapa del pipeline.

    Esto permite documentar en un notebook que la actividad cumple con:
    captura de camara, gris, Canny, ROI con fillPoly y HoughLinesP.
    """
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    raw_path = ARTIFACTS_DIR / "01_raw_camera.png"
    gray_path = ARTIFACTS_DIR / "02_grayscale.png"
    edges_path = ARTIFACTS_DIR / "03_canny_edges.png"
    roi_mask_path = ARTIFACTS_DIR / "04_roi_mask.png"
    roi_edges_path = ARTIFACTS_DIR / "05_roi_applied.png"
    hough_path = ARTIFACTS_DIR / "06_hough_lines.png"
    meta_path = ARTIFACTS_DIR / "artifact_metadata.md"

    cv2.imwrite(str(raw_path), frame_bgr)
    cv2.imwrite(str(gray_path), detection.gray)
    cv2.imwrite(str(edges_path), detection.edges)
    cv2.imwrite(str(roi_mask_path), detection.roi_mask)
    cv2.imwrite(str(roi_edges_path), detection.masked_edges)
    cv2.imwrite(str(hough_path), detection.processed_bgr)

    metadata_lines = [
        "# Artefactos de validacion del pipeline",
        "",
        f"- Frame exportado: {frame_index}",
        f"- Resolucion: {frame_bgr.shape[1]}x{frame_bgr.shape[0]}",
        f"- Hough total: {len(detection.detected_segments)}",
        f"- Lineas utiles: {len(detection.usable_segments)}",
        f"- Lineas horizontales filtradas: {detection.rejected_horizontal_segments}",
        f"- Fuente de guia: {detection.guidance_source}",
        f"- Error seleccionado: {detection.chosen_error:.2f} px",
        f"- ROI: {detection.roi_polygon.tolist()}",
        "",
        "## Archivos",
        "",
        "- `01_raw_camera.png`: imagen capturada por la camara a bordo",
        "- `02_grayscale.png`: conversion a escala de grises",
        "- `03_canny_edges.png`: bordes detectados con Canny",
        "- `04_roi_mask.png`: mascara creada con fillPoly",
        "- `05_roi_applied.png`: bordes luego de aplicar la ROI",
        "- `06_hough_lines.png`: lineas rectas detectadas por Hough sobre la imagen procesada",
    ]
    meta_path.write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")


def estimate_yellow_guidance_error(frame_bgr: np.ndarray, setpoint: float) -> tuple[float | None, int]:
    """Obtiene una referencia auxiliar con el centroide de pixeles amarillos.

    El sample original de Webots sigue la linea amarilla por color. Aqui lo
    usamos solo como respaldo para que el coche no se salga del camino antes de
    que la transformada de Hough produzca lineas utiles.
    """
    height, width = frame_bgr.shape[:2]

    # Se privilegia la mitad inferior ampliada para mantener la referencia
    # cercana al vehiculo pero sin perder la linea cuando aparece un poco mas
    # arriba en curvas o al inicio de la simulacion.
    search_region = frame_bgr[int(height * 0.35) :, :, :]
    diff = np.abs(search_region.astype(np.int16) - YELLOW_BGR_REFERENCE).sum(axis=2)
    yellow_mask = diff < YELLOW_DIFF_THRESHOLD

    ys, xs = np.nonzero(yellow_mask)
    yellow_pixels = int(xs.size)
    if yellow_pixels < YELLOW_MIN_PIXELS:
        return None, yellow_pixels

    # Se pondera por altura para dar mas peso a pixeles cercanos al vehiculo.
    weights = 1.0 + ys.astype(np.float32)
    x_mean = float(np.average(xs.astype(np.float32), weights=weights))
    error = x_mean - setpoint
    return error, yellow_pixels


def detect_lane_lines(frame_bgr: np.ndarray) -> DetectionResult:
    """Ejecuta el pipeline completo de deteccion de carriles.

    La salida principal es la lista de lineas detectadas por Hough y el error
    elegido para alimentar el PID. El error se define como la distancia entre
    el punto medio horizontal de una linea y el centro horizontal de la imagen.
    Se usa la linea con el error absoluto mas pequeno para seguir la marca
    amarilla mas cercana al centro de la camara.
    """
    height, width = frame_bgr.shape[:2]
    setpoint = width / 2.0

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)

    roi_polygon = build_roi_polygon(width, height)
    mask = np.zeros_like(edges)
    cv2.fillPoly(mask, roi_polygon, 255)
    masked_edges = cv2.bitwise_and(edges, mask)

    lines = cv2.HoughLinesP(
        masked_edges,
        rho=HOUGH_RHO,
        theta=HOUGH_THETA,
        threshold=HOUGH_THRESHOLD,
        minLineLength=HOUGH_MIN_LINE_LENGTH,
        maxLineGap=HOUGH_MAX_LINE_GAP,
    )

    processed_bgr = frame_bgr.copy()
    cv2.polylines(processed_bgr, roi_polygon, isClosed=True, color=(255, 0, 255), thickness=2)

    detected_segments: list[tuple[int, int, int, int]] = []
    usable_segments: list[tuple[int, int, int, int]] = []
    rejected_horizontal_segments = 0
    candidate_errors: list[float] = []
    yellow_hint_error, yellow_pixels = estimate_yellow_guidance_error(frame_bgr, setpoint)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = map(int, line[0])
            detected_segments.append((x1, y1, x2, y2))

            delta_x = x2 - x1
            delta_y = y2 - y1
            slope = math.inf if delta_x == 0 else delta_y / float(delta_x)

            # Se descartan lineas casi horizontales para no contaminar el error
            # del controlador con bordes de cruces peatonales o intersecciones.
            if abs(delta_y) < MIN_DELTA_Y or abs(slope) < MIN_ABS_SLOPE:
                rejected_horizontal_segments += 1
                cv2.line(processed_bgr, (x1, y1), (x2, y2), (0, 0, 255), 1)
                continue

            usable_segments.append((x1, y1, x2, y2))
            x_mid = (x1 + x2) / 2.0
            error = x_mid - setpoint
            candidate_errors.append(error)

            cv2.line(processed_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(processed_bgr, (int(x_mid), int((y1 + y2) / 2.0)), 4, (255, 255, 0), -1)

    if candidate_errors:
        # El error se obtiene de la linea util cuyo punto medio esta mas cerca
        # del centro horizontal de la imagen.
        chosen_error = min(candidate_errors, key=abs)
        guidance_source = "hough"
    elif yellow_hint_error is not None:
        # Si Hough todavia no entrega lineas estables, se usa la guia auxiliar
        # sobre la linea amarilla para permanecer dentro del camino y poder
        # re-adquirir lineas utiles despues.
        chosen_error = yellow_hint_error
        guidance_source = "yellow_hint"
    else:
        chosen_error = 0.0
        guidance_source = "none"

    cv2.line(
        processed_bgr,
        (int(setpoint), height),
        (int(setpoint), int(height * 0.55)),
        (255, 255, 255),
        2,
    )
    if yellow_hint_error is not None:
        yellow_x = int(clamp(setpoint + yellow_hint_error, 0, width - 1))
        cv2.circle(processed_bgr, (yellow_x, int(height * 0.82)), 5, (0, 255, 255), -1)

    # Texto compacto: escala 0.30 y espaciado de 10 px permiten que las 6 lineas
    # quepan dentro de los 64 px de alto de la camara (y max = 9 + 5*10 = 59 px).
    overlay_lines = [
        f"Hough total: {len(detected_segments)}",
        f"Utiles: {len(usable_segments)}",
        f"Filtradas: {rejected_horizontal_segments}",
        f"Px amarillos: {yellow_pixels}",
        f"Fuente: {guidance_source}",
        f"Error: {chosen_error:.2f}px",
    ]
    for index, text in enumerate(overlay_lines):
        cv2.putText(
            processed_bgr,
            text,
            (4, 9 + index * 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.30,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    processed_preview = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
    processed_bgr = cv2.addWeighted(processed_bgr, 0.70, processed_preview, 0.30, 0.0)

    return DetectionResult(
        processed_bgr=processed_bgr,
        gray=gray,
        edges=edges,
        roi_mask=mask,
        masked_edges=masked_edges,
        roi_polygon=roi_polygon,
        detected_segments=detected_segments,
        usable_segments=usable_segments,
        rejected_horizontal_segments=rejected_horizontal_segments,
        setpoint=setpoint,
        chosen_error=chosen_error,
        guidance_source=guidance_source,
        yellow_pixels=yellow_pixels,
    )


@dataclass
class PIDController:
    """PID discreto sencillo para convertir el error visual en direccion."""

    kp: float
    ki: float
    kd: float
    integral: float = 0.0
    previous_error: float = 0.0

    def update(self, error: float, dt: float) -> float:
        """Calcula el angulo de direccion a partir del error actual."""
        proportional = self.kp * error

        self.integral += error * dt
        self.integral = clamp(self.integral, -INTEGRAL_LIMIT, INTEGRAL_LIMIT)
        integral_term = self.ki * self.integral

        derivative = 0.0 if dt <= 0.0 else (error - self.previous_error) / dt
        derivative_term = self.kd * derivative

        self.previous_error = error
        return proportional + integral_term + derivative_term


def paste_image_to_display(display, image_bytes: bytes, width: int, height: int) -> None:
    """Pega una imagen en un display de Webots si el dispositivo existe."""
    if display is None:
        return
    image_ref = display.imageNew(image_bytes, Display.BGRA, width, height)
    display.imagePaste(image_ref, 0, 0, False)
    display.imageDelete(image_ref)


def main() -> None:
    """Bucle principal del controlador externo."""
    driver = Driver()
    basic_timestep = int(driver.getBasicTimeStep())
    dt = basic_timestep / 1000.0

    camera = try_get_device(driver, CAMERA_DEVICE_CANDIDATES)
    if camera is None:
        raise RuntimeError(
            "No se encontro una camara. Revisa CAMERA_DEVICE_CANDIDATES y el "
            "nombre real del dispositivo en el mundo de Webots."
        )

    camera.enable(basic_timestep)
    width = camera.getWidth()
    height = camera.getHeight()

    raw_display = try_get_device(driver, RAW_DISPLAY_CANDIDATES)
    processed_display = try_get_device(driver, PROCESSED_DISPLAY_CANDIDATES)

    # Dimensiones reales de cada display para escalar las imagenes exactamente.
    raw_disp_w = raw_display.getWidth() if raw_display else width
    raw_disp_h = raw_display.getHeight() if raw_display else height
    proc_disp_w = processed_display.getWidth() if processed_display else width
    proc_disp_h = processed_display.getHeight() if processed_display else height

    # Ganancias iniciales sugeridas en el plan. La idea es arrancar conservador
    # y afinar primero Kp, luego Kd y al final un Ki pequeno.
    pid = PIDController(kp=0.012, ki=0.0001, kd=0.006)

    driver.setCruisingSpeed(TARGET_SPEED_KMH)
    driver.setSteeringAngle(0.0)

    print("Controlador de la Actividad 2.1 iniciado.")
    print(f"Resolucion de camara: {width}x{height}")
    print(f"Displays encontrados: raw={raw_display is not None}, processed={processed_display is not None}")
    print(
        "Sintonizacion inicial PID -> "
        f"Kp={pid.kp}, Ki={pid.ki}, Kd={pid.kd}, velocidad={TARGET_SPEED_KMH} km/h"
    )
    print(f"Reporte automatico de validacion: {VALIDATION_REPORT_PATH}")

    step_counter = 0
    filtered_error = 0.0
    commanded_steering = 0.0
    last_guided_error = 0.0
    last_guided_steering = 0.0
    frames_since_guidance = GUIDANCE_MEMORY_FRAMES + 1
    validation_stats = ValidationStats()
    artifacts_exported = False
    while driver.step() != -1:
        camera_image = camera.getImage()
        frame_bgr = camera_bgra_to_bgr(camera_image, width, height)

        detection = detect_lane_lines(frame_bgr)

        if detection.guidance_source != "none":
            # Se suaviza el error visual para no reaccionar con exceso a
            # variaciones cuadro a cuadro de Hough o del respaldo amarillo.
            filtered_error = (
                ERROR_SMOOTHING_ALPHA * detection.chosen_error
                + (1.0 - ERROR_SMOOTHING_ALPHA) * filtered_error
            )
            control_error = filtered_error
            frames_since_guidance = 0
            applied_source = detection.guidance_source
            steering_target = pid.update(control_error, dt)
            last_guided_error = control_error
        elif frames_since_guidance <= GUIDANCE_MEMORY_FRAMES:
            # Cuando la linea desaparece por interseccion o ruido, no conviene
            # regresar de inmediato a "seguir recto". En su lugar se conserva
            # por algunos cuadros la trayectoria mas reciente para mantenerse
            # dentro del camino y dar tiempo a que reaparezca la marca amarilla.
            hold_factor = GUIDANCE_DECAY ** frames_since_guidance
            control_error = last_guided_error * hold_factor
            steering_target = last_guided_steering * (STEERING_HOLD_DECAY ** frames_since_guidance)
            frames_since_guidance += 1
            applied_source = "steering_hold"
        else:
            # Si ya paso demasiado tiempo sin observar la linea, se suelta el
            # volante muy poco a poco para no provocar una salida abrupta.
            control_error = 0.0
            steering_target = commanded_steering * STEERING_HOLD_DECAY
            pid.integral *= 0.95
            pid.previous_error = 0.0
            applied_source = "slow_release"

        steering_target = clamp(steering_target, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE)
        commanded_steering = limit_steering_step(steering_target, commanded_steering)
        steering_angle = commanded_steering
        if detection.guidance_source != "none":
            last_guided_steering = steering_angle

        validation_stats.observe(step_counter, detection, applied_source, control_error)

        if not artifacts_exported and (len(detection.usable_segments) > 0 or detection.guidance_source != "none"):
            export_pipeline_artifacts(frame_bgr, detection, step_counter)
            artifacts_exported = True

        driver.setCruisingSpeed(TARGET_SPEED_KMH)
        driver.setSteeringAngle(steering_angle)

        # Si existen dos displays, el primero muestra la imagen cruda y el
        # segundo la imagen procesada. Si solo existe uno, se prioriza la
        # imagen procesada porque es la evidencia mas util para la actividad.
        # Las imagenes se escalan al tamano exacto del display para que no
        # queden bordes negros ni contenido recortado.
        if raw_display is not None and processed_display is not None:
            raw_scaled = scale_to_display(frame_bgr, raw_disp_w, raw_disp_h)
            paste_image_to_display(raw_display, bgr_to_display_bytes(raw_scaled), raw_disp_w, raw_disp_h)
            proc_scaled = scale_to_display(detection.processed_bgr, proc_disp_w, proc_disp_h)
            paste_image_to_display(processed_display, bgr_to_display_bytes(proc_scaled), proc_disp_w, proc_disp_h)
        elif processed_display is not None:
            proc_scaled = scale_to_display(detection.processed_bgr, proc_disp_w, proc_disp_h)
            paste_image_to_display(processed_display, bgr_to_display_bytes(proc_scaled), proc_disp_w, proc_disp_h)
        elif raw_display is not None:
            raw_scaled = scale_to_display(frame_bgr, raw_disp_w, raw_disp_h)
            paste_image_to_display(raw_display, bgr_to_display_bytes(raw_scaled), raw_disp_w, raw_disp_h)

        if step_counter % DEBUG_EVERY_N_STEPS == 0:
            print(
                "frame="
                f"{step_counter} "
                f"hough_total={len(detection.detected_segments)} "
                f"lineas_utiles={len(detection.usable_segments)} "
                f"filtradas_horizontales={detection.rejected_horizontal_segments} "
                f"yellow_pixels={detection.yellow_pixels} "
                f"source={applied_source} "
                f"error={control_error:.2f} "
                f"steering={steering_angle:.4f}"
            )
        if step_counter % VALIDATION_WRITE_EVERY_N_STEPS == 0:
            write_validation_summary(validation_stats)

        step_counter += 1

    write_validation_summary(validation_stats)


if __name__ == "__main__":
    main()
