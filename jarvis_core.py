import os, threading, io, datetime, time, psutil, queue, re, sys
import torch, sounddevice as sd, speech_recognition as sr
import ollama
import argostranslate.package
import argostranslate.translate
from kokoro import KPipeline
from faster_whisper import WhisperModel
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --- MODULE IMPORTS ---
from comm_engine import CommEngine
from tactical_jarvis import TacticalAgent 
from vision_jarvis import VisionEngine
from autonomous_brain import AutonomousBrain

# ... (OfflineTranslator and ArcReactor classes remain unchanged as per your request) ...

class OfflineTranslator:
    def __init__(self, from_code="en", to_code="hi"):
        self.from_code = from_code
        self.to_code = to_code
        try:
            self.setup_translator()
        except Exception as e:
            print(f"Translator Setup Warning: {e}")

    def setup_translator(self):
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(
            filter(lambda x: x.from_code == self.from_code and x.to_code == self.to_code, available_packages)
        )
        argostranslate.package.install_from_path(package_to_install.download())

    def translate(self, text):
        try:
            return argostranslate.translate.translate(text, self.from_code, self.to_code)
        except:
            return "[Translation Error]"

class ArcReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.is_speaking = False
        self.rotation = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)

    def update_animation(self):
        self.rotation = (self.rotation + (12 if self.is_speaking else 3)) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        color = QColor(255, 50, 50) if self.is_speaking else QColor(0, 200, 255)
        painter.setPen(QPen(color, 4))
        painter.drawEllipse(center, 80, 80)
        painter.translate(center)
        painter.rotate(self.rotation)
        for _ in range(12):
            painter.rotate(30)
            painter.drawRect(65, -5, 12, 8)

class JarvisUI(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.translator = OfflineTranslator(to_code="hi") 
        self.initUI()
        self.core.ui_callback = self.update_reactor_state

    def initUI(self):
        self.setWindowTitle("JARVIS OS - TACTICAL V1.7")
        self.setFixedSize(950, 850)
        self.setStyleSheet("background-color: #050505; color: #00C8FF;")

        main_layout = QVBoxLayout()
        top_row = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.reactor = ArcReactor()
        left_panel.addWidget(self.reactor)

        self.dash_box = QGroupBox("SYSTEM DIAGNOSTICS")
        self.dash_box.setStyleSheet("color: #00FF96; border: 1px solid #004455; font-weight: bold;")
        dash_layout = QVBoxLayout()
        self.cpu_label = QLabel("CPU: 0%")
        self.bat_label = QLabel("BATTERY: --")
        self.status_label = QLabel("NEURAL LINK: STANDBY")
        for lbl in [self.cpu_label, self.bat_label, self.status_label]:
            lbl.setStyleSheet("font-family: Consolas; font-size: 13px; border: none;")
            dash_layout.addWidget(lbl)
        self.dash_box.setLayout(dash_layout)
        left_panel.addWidget(self.dash_box)
        top_row.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        self.eng_log = QTextEdit(); self.eng_log.setReadOnly(True)
        self.trans_log = QTextEdit(); self.trans_log.setReadOnly(True)
        self.eng_log.setStyleSheet("border: 1px solid #004455; background: #070707;")
        self.trans_log.setStyleSheet("border: 1px solid #00FF96; color: #00FF96; background: #070707;")
        
        right_panel.addWidget(QLabel("COMMUNICATION LOG (EN)"))
        right_panel.addWidget(self.eng_log)
        right_panel.addWidget(QLabel("OFFLINE TRANSLATION (HI)"))
        right_panel.addWidget(self.trans_log)
        top_row.addLayout(right_panel, 2)

        main_layout.addLayout(top_row)

        toolbar = QHBoxLayout()
        self.mic_btn = QPushButton("🎤 ACTIVATE MIC")
        self.mic_btn.setStyleSheet("background: #002233; border: 1px solid #00C8FF; padding: 10px;")
        self.mic_btn.clicked.connect(self.manual_mic_trigger)
        
        self.rag_btn = QPushButton("📁 UPLOAD KNOWLEDGE (RAG)")
        self.rag_btn.setStyleSheet("background: #002233; border: 1px solid #00FF96; padding: 10px; color: #00FF96;")
        self.rag_btn.clicked.connect(self.manual_rag_upload)

        toolbar.addWidget(self.mic_btn)
        toolbar.addWidget(self.rag_btn)
        main_layout.addLayout(toolbar)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Direct Command Entry...")
        self.input_field.returnPressed.connect(self.send_gui_command)
        main_layout.addWidget(self.input_field)

        container = QWidget(); container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.dash_timer = QTimer()
        self.dash_timer.timeout.connect(self.update_dashboard)
        self.dash_timer.start(2000)

    def update_dashboard(self):
        cpu = psutil.cpu_percent()
        bat = psutil.sensors_battery()
        self.cpu_label.setText(f"CPU: {cpu}%")
        if bat: self.bat_label.setText(f"BATTERY: {bat.percent}% {'(Charging)' if bat.power_plugged else ''}")

    def manual_mic_trigger(self):
        self.log_both("SYSTEM: Manual Microphone override engaged.")
        self.core.command_queue.put("force_listen")

    def manual_rag_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.txt)")
        if file_path:
            self.log_both(f"SYSTEM: Loading {os.path.basename(file_path)} into RAG Engine...")
            if hasattr(self.core, 'rag'):
                result = self.core.rag.process_and_add_file(file_path)
                self.log_both(f"RAG: {result}")
            else:
                self.log_both("SYSTEM ERROR: RAGEngine not initialized.")

    def send_gui_command(self):
        text = self.input_field.text().strip()
        if text:
            self.log_both(f"USER: {text}")
            self.core.command_queue.put(text)
            self.input_field.clear()

    @pyqtSlot(str)
    def log_both(self, text):
        timestamp = datetime.datetime.now().strftime('%H:%M')
        self.eng_log.append(f"[{timestamp}] {text}")
        translated = self.translator.translate(text)
        self.trans_log.append(f"[{timestamp}] {translated}")

    def update_reactor_state(self, speaking, scanning=False):
        self.reactor.is_speaking = speaking
        self.status_label.setText("NEURAL LINK: ACTIVE" if speaking else "NEURAL LINK: STANDBY")

# --- CORE INTEGRATION ---

# --- CORE INTEGRATION ---

class JarvisCore:
    def __init__(self):
        os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
        self.voice_pipeline = KPipeline(lang_code='a')
        self.stt_model = WhisperModel("distil-large-v3", device="cuda", compute_type="float32")
        self.command_queue = queue.Queue()
        self.ui_callback = None 

        self.comm = CommEngine()
        self.vision = VisionEngine()
        self.tactician = TacticalAgent()
        self.auto_pulse = AutonomousBrain(self.comm)
        
        # --- EMAIL STATE TRACKING ---
        self.email_state = "IDLE" 
        self.current_recipient = None
        self.current_subject = None
        self.last_unknown_email = None # Tracks new emails for database storage

    def speak(self, text):
        QMetaObject.invokeMethod(window, "log_both", Qt.QueuedConnection, Q_ARG(str, f"JARVIS: {text}"))
        def run_tts():
            if self.ui_callback: self.ui_callback(True)
            generator = self.voice_pipeline(text, voice='af_nicole', speed=1)
            for _, _, audio in generator:
                sd.play(audio, 24000); sd.wait()
            if self.ui_callback: self.ui_callback(False)
        threading.Thread(target=run_tts, daemon=True).start()

    def voice_listener(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            while True:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=7)
                    wav_data = io.BytesIO(audio.get_wav_data())
                    segments, _ = self.stt_model.transcribe(wav_data)
                    text = "".join([s.text for s in segments]).strip()
                    if text: self.command_queue.put(text)
                except: continue

    def process_command(self, query):
        query = query.lower().strip()

        # --- GLOBAL CANCEL LOGIC ---
        if query in ["cancel", "abort", "stop"]:
            if self.email_state != "IDLE":
                self.email_state = "IDLE"
                self.current_recipient = None
                self.last_unknown_email = None
                self.speak("Email operations aborted, Sir.")
                return

        # --- NEW CONTACT STORAGE LOGIC ---
        if self.email_state == "WAITING_FOR_NAME_TO_STORE":
            new_name = query.strip()
            # Ensure your CommEngine has a save_contact(name, email) method
            self.comm.save_contact(new_name, self.last_unknown_email)
            self.speak(f"Database updated. {new_name} is now linked to {self.last_unknown_email}, Sir.")
            self.email_state = "IDLE"
            self.last_unknown_email = None
            return

        # --- EMAIL STATE MACHINE ---
        if self.email_state == "WAITING_FOR_SUBJECT":
            self.current_subject = query
            self.email_state = "WAITING_FOR_BODY"
            self.speak(f"Subject set. What are the message hints, Sir?")
            return

        if self.email_state == "WAITING_FOR_BODY":
            self.speak("Developing professional draft and transmitting...")
            result = self.comm.send_email(
                self.current_recipient['email'], 
                self.current_recipient['name'], 
                self.current_subject, 
                query 
            )
            self.speak(result)
            
            # Post-Transmission Learning: If it was a direct email, ask to save it
            if self.current_recipient['name'] == "Direct Recipient":
                self.last_unknown_email = self.current_recipient['email']
                self.email_state = "WAITING_FOR_NAME_TO_STORE"
                self.speak("This address is not in our records. Who is the owner of this contact, Sir?")
            else:
                self.email_state = "IDLE"
            
            self.current_recipient = None
            self.current_subject = None
            return

        # --- EMAIL INITIATION (DIRECT OR DATABASE) ---
        if "email" in query or "send" in query:
            target = query.replace("send email to", "").replace("email", "").replace("send", "").strip()
            
            # Logic: If query contains '@', treat as direct email
            if "@" in target:
                self.current_recipient = {'name': 'Direct Recipient', 'email': target}
                self.email_state = "WAITING_FOR_SUBJECT"
                self.speak(f"Direct uplink established to {target}. Please state the subject.")
            else:
                contact = self.comm.get_contact_by_name(target)
                if contact:
                    self.current_recipient = contact
                    self.email_state = "WAITING_FOR_SUBJECT"
                    self.speak(f"Opening channel to {contact['name']}. Please state the subject.")
                else:
                    self.speak(f"Contact '{target}' not found. Please provide a direct email address or update the registry.")

        # --- STANDARD SYSTEMS ---
        elif any(x in query for x in ["look", "see", "scan"]):
            self.speak(self.vision.capture_and_analyze(query))
        
        elif "evaluate" in query or "analyze" in query:
            self.speak(self.tactician.evaluate_idea(query))

        else:
            messages = [
                {'role': 'system', 'content': "You are JARVIS, a tactical AI for Rohith. Concise, professional, loyal."},
                {'role': 'user', 'content': query}
            ]
            try:
                res = ollama.chat(model='qwen2.5:7b', messages=messages)
                self.speak(res['message']['content'])
            except:
                self.speak("Neural link failure.")

    def run_logic(self):
        threading.Thread(target=self.auto_pulse.monitor_environment, args=(self,), daemon=True).start()
        threading.Thread(target=self.voice_listener, daemon=True).start()
        self.speak("Dashboard active. Tactical systems ready, Sir.")
        while True:
            query = self.command_queue.get()
            self.process_command(query)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    jarvis_core = JarvisCore()
    window = JarvisUI(jarvis_core)
    window.show()
    threading.Thread(target=jarvis_core.run_logic, daemon=True).start()
    sys.exit(app.exec_())