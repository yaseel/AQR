import tkinter as tk
from tkinter import ttk
import pytesseract
import pyautogui
import cohere
import os
import sys
import logging
import time
import re
import cv2
import numpy as np
from PIL import ImageGrab, Image
from cryptography.fernet import Fernet

# Configure Logging
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Decrypt API Key
CIPHER_KEY = b'JjcdhA2jUryMy5VnKm-ZQ2oRhEVeVrU4NjIfdW9_iOQ='
ENCRYPTED_API_KEY = b'gAAAAABniqv_YcQiDjUhYJQwxY54_XDSZZBBDrAc9QQ2N_yS3Fp45TVToGH4onYA24AejkR2CbPcL4-e9U4AypVOko7-4assfik71UPcJyZ_RmAQcUXkH8H094OVUU5uyO_9--58eBvV'

def decrypt_api_key():
    cipher = Fernet(CIPHER_KEY)
    return cipher.decrypt(ENCRYPTED_API_KEY).decode("utf-8")

# Tesseract Configuration
if getattr(sys, 'frozen', False):  # If running as a PyInstaller bundle
    base_path = sys._MEIPASS
    tesseract_path = os.path.join(base_path, "tesseract.exe")
    tessdata_dir = os.path.join(base_path, "tessdata")  # Include tessdata folder
else:  # Normal Python environment
    tesseract_path = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    tessdata_dir = "C:/Program Files/Tesseract-OCR/tessdata"  # Adjust path as necessary

pytesseract.pytesseract.tesseract_cmd = tesseract_path
os.environ["TESSDATA_PREFIX"] = tessdata_dir  # Set TESSDATA_PREFIX

# Popup Status
class PopupStatus:
    def __init__(self, root):
        self.popup = tk.Toplevel(root)
        self.popup.title("Processing...")
        self.popup.geometry("300x120+50+50")
        self.popup.resizable(False, False)
        self.popup.attributes("-topmost", True)

        self.label = ttk.Label(self.popup, text="Initializing...", wraplength=250)
        self.label.pack(pady=10)

        self.close_button = ttk.Button(self.popup, text="Close", command=self.close)
        self.close_button.pack(pady=5)

        self.is_done = False

    def update_status(self, message, is_done=False):
        self.label.config(text=message)
        self.popup.update()

        if is_done:
            self.is_done = True
            self.auto_close()

    def auto_close(self):
        self.popup.after(10000, self.close)

    def close(self):
        self.popup.destroy()

# OCR Functions
def capture_screen_tesseract(lang="eng"):
    try:
        logging.info("Starting screen capture...")
        screen = ImageGrab.grab()
        screen_np = np.array(screen)
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((2, 2), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        debug_image = Image.fromarray(enhanced)
        debug_image.save("enhanced_debug.png")
        logging.info("Processed screenshot saved as 'enhanced_debug.png'.")

        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(debug_image, lang=lang, config=custom_config)
        logging.debug(f"OCR Text (Tesseract): {text[:50]}...")
        return text
    except Exception as e:
        logging.error(f"Tesseract OCR failed: {e}")
        return None

# Processing Functions
def clean_ocr_output(text):
    """
    Clean OCR output dynamically for all languages by removing noise and irrelevant lines.
    """
    logging.debug(f"Raw OCR Output: {text}")
    cleaned_text = re.sub(r"[^\w\s\?\.,:;!\"'()\-]", "", text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    meaningful_lines = [line.strip() for line in cleaned_text.splitlines() if len(line.split()) > 2 or "?" in line]
    final_text = " ".join(meaningful_lines)
    logging.debug(f"Cleaned OCR Output: {final_text}")
    return final_text

def generate_response(prompt):
    try:
        api_key = decrypt_api_key()
        co = cohere.Client(api_key)
        instruction_prompt = (
            "Answer the following question clearly and concisely. "
            "Do not repeat the question.\n\n"
            f"Question: {prompt}\n"
            "Answer:"
        )
        response = co.generate(
            model="command-xlarge-nightly",
            prompt=instruction_prompt,
            max_tokens=100,
        )
        return response.generations[0].text.strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "Failed to get a response."

def type_response(response):
    try:
        pyautogui.typewrite(response, interval=0.01)
        pyautogui.press("enter")
    except Exception as e:
        logging.error(f"Error typing response: {e}")

def process_chat(root):
    popup = PopupStatus(root)
    popup.update_status("Waiting for user to click on text box...")

    time.sleep(1)
    popup.update_status("Processing OCR...")

    text = capture_screen_tesseract()
    if not text:
        popup.update_status("Failed: No text detected.")
        return

    popup.update_status("Cleaning OCR output...")
    text = clean_ocr_output(text)

    popup.update_status("Detecting question...")
    last_question = None
    for line in reversed(text.splitlines()):
        if "?" in line:
            last_question = line.strip()
            break

    if not last_question:
        popup.update_status("Failed: No question detected.")
        return

    popup.update_status("Generating response...")
    ai_response = generate_response(last_question)

    if "Failed" in ai_response:
        popup.update_status("Failed: Response generation failed.")
        return

    popup.update_status("Typing response...")
    type_response(ai_response)

    popup.update_status("Done!", is_done=True)

# GUI
def main():
    root = tk.Tk()
    root.title("LOOK SMART AI")
    root.geometry("300x200")

    ttk.Button(root, text="Process Chat", command=lambda: process_chat(root)).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
