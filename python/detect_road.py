from ultralytics import YOLO
import cv2
import paho.mqtt.client as mqtt
import time

# -------------------------------------
# CARGAR MODELO
# -------------------------------------
model = YOLO("yolov8s.pt")

# -------------------------------------
# CÁMARA
# -------------------------------------
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# -------------------------------------
# CLASES A DETECTAR: persona(0), auto(2)
# -------------------------------------
CLASSES_TARGET = [0, 2]

# -------------------------------------
# CONFIGURACIÓN MQTT
# -------------------------------------
MQTT_USER = "admin"
MQTT_PASSWORD = "gfu24ozu4t323aapj7b1pqb04yh4a66l"
MQTT_SERVER = "shinkansen.proxy.rlwy.net"
MQTT_PORT = 47186

# Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT")
        # Suscribirse a los tópicos del semáforo
        client.subscribe("trafficlight/state")
        client.subscribe("trafficlight/status")
    else:
        print(f"Error de conexión MQTT: {rc}")

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode()}")

# Configurar cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("Iniciando conexión MQTT...")
    time.sleep(2)  # Esperar conexión inicial
except Exception as e:
    print(f"Error conectando a MQTT: {e}")

# Estados por frame
person_detected = False
car_detected = False

# -------------------------------------
# LOOP PRINCIPAL
# -------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer la cámara.")
        break

    # Detección
    results = model(frame, conf=0.5, verbose=False)
    annotated = frame.copy()

    # Reiniciar detección por frame
    person_detected = False
    car_detected = False

    # Procesar detecciones
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            if cls not in CLASSES_TARGET:
                continue

            # Coordenadas
            x1, y1, x2, y2 = list(map(int, box.xyxy[0]))
            conf = float(box.conf[0])
            label = model.names[cls]

            # Dibujar caja
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"{label} {conf:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # Marcar detecciones
            if cls == 0:
                person_detected = True
            elif cls == 2:
                car_detected = True

    # -------------------------------------
    # LÓGICA DE CONTROL DEL SEMÁFORO
    # -------------------------------------
    if person_detected and not car_detected:
        # Solo personas -> semáforo en verde más tiempo
        mqtt_client.publish("trafficlight/config/set", '{"green_time": 12000}')
    elif car_detected and not person_detected:
        # Solo autos -> semáforo normal
        mqtt_client.publish("trafficlight/config/set", '{"green_time": 8000}')
    elif person_detected and car_detected:
        # Ambos detectados -> tiempo intermedio
        mqtt_client.publish("trafficlight/config/set", '{"green_time": 10000}')

    # Mostrar pantalla
    cv2.imshow("Detección de Personas y Autos", annotated)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
mqtt_client.loop_stop()
mqtt_client.disconnect()
cv2.destroyAllWindows()
