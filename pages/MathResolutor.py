import cv2
import numpy as np
import mediapipe as mp
import streamlit as st
from streamlit_cookies_manager import CookieManager
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from dotenv import load_dotenv
import os
from PIL import Image
import google.generativeai as genai
import time
import queue

load_dotenv()

cookies = CookieManager()
if not cookies.ready():
    st.stop()

session = cookies.get("session")
if not session: 
    st.switch_page("main.py")

# Configuración de MediaPipe para manos - reducir complejidad
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=0,  # Usar el modelo más ligero
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Configuración de Gemini
genai.configure(api_key=os.getenv('GEMINI_KEY'))
model = genai.GenerativeModel("gemini-2.0-flash")

# Variables de estado
if "canvas" not in st.session_state:
    st.session_state.canvas = None
if "response" not in st.session_state:
    st.session_state.response = ""
if "show_canvas" not in st.session_state:
    st.session_state.show_canvas = False
if "processing_ai" not in st.session_state:
    st.session_state.processing_ai = False

# IDs de las puntas de los dedos
tipsIDs = [4, 8, 12, 16, 20]

# Cola para comunicación entre hilos
frame_queue = queue.Queue(maxsize=1)
result_queue = queue.Queue()

# Estado compartido (minimizado)
shared_state = {
    "canvas": None,
    "temp_canvas": None,
    "prev_pos": None,
    "resolver": False,
    "respuesta": " ",
    "last_process_time": 0,
    "fps_limit": 30  # Limitar a 30 FPS para el procesamiento
}

def sendTo_AI(canvas):
    pil_image = Image.fromarray(canvas)
    response = model.generate_content(["Resuleve el problema matematico de la imagen en caso que la imagen no contenga un problema claro responde con el texto \"Revisa el problema\"", pil_image])
    st.session_state.response = response.text
    return response.text

def sendToAI(canvas):
    """Función para enviar la imagen a la IA en un hilo separado"""
    try:
        pil_image = Image.fromarray(canvas)
        response = model.generate_content(["Resuelve el problema matematico de la imagen en caso que la imagen no contenga un problema claro responde con el texto \"Revisa el problema\"", pil_image])
        result_queue.put(response.text)
    except Exception as e:
        result_queue.put(f"Error al procesar la imagen: {str(e)}")
    finally:
        st.session_state.processing_ai = False

def fingersUp(lm_list, hand_type, results):
    """Función optimizada para detectar dedos levantados"""
    if not results.multi_hand_landmarks:
        return []
        
    fingers = []
    # Tratamiento del pulgar
    if hand_type == "Right":
        fingers.append(1 if lm_list[tipsIDs[0]][0] > lm_list[tipsIDs[0] - 1][0] else 0)
    else:
        fingers.append(1 if lm_list[tipsIDs[0]][0] < lm_list[tipsIDs[0] - 1][0] else 0)
    
    # 4 dedos restantes
    for id in range(1, 5):
        fingers.append(1 if lm_list[tipsIDs[id]][1] < lm_list[tipsIDs[id] - 2][1] else 0)
    
    return fingers

def process_hands(image):
    """Procesa solo la detección de manos, optimizado"""
    # Control de velocidad de procesamiento
    current_time = time.time()
    if current_time - shared_state["last_process_time"] < 1.0/shared_state["fps_limit"]:
        return None, [], None
    
    shared_state["last_process_time"] = current_time
    
    # Preprocesamiento de imagen para MediaPipe
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_image)
    
    if not results.multi_hand_landmarks:
        return None, [], None
    
    # Extraer datos de la mano detectada
    hand_type = "Left" if results.multi_handedness[0].classification[0].label == "Right" else "Right"
    
    # Extraer landmarks y calcular dedos levantados
    h, w, _ = image.shape
    lm_list = []
    for lm in results.multi_hand_landmarks[0].landmark:
        cx, cy = int(lm.x * w), int(lm.y * h)
        lm_list.append([cx, cy])
    
    fingers = fingersUp(lm_list, hand_type, results)
    current_pos = lm_list[8]
    
    return results, fingers, current_pos

def video_frame_callback(frame):
    """Callback optimizado para procesamiento de frames"""
    img = frame.to_ndarray(format="bgr24")
    flipped_img = cv2.flip(img, 1)  # Voltear imagen una sola vez
    
    # Proceso principal de detección de manos (controlado por FPS)
    results, fingers, current_pos = process_hands(flipped_img)
    
    # Inicializar canvas si es necesario
    if shared_state["temp_canvas"] is None:
        shared_state["temp_canvas"] = np.zeros_like(flipped_img)
    
    # Procesar gestos solo si se detectaron manos
    if results is not None and fingers:
        # Dibujar con el dedo índice
        if fingers == [0, 1, 0, 0, 0]:
            if shared_state["prev_pos"] is None:
                shared_state["prev_pos"] = current_pos
            elif current_pos is not None and shared_state["prev_pos"] is not None:
                cv2.line(shared_state["temp_canvas"], 
                        current_pos, 
                        shared_state["prev_pos"], 
                        (255, 0, 255), 10)
            shared_state["prev_pos"] = current_pos
        else:
            shared_state["prev_pos"] = None
        
        # Borrar con el pulgar
        if fingers == [1, 0, 0, 0, 0]:
            shared_state["temp_canvas"] = np.zeros_like(flipped_img)
        
        # Guardar canvas con todos los dedos
        elif fingers == [1, 1, 1, 1, 1]:
            # Marcar para resolver y copiar canvas
            shared_state["canvas"] = shared_state["temp_canvas"].copy()
            shared_state["resolver"] = True
            
            # Poner el frame actual en la cola para procesar en el hilo principal
            try:
                # Non-blocking put - solo actualiza si la cola está vacía
                if frame_queue.empty():
                    frame_queue.put_nowait(True)
            except queue.Full:
                pass
    
    # Combinar imagen con canvas de manera más eficiente
    if np.any(shared_state["temp_canvas"]):
        # Solo mezclar si hay algo dibujado
        result = cv2.addWeighted(flipped_img, 1, shared_state["temp_canvas"], 1, 0)
    else:
        result = flipped_img
    
    # Opcional: Mostrar indicador de dedos detectados en la esquina
    if fingers:
        cv2.putText(result, f"Dedos: {fingers}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return frame.from_ndarray(result)

# Configuración para la webcam
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# UI layout
c1, _, c2 = st.columns([5,3,2])

with c1:
    st.title("Resolutor de problemas matemáticos")
with c2: 
    if st.button("Home", icon=":material/home:"):
        st.switch_page("pages/home.py")
st.write("Dibuja un problema matemático y levanta todos los dedos para resolverlo")

# Componente para mostrar la webcam
ctx = webrtc_streamer(
    key="WYH",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    video_frame_callback=video_frame_callback,
    async_processing=True,
)

# Layout para canvas y respuesta
col1, col2 = st.columns([3, 2])
with col1:
    canvas_placeholder = st.empty()
with col2:
    response_placeholder = st.empty()

# Bucle principal más eficiente
if ctx.state.playing:
    while True:
        try:
            # Verificar si hay nuevos frames para procesar (non-blocking)
            process_signal = frame_queue.get_nowait() if not frame_queue.empty() else None
            
            # Mostrar canvas actual
            if shared_state["temp_canvas"] is not None:
                canvas_placeholder.image(shared_state["temp_canvas"], 
                                        caption="Dibuja aquí", 
                                        channels="BGR")
            
            if shared_state["resolver"]:
                respuesta = sendTo_AI(shared_state["canvas"])
                st.session_state.response = respuesta
                response_placeholder.markdown(f"### Respuesta:\n{st.session_state.response}")
                shared_state["resolver"] = False
            # Pausar brevemente para no sobrecargar la UI
            time.sleep(0.1)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            break
else:
    st.info("Activa la cámara para comenzar")

# Mostrar la respuesta guardada si existe
if st.session_state.response:
    response_placeholder.markdown(f"### Respuesta:\n{st.session_state.response}")