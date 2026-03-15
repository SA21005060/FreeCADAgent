import textwrap
import re
import FreeCADGui
from PySide2 import QtWidgets, QtCore
import subprocess
import os
import base64
from openai import OpenAI  # , AzureOpenAI
import ast
import json
import requests
import threading
import time
import datetime

# from llm_client2 import llm_client

from src.llm_client import prompt_llm
from pathlib import Path
from src.styles import apply_stylesheet


GEN_SCRIPT = Path("generated/result_script.py")
RUN_SCRIPT = Path("src/run_freecad.py")
LOG_FILE = Path("generated/last_run_log.txt")
BASE_INSTRUCTION = Path("prompts/base_instruction.txt")

GUI_SNIPPET = """
import FreeCADGui
FreeCADGui.activeDocument().activeView().viewAxometric()
FreeCADGui.SendMsgToActiveView("ViewFit")
"""

screenshot_code = """
import FreeCADGui
import time
time.sleep(5)  # allow GUI to load
view = FreeCADGui.ActiveDocument.ActiveView

print("📸 Successfully ran FreeCAD script")
"""

MAX_RETRIES = 3  # Maximum auto-fix attempts
# from sentence_transformers import SentenceTransformer, util
# from dotenv import load_dotenv

# 加载环境变量
# 首先尝试加载当前目录的.env
# load_dotenv()


# Project root = folder containing this file (e.g., MyWorkbench/)
project_root = os.path.dirname(os.path.abspath(__file__))

# Use that as base_dir
base_dir = project_root

# Define subpaths
log_dir = os.path.join(base_dir, "logs")
cache_file = os.path.join(base_dir, "confirmed_macros.jsonl")
rejected_file = os.path.join(base_dir, "rejected_macros.jsonl")

# Make sure logs folder exists
os.makedirs(log_dir, exist_ok=True)

# Set environment variable to prevent tokenizers from using multiple threads
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class CADAssistantPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.embedding_model = None
        self.embedding_model_ready = False

        # self.api_key = None
        # self.base_url = None

        # Start model loading in background
        # threading.Thread(target=self.load_embedding_model, daemon=True).start()

        # Skip cache flag
        self.skip_cache = True  # False

        # Ensure Whisper server is running
        self.ensure_whisper_server()

        # Load model configs
        config_path = os.path.join(base_dir, "model_configs.json")
        try:
            with open(config_path, "r") as f:
                self.model_configs = json.load(f)
        except Exception as e:
            self.model_configs = {}
            QtWidgets.QMessageBox.critical(
                self, "Config Error", f"Failed to load model config:\n{str(e)}"
            )

        self.setWindowTitle("FreeCADAgent AI Assistant")
        self.previous_code = None  # Store previous macro text
        self.last_successful_model = None  # Cache for last working model
        self.timestamp = datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )  # Timestamp for log files

        # Layout
        layout = QtWidgets.QVBoxLayout()

        self.prompt_input = QtWidgets.QTextEdit()
        self.prompt_input.setPlaceholderText(
            "Describe your CAD task here (e.g., 'create a cube with side 10mm')"
        )
        layout.addWidget(QtWidgets.QLabel("Prompt:"))
        layout.addWidget(self.prompt_input)

        # Buttons rows
        # Row 1: Send, Reset, Speak, Image
        button_row_1 = QtWidgets.QHBoxLayout()

        self.submit_button = QtWidgets.QPushButton("🚀 Send")
        self.submit_button.clicked.connect(self.on_submit)
        button_row_1.addWidget(self.submit_button)

        self.reset_model_button = QtWidgets.QPushButton("🔄 Reset")
        self.reset_model_button.clicked.connect(self.on_reset_model)
        button_row_1.addWidget(self.reset_model_button)

        self.record_button = QtWidgets.QPushButton("🎙 Speak")
        self.record_button.clicked.connect(self.record_and_transcribe)
        button_row_1.addWidget(self.record_button)

        self.load_prompt_button = QtWidgets.QPushButton("📄 Text")
        self.load_prompt_button.clicked.connect(self.load_prompt_from_file)
        button_row_1.addWidget(self.load_prompt_button)

        self.image_button = QtWidgets.QPushButton("🖼 Image")
        self.image_button.clicked.connect(self.select_image_file)
        button_row_1.addWidget(self.image_button)

        self.image_path = None  # Store selected image path

        layout.addLayout(button_row_1)

        # # Row 2: Good, Poor
        # button_row_2 = QtWidgets.QHBoxLayout()

        # self.confirm_button = QtWidgets.QPushButton("👍 Good")
        # self.confirm_button.clicked.connect(self.confirm_macro_as_good)
        # self.confirm_button.setEnabled(False)  # Only enable after a successful macro
        # button_row_2.addWidget(self.confirm_button)

        # self.reject_button = QtWidgets.QPushButton("👎 Poor")
        # self.reject_button.clicked.connect(self.reject_cached_macro)
        # self.reject_button.setEnabled(False)
        # button_row_2.addWidget(self.reject_button)

        # layout.addLayout(button_row_2)

        # Model selection dropdown
        self.model_selector = QtWidgets.QComboBox()
        self.model_selector.addItems(
            [
                "MiniMax-M2.5",
                "qwen3.5",
                "lfm2.5-thinking",
                "GPT-4.1",
                "GPT-4o",
            ]
        )
        self.model_selector.setCurrentIndex(0)  # Default to first option

        model_layout = QtWidgets.QHBoxLayout()
        model_layout.addWidget(QtWidgets.QLabel("LLM:"))
        model_layout.addWidget(self.model_selector)
        layout.addLayout(model_layout)

        self.url_selector = QtWidgets.QComboBox()
        self.url_selector.addItems(
            [
                "https://api.minimaxi.com/v1",
                "http://localhost:11434/v1",
            ]
        )
        self.url_selector.setCurrentIndex(0)  # Default to first option

        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(QtWidgets.QLabel("URL:"))
        url_layout.addWidget(self.url_selector)
        layout.addLayout(url_layout)

        # self.api_key_input = QtWidgets.QTextEdit()
        # self.api_key_input.setPlaceholderText("LLM API Key (e.g., 'sk-...)')")
        # self.api_key_input.setMinimumHeight(10)
        # layout.addWidget(QtWidgets.QLabel("LLM API Key:"))
        # layout.addWidget(self.api_key_input)

        # Output box
        self.response_output = QtWidgets.QTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setMinimumHeight(1000)
        layout.addWidget(QtWidgets.QLabel("Response:"))
        layout.addWidget(self.response_output)

        # # Manual macro input area
        # manual_layout = QtWidgets.QHBoxLayout()

        # # Manual code editor (left side)
        # self.manual_input_box = QtWidgets.QTextEdit()
        # self.manual_input_box.setPlaceholderText("Paste the macro here and click ▶️ Run")
        # manual_layout.addWidget(self.manual_input_box, 2)

        # # Buttons layout (right side, vertical)
        # manual_button_column = QtWidgets.QVBoxLayout()

        # self.run_manual_button = QtWidgets.QPushButton("▶ Run")
        # self.run_manual_button.clicked.connect(self.run_manual_macro)
        # manual_button_column.addWidget(self.run_manual_button)

        # self.clean_manual_button = QtWidgets.QPushButton("🧹 Clean")
        # self.clean_manual_button.clicked.connect(self.clean_manual_input)
        # manual_button_column.addWidget(self.clean_manual_button)

        # self.save_macro_button = QtWidgets.QPushButton("💾 Save")
        # self.save_macro_button.clicked.connect(self.save_manual_macro)
        # manual_button_column.addWidget(self.save_macro_button)

        # manual_layout.addLayout(manual_button_column, 0)

        # layout.addWidget(QtWidgets.QLabel("Manual Macro Execution:"))
        # layout.addLayout(manual_layout)

        self.setLayout(layout)

        # Apply QSS styling
        apply_stylesheet(self)

    def run_manual_macro(self):
        code = self.manual_input_box.toPlainText().strip()
        if not code:
            self.response_output.setPlainText("❌ No code to execute.")
            return
        try:
            ast.parse(code)
            exec(code, globals())
            self.previous_code = code
            self.response_output.setPlainText("✅ Manual macro executed successfully.")
        except Exception as e:
            self.response_output.setPlainText(f"❌ Error in manual macro:\n\n{str(e)}")

    def clean_manual_input(self):
        self.manual_input_box.clear()

    def save_manual_macro(self):
        code = self.manual_input_box.toPlainText().strip()
        if not code:
            self.response_output.setPlainText("❌ No code to save.")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Macro As",
            os.path.expanduser("~/macro.FCMacro"),
            "FreeCAD Macro (*.FCMacro)",
        )
        if save_path:
            try:
                with open(save_path, "w") as f:
                    f.write(code)
                self.response_output.setPlainText(f"✅ Macro saved to:\n{save_path}")
            except Exception as e:
                self.response_output.setPlainText(f"❌ Failed to save macro:\n{str(e)}")

    def select_image_file(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.image_path = file_path
            self.response_output.setPlainText(f"🖼 Image selected: {file_path}")

    def ensure_whisper_server(self):
        try:
            # Try connecting to server
            response = requests.get("http://127.0.0.1:5005/docs", timeout=2)
            if response.status_code == 200:
                print("✅ Whisper server is running.")
                return  # Server is up

        except Exception:
            print("⚠️ Whisper server not detected. Starting...")

        def launch_server():
            server_script = os.path.join(base_dir, "whisper_server.py")
            log_path = os.path.join(log_dir, "whisper_server.log")

            env = os.environ.copy()
            env.pop("PYTHONHOME", None)  # prevent FreeCAD from polluting venv Python

            import shutil

            python_exec = shutil.which("python3") or "/usr/bin/python3"
            print(f"🔧 Launching Whisper server with interpreter: {python_exec}")

            with open(log_path, "w") as log_file:
                subprocess.Popen(
                    [python_exec, server_script],
                    stdout=log_file,
                    stderr=log_file,
                    env=env,
                )
            print(f"🔧 Whisper server started with: {python_exec}")

        threading.Thread(target=launch_server, daemon=True).start()

        print("🚀 Whisper server launched.")

    def load_embedding_model(self):
        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.embedding_model_ready = True
            print("✅ Embedding model loaded in background.")
        except Exception as e:
            self.response_output.append(f"❌ Failed to load embedding model:\n{str(e)}")

    def record_and_transcribe(self):
        # Show immediate UI feedback
        self.response_output.setPlainText("🎙 Recording...")
        self.response_output.repaint()
        QtCore.QCoreApplication.processEvents()

        # (1) Transcription (Whisper HTTP)
        try:
            response = requests.post(
                "http://127.0.0.1:5005/record_and_transcribe",
                json={"duration": 5, "samplerate": 16000, "channels": 1},
                timeout=30,  # a little more generous on first warm-up
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(data["error"])

            text = (data.get("text") or "").strip()
            if not text:
                raise RuntimeError("Received empty transcription.")

            self.prompt_input.setPlainText(text)
            self.response_output.setPlainText(
                "✅ Transcription complete. Submitting to LLM..."
            )

        except Exception as e:
            # Only errors from the STT/HTTP path land here
            self.response_output.setPlainText(
                f"❌ Failed to get transcription from server:\n\n{e}"
            )
            return  # stop; don't try to submit to LLM

        # (2) LLM + macro execution
        try:
            self.on_submit()
        except Exception as e:
            # If on_submit raises, report it accurately
            self.response_output.setPlainText(
                f"❌ Submission/macro step failed:\n\n{e}"
            )

    def on_reset_model(self):
        self.last_successful_model = None
        self.previous_code = None
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clear uploaded image
        self.image_path = None

        # Clear prompt input
        self.prompt_input.clear()

        # Show message that image was cleared
        self.response_output.setPlainText(
            "✅ Model, code history, and uploaded image reset."
        )

        # Disable confirm/reject buttons
        self.confirm_button.setEnabled(False)
        self.reject_button.setEnabled(False)

    def format_selection_info(self, selection):
        if not selection:
            return "No selection"

        lines = []
        for sel in selection:
            lines.append(f"Object: {sel.ObjectName}")
            for i, sub in enumerate(sel.SubObjects):
                name = sel.SubElementNames[i]
                geom_type = (
                    type(sub).__name__.replace("TopoShape", "").replace("Part::", "")
                )
                lines.append(f"Selected {geom_type}: {name}")

                # Add click (pick) location if available
                if i < len(sel.PickedPoints):
                    pick = sel.PickedPoints[i]
                    lines.append(
                        f"Clicked at: ({pick.x:.5f}, {pick.y:.5f}, {pick.z:.5f})"
                    )
        return "\n".join(lines)

    def load_prompt_from_file(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Text Files (*.txt)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.prompt_input.setPlainText(content)
                    self.response_output.setPlainText(
                        f"📄 Loaded prompt from: {file_path}"
                    )
            except Exception as e:
                self.response_output.setPlainText(
                    f"❌ Failed to load prompt file:\n{str(e)}"
                )

    def on_submit(self):
        error_text = ""
        timestamp = self.timestamp  # Use the timestamp from initialization
        start_time = time.time()  # Start timing

        prompt = self.prompt_input.toPlainText().strip()
        is_help_query = prompt.lower().startswith("help")

        selection = FreeCADGui.Selection.getSelectionEx()
        if selection:
            selected_text = self.format_selection_info(selection)
        else:
            selected_text = "No selection"

        self.last_selection_text = selected_text  # cache for later use

        model_name = self.model_selector.currentText()

        timeout = 1200

        api_key = "sk-cp-3QJ9WJkW-mL7wsYUrGn1KP_6GcVWnT1Vup7asuCdhlsmKf9bFL2AVV64YmQ5ixWQq0-duQ3fps6MOlGU1Em1wZNwwycQ_DBnuXDJRES0mbRGQBP5SNSVkK8" # self.api_key_input.toPlainText().strip()

        base_url = self.url_selector.currentText()

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

        if self.previous_code and not is_help_query:
            system_msg = (
                "You are a CAD assistant. Modify the given FreeCAD Python macro according to the user's instructions and/or the provided image. "
                "The user's selection may also include 3D coordinates from a click; use them to position geometry accurately on the selected vertex, edge, face, or body. "
                "Ensure the final code includes code to fit the view and set the isometric view to the part."
            )

            user_msg = (
                "**Here is the original FreeCAD macro**:\n\n"
                f"```\n{self.previous_code}\n```\n\n"
                "**Modify it according to this instruction**:\n"
                f"{prompt}\n\n"
                "**IMPORTANT: The following object(s) were selected, including pick locations**:\n"
                f"{selected_text}\n\n"
                "**Use the clicked coordinates to determine placement and orientation when appropriate.**\n"
            )
            try:
                # Save the user message (the prompt sent to LLM)
                with open(
                    os.path.join(
                        log_dir, f"{timestamp}_follow_up_user_msg_to_{model_name}.txt"
                    ),
                    "w",
                ) as f:
                    f.write(user_msg)
            except Exception as save_followup_user_msg_ex:
                self.response_output.setPlainText(
                    f"❌ Failed to save logs:\n\n{str(save_followup_user_msg_ex)}"
                )
                return

        else:
            system_msg = (
                "You are a CAD assistant. Generate a complete FreeCAD Python macro according to the user's instructions and/or the provided image. "
                "Ensure the final code includes code to fit the view and set the isometric view to the part."
            )
            user_msg = prompt

            try:
                # Save user prompt
                with open(
                    os.path.join(
                        log_dir, f"{timestamp}_init_user_msg_to_{model_name}.txt"
                    ),
                    "w",
                ) as f:
                    f.write(user_msg)
            except Exception as save_init_user_msg_ex:
                self.response_output.append(
                    f"❌ Failed to save logs:\n{str(save_init_user_msg_ex)}"
                )

        # Prepare image input
        image_input = None
        if self.image_path:
            try:
                with open(self.image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")
                # Infer mime type by file extension (safe default)
                mime_type = (
                    "image/png"
                    if self.image_path.lower().endswith(".png")
                    else "image/jpeg"
                )
                image_input = {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                }
            except Exception as read_image_ex:
                self.response_output.setPlainText(
                    f"❌ Failed to read image: {str(read_image_ex)}"
                )
                return

        preview_message = f"🛰 Sending to {model_name}...\n\n--- System Prompt ---\n{system_msg}\n\n--- User Prompt ---\n{user_msg}"
        self.response_output.setPlainText(preview_message)
        QtCore.QCoreApplication.processEvents()

        raw_message = None  # Safe default

        try:
            messages = [{"role": "system", "content": system_msg}]
            if image_input:
                messages.append(
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_msg}, image_input],
                    }
                )
            else:
                messages.append({"role": "user", "content": user_msg})

            # Use streaming for real-time output
            accumulated_content = ""
            streaming_message = f"🛰 Sending to {model_name}...\n\n"
            self.response_output.setPlainText(streaming_message)
            QtCore.QCoreApplication.processEvents()

            try:
                with open(
                    os.path.join(
                        log_dir, f"{timestamp}_system_msg_to_{model_name}.txt"
                    ),
                    "w",
                ) as f:
                    f.write(system_msg)
            except Exception as save_sysmsg_ex:
                self.response_output.append(
                    f"❌ Failed to save system message log:\n{str(save_sysmsg_ex)}"
                )

            # Stream the response in real-time
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_completion_tokens=4096,
                temperature=0.0,
                seed=42,
                stream=True,  # Enable streaming
            )

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    content_chunk = delta.content
                    accumulated_content += content_chunk
                    # Update output in real-time
                    current_text = self.response_output.toPlainText()
                    # Keep the header, append new content
                    if not current_text.endswith(content_chunk):
                        self.response_output.setPlainText(current_text + content_chunk)
                        QtCore.QCoreApplication.processEvents()

            raw_message = accumulated_content
            print(f"✅ {model_name} succeeded:\n\n{raw_message}")

            if is_help_query:
                self.response_output.setPlainText(
                    f"💡 Help from {model_name}:\n\n{raw_message}"
                )
                return

            # Extract Python code block
            matches = re.findall(r"```(?:python)?\s*(.*?)```", raw_message, re.DOTALL)
            if matches:
                clean_code = textwrap.dedent(max(matches, key=len)).strip()
            else:
                clean_code = textwrap.dedent(raw_message).strip()

            # Attempt to parse and run
            ast.parse(clean_code)
            exec(clean_code, globals())

            model_used = response.model or "Unknown model"
            self.last_successful_model = model_used
            self.previous_code = clean_code

            # Add completion time to response
            end_time = time.time()
            duration_sec = end_time - start_time
            self.response_output.setPlainText(
                f"✅ {model_used} succeeded (completed in {duration_sec:.2f} seconds):\n\n{clean_code}"
            )

            self.confirm_button.setEnabled(
                True
            )  # Enable confirm after successful macro
            self.reject_button.setEnabled(True)  # Enable reject after successful macro

            try:
                with open(
                    os.path.join(
                        log_dir, f"{timestamp}_init_msg_from_{model_name}.txt"
                    ),
                    "w",
                ) as f:
                    f.write(clean_code)
            except Exception as save_llm_resp_ex:
                error_text += (
                    f"❌ Failed to save LLM response:\n\n{str(save_llm_resp_ex)}"
                )

        except Exception as outer_ex:
            outer_err_str = str(outer_ex)  # capture immediately
            error_text = f"❌ {model_name} failed to produce an executable macro.\n\n"

            if raw_message:
                error_text += (
                    "**Here is the full response:**\n\n" + raw_message + "\n\n"
                )

                try:
                    with open(
                        os.path.join(
                            log_dir, f"{timestamp}_follow_up_msg_from_{model_name}.txt"
                        ),
                        "w",
                    ) as f:
                        f.write(raw_message)
                except Exception as save_followup_resp_ex:
                    error_text += f"❌ Failed to save LLM response:\n\n{str(save_followup_resp_ex)}"

            error_text += f"Error:\n{outer_err_str}"
            self.response_output.setPlainText(error_text)

            # Self-refinement pass
            self.refine_with_error(
                client=client,
                failed_code=clean_code
                if "clean_code" in locals()
                else "<no code extracted>",
                error_msg=outer_err_str,
                prompt=prompt,
                selected_text=selected_text,
                model_name=model_name,
                system_msg_base=system_msg,
                api_key=api_key,
                base_url=base_url,
                timestamp=timestamp,
                start_time=start_time,
            )

    def is_semantically_similar(self, a, b, threshold=0.8):
        a_norm, b_norm = a.strip(), b.strip()
        if a_norm == b_norm:
            return True  # exact match shortcut

        if not self.embedding_model_ready:
            self.response_output.append(
                "⚠️ Embedding model is still loading. Please try again shortly."
            )
            return False

        embeddings = self.embedding_model.encode(
            [a_norm, b_norm], convert_to_tensor=True
        )
        cosine_sim = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
        return cosine_sim >= threshold

    def try_load_cached_macro(self, prompt, selection_text):
        try:
            with open(cache_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        prompt_match = self.is_semantically_similar(
                            entry["prompt"], prompt, threshold=0.95
                        )
                        selection_match = self.is_semantically_similar(
                            entry["selection"], selection_text, threshold=0.95
                        )

                        if prompt_match and selection_match:
                            return entry
                    except Exception as inner_e:
                        self.response_output.append(
                            f"⚠️ Skipped corrupted cache entry: {str(inner_e)}"
                        )

        except Exception as e:
            self.response_output.append(f"⚠️ Failed to read cache: {str(e)}")

        return None

    def complexCAD(self, user_input, model_name, api_key, base_url):
        # user_input = input("Describe your FreeCAD part: ")

        # Read base instructions
        self.response_output.append(f" Complex Attempt begin...\n")
        self.response_output.setPlainText("🤖 Attempting auto refinement...\n")
        QtCore.QCoreApplication.processEvents()

        start_time = time.time()
        base_instruction = BASE_INSTRUCTION.read_text().strip()
        full_prompt = (
            f"{base_instruction}\n\nUser instruction: {user_input}"
            + "\n\n**Output Format Guidelines**: The final generated FreeCAD Python macro must be between ```python and ```"
        )

        # Initial LLM generation
        generated_code = prompt_llm(full_prompt, model_name, api_key, base_url)

        matches = re.findall(r"```(?:python)?\s*(.*?)```", generated_code, re.DOTALL)
        if matches:
            generated_code = textwrap.dedent(max(matches, key=len)).strip()
        else:
            generated_code = textwrap.dedent(generated_code).strip()

        # Append GUI snippet
        generated_code += "\n\n" + GUI_SNIPPET + screenshot_code

        ast.parse(generated_code)
        exec(generated_code, globals())
        self.previous_code = generated_code
        duration_sec = time.time() - start_time if start_time else -1
        self.response_output.setPlainText(
            f"✅ Refinement succeeded  (completed in {duration_sec:.2f} seconds):\n\n{generated_code}"
        )
        self.confirm_button.setEnabled(True)  # Allow user to confirm refined macro
        self.reject_button.setEnabled(
            True
        )  # Allow user to reject even refined macro if needed

        # Save initial script
        GEN_SCRIPT.write_text(generated_code)
        self.response_output.append(f"\n     Initial code written to {GEN_SCRIPT}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                start_time = time.time()
                self.response_output.append(f"\n▶ Attempt {attempt} running FreeCAD...")
                # success = run_freecad_script()
                # Attempt to parse and run

                # Read captured FreeCAD logs
                error_logs = (
                    LOG_FILE.read_text() if LOG_FILE.exists() else "No log found."
                )

                # Prepare prompt for LLM to fix the code
                fix_prompt = (
                    f"""
        I want to make the following part using FreeCAD 1.0.1 python scripting

        {user_input}

        The following FreeCAD script was created but it failed during execution:

        {generated_code}

        Here is the error log:
        {error_logs}

        Please provide a corrected FreeCAD script. Keep the logic same, just correct the given error. Respond with valid FreeCAD 1.0.1 Python code only, no extra comments.
        """
                    + "\n\n**Output Format Guidelines**: The final generated FreeCAD Python macro must be between ```python and ```"
                )
                # Get fixed code from LLM
                generated_code = prompt_llm(fix_prompt)

                # Clean code fences if present
                matches = re.findall(
                    r"```(?:python)?\s*(.*?)```", generated_code, re.DOTALL
                )
                if matches:
                    generated_code = textwrap.dedent(max(matches, key=len)).strip()
                else:
                    generated_code = textwrap.dedent(generated_code).strip()

                # Save fixed code for next attempt
                generated_code = generated_code + "\n\n" + GUI_SNIPPET

                ast.parse(generated_code)
                exec(generated_code, globals())
                self.previous_code = generated_code
                duration_sec = time.time() - start_time if start_time else -1
                self.response_output.setPlainText(
                    f"✅ Refinement succeeded at attempt {attempt} (completed in {duration_sec:.2f} seconds):\n\n{generated_code}"
                )
                self.confirm_button.setEnabled(
                    True
                )  # Allow user to confirm refined macro
                self.reject_button.setEnabled(
                    True
                )  # Allow user to reject even refined macro if needed

                GEN_SCRIPT.write_text(generated_code)
                self.response_output.append(
                    f"     Fixed code written to {GEN_SCRIPT}. successfully..."
                )
                return

                # else:
                #     print(f"❌ Max retries ({MAX_RETRIES}) reached. Check {LOG_FILE} for details.")
                #     return False

                # Success! Exit the loop immediately
            except Exception as e2:
                error_msg = str(e2)
                # failed_code = generated_code if 'clean_code' in locals() else "<no code extracted>"
                self.response_output.append(
                    f"⚠️ Complex Attempt {attempt} failed. Retrying...\n"
                )
                QtCore.QCoreApplication.processEvents()

                attempt += 1  # Next retry

    def refine_with_error(
        self,
        client,
        failed_code,
        error_msg,
        prompt,
        selected_text,
        model_name,
        system_msg_base,
        api_key,
        base_url,
        max_attempts=3,
        timestamp=None,
        start_time=None,
    ):
        attempt = 1
        last_raw_message = None

        self.response_output.setPlainText("🤖 Attempting auto refinement...\n")
        QtCore.QCoreApplication.processEvents()

        while attempt <= max_attempts:
            try:
                refine_system_msg = system_msg_base + (
                    "\nYou previously generated the following macro, which failed with an error. "
                    "Please fix it accordingly. Ensure the result is valid Python and executable in FreeCAD."
                )
                refine_user_msg = (
                    f"**Attempt {attempt}**:\n\n"
                    "**The following macro failed**:\n"
                    f"```\n{failed_code}\n```\n\n"
                    f"**Error Message**:\n{error_msg}\n\n"
                    "**User's instruction was**:\n"
                    f"{prompt}\n\n"
                    "**Selection Info**:\n"
                    f"{selected_text}"
                )

                messages = [{"role": "system", "content": refine_system_msg}]
                messages.append({"role": "user", "content": refine_user_msg})

                # Save the refinement input
                try:
                    refine_log_path = os.path.join(
                        log_dir,
                        f"{timestamp}_refine_attempt_{attempt}_to_{model_name}.txt",
                    )
                    with open(refine_log_path, "w") as f:
                        f.write("--- System Message ---\n")
                        f.write(refine_system_msg + "\n\n")
                        f.write("--- User Message ---\n")
                        f.write(refine_user_msg)
                except Exception as e:
                    self.response_output.append(
                        f"❌ Failed to save refinement input for attempt {attempt}:\n{str(e)}"
                    )

                # Call the LLM for refinement with streaming
                accumulated_refine = ""

                # Show streaming status
                self.response_output.append(f"🤖 Refining (attempt {attempt})...\n")
                QtCore.QCoreApplication.processEvents()

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_completion_tokens=4096,
                    temperature=0.0,
                    seed=42,
                    stream=True,  # Enable streaming
                )

                # Stream the response in real-time
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content_chunk = delta.content
                        accumulated_refine += content_chunk
                        # Update output in real-time
                        current_text = self.response_output.toPlainText()
                        if not current_text.endswith(content_chunk):
                            self.response_output.setPlainText(
                                current_text + content_chunk
                            )
                            QtCore.QCoreApplication.processEvents()

                last_raw_message = accumulated_refine

                # Save the raw response
                try:
                    refine_response_path = os.path.join(
                        log_dir,
                        f"{timestamp}_refine_attempt_{attempt}_from_{model_name}.txt",
                    )
                    with open(refine_response_path, "w") as f:
                        f.write(last_raw_message)
                except Exception as e:
                    self.response_output.append(
                        f"❌ Failed to save refinement response for attempt {attempt}:\n{str(e)}"
                    )

                # Try parsing and executing the refined code
                matches = re.findall(
                    r"```(?:python)?\s*(.*?)```", last_raw_message, re.DOTALL
                )
                clean_code = (
                    textwrap.dedent(max(matches, key=len)).strip()
                    if matches
                    else textwrap.dedent(last_raw_message).strip()
                )

                ast.parse(clean_code)
                exec(clean_code, globals())
                self.previous_code = clean_code
                duration_sec = time.time() - start_time if start_time else -1
                self.response_output.setPlainText(
                    f"✅ Refinement succeeded at attempt {attempt} (completed in {duration_sec:.2f} seconds):\n\n{clean_code}"
                )
                self.confirm_button.setEnabled(
                    True
                )  # Allow user to confirm refined macro
                self.reject_button.setEnabled(
                    True
                )  # Allow user to reject even refined macro if needed

                return  # Success! Exit the loop immediately

            except Exception as e2:
                error_msg = str(e2)
                failed_code = (
                    clean_code if "clean_code" in locals() else "<no code extracted>"
                )
                self.response_output.append(
                    f"⚠️ Attempt {attempt} failed. Retrying...\n"
                )
                QtCore.QCoreApplication.processEvents()

                attempt += 1  # Next retry

        # # After exhausting all attempts, reset the state
        # self.response_output.setPlainText(
        #     f"❌ All {max_attempts} refinement attempts failed.\n\nLast Error:\n{error_msg}\n\nHere is the last LLM response:\n\n{last_raw_message}"
        # )
        # self.previous_code = None

        # # Log total time before failure
        # end_time = time.time()
        # duration_sec = end_time - start_time if start_time else -1
        # failure_log = f"🕒 Total time before failure: {duration_sec:.2f} seconds."
        # self.response_output.append(failure_log)

        self.complexCAD(
            user_input=messages,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
        )

        # try:
        #     with open(
        #         os.path.join(log_dir, f"{timestamp}_failure_time_{model_name}.txt"), "w"
        #     ) as f:
        #         f.write(f"{duration_sec:.2f} seconds\n")
        # except Exception as e:
        #     self.response_output.append(
        #         f"❌ Failed to save failure time log:\n{str(e)}"
        #     )

    def confirm_macro_as_good(self):
        if not self.previous_code:
            self.response_output.append("❌ No macro to confirm.")
            return

        prompt = self.prompt_input.toPlainText().strip()
        selection_text = (
            self.last_selection_text
            if hasattr(self, "last_selection_text")
            else "No selection"
        )
        model_used = self.last_successful_model or "Unknown model"

        record = {
            "prompt": prompt,
            "selection": selection_text,
            "code": self.previous_code,
            "model": model_used,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        try:
            with open(cache_file, "a") as f:
                f.write(json.dumps(record) + "\n")
            QtWidgets.QMessageBox.information(
                self, "Macro Cached", "✅ Macro confirmed and saved to cache."
            )
            self.confirm_button.setEnabled(False)
            self.reject_button.setEnabled(False)
        except Exception as e:
            self.response_output.append(f"❌ Failed to save confirmed macro:\n{str(e)}")

    def reject_cached_macro(self):
        prompt = self.prompt_input.toPlainText().strip()
        self.reject_button.setEnabled(False)  # Disable to prevent re-click
        self.response_output.append(
            "👎 User rejected cached macro. Sending prompt to LLM..."
        )
        self.reject_button.setEnabled(False)
        self.confirm_button.setEnabled(False)

        rejected_record = {
            "prompt": prompt,
            "selection": self.last_selection_text
            if hasattr(self, "last_selection_text")
            else "No selection",
            "previous_code": self.previous_code
            if self.previous_code
            else "<no code cached>",  # optional: include code if any
            "model": self.last_successful_model or "Unknown model",
            "timestamp": datetime.datetime.now().isoformat(),
        }

        try:
            with open(rejected_file, "a") as f:
                f.write(json.dumps(rejected_record) + "\n")
        except Exception as e:
            self.response_output.append(f"⚠️ Failed to log rejected macro: {str(e)}")

        # Clear any cached state before retry
        self.previous_code = None
        self.last_successful_model = None

        # Force bypass cache on next submission
        self.skip_cache = True

        # Re-trigger the LLM call by calling on_submit again
        self.on_submit()


class CADAssistantCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(base_dir, "assets", "icon.png"),
            "MenuText": "FreeCADAgent AI Assistant",
            "ToolTip": "Open the FreeCADAgent AI Assistant Panel for LLM-powered macro generation",
        }

    def Activated(self):
        dock = FreeCADGui.getMainWindow().findChild(QtWidgets.QDockWidget, "GPTDock")
        if dock:
            dock.close()

        dock = QtWidgets.QDockWidget("FreeCADAgent AI Assistant")
        dock.setObjectName(
            "GPTDock"
        )  # Updated from "Dock" to "GPTDock" for consistency
        panel = CADAssistantPanel()
        dock.setWidget(panel)
        FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def IsActive(self):
        return True  # Always active


FreeCADGui.addCommand("CAD_Assistant_Command", CADAssistantCommand())
