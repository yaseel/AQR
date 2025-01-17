import tkinter as tk
from tkinter import ttk
import pytesseract
import pyautogui
import requests
import cohere
import os
import sys
import time
import re
import cv2
import numpy as np
from PIL import ImageGrab, Image
from cryptography.fernet import Fernet

class PopupStatus:
    def __init__(self, root):
        self.popup = tk.Toplevel(root)
        self.popup.title("Processing...")
        self.popup.geometry("250x100+50+50")  # Positioned at the corner
        self.popup.resizable(False, False)
        self.popup.attributes("-topmost", True)  # Keep popup on top

        self.label = ttk.Label(self.popup, text="Initializing...", wraplength=200, anchor="center", justify="center")
        self.label.pack(pady=10)

        self.close_button = ttk.Button(self.popup, text="Close", command=self.close)
        self.close_button.pack(pady=5)

        # Track if the popup should auto-close
        self.is_done = False

    def update_status(self, message, is_done=False):
        """
        Update the status message in the popup.
        """
        self.label.config(text=message)
        self.popup.update()  # Ensure the popup updates immediately

        if is_done:
            self.is_done = True
            self.auto_close()

    def auto_close(self):
        """
        Auto-close the popup after 10 seconds.
        """
        self.popup.after(10000, self.close)

    def close(self):
        """
        Close the popup.
        """
        self.popup.destroy()

last_question_global = None  # Tracks the last question detected


CIPHER_KEY = b'JjcdhA2jUryMy5VnKm-ZQ2oRhEVeVrU4NjIfdW9_iOQ='
ENCRYPTED_API_KEY = b'gAAAAABniqv_YcQiDjUhYJQwxY54_XDSZZBBDrAc9QQ2N_yS3Fp45TVToGH4onYA24AejkR2CbPcL4-e9U4AypVOko7-4assfik71UPcJyZ_RmAQcUXkH8H094OVUU5uyO_9--58eBvV'

def decrypt_api_key():
    cipher = Fernet(CIPHER_KEY)
    return cipher.decrypt(ENCRYPTED_API_KEY).decode("utf-8")

if getattr(sys, 'frozen', False):  # Running as a PyInstaller bundle
    base_path = sys._MEIPASS
    tesseract_path = os.path.join(base_path, "tesseract.exe")
else:  # Running in a normal Python environment
    tesseract_path = "C:/Program Files/Tesseract-OCR/tesseract.exe"  # Adjust path as needed

pytesseract.pytesseract.tesseract_cmd = tesseract_path

# EasyOCR (Optional)
try:
    import easyocr
    EASY_OCR_ENABLED = True
except ImportError:
    EASY_OCR_ENABLED = False
    print("EasyOCR not installed. Defaulting to Tesseract.")

def capture_screen(lang="eng"):
    try:
        screen = ImageGrab.grab()
        screen_np = np.array(screen)

        # Convert to grayscale
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)

        # Apply morphological transformations for better segmentation
        kernel = np.ones((2, 2), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

        # Use CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Save debug image
        debug_image = Image.fromarray(enhanced)
        debug_image.save("enhanced_debug.png")

        # OCR with Tesseract
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(debug_image, lang=lang, config=custom_config)
        return text
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None


# EasyOCR implementation (Optional)
def capture_screen_easyocr():
    if not EASY_OCR_ENABLED:
        print("EasyOCR is not installed.")
        return None

    try:
        reader = easyocr.Reader(['en'])  # Initialize EasyOCR
        screen = ImageGrab.grab()
        screen.save("raw_screenshot.png")
        print("Debug: Raw screenshot saved as 'raw_screenshot.png'.")

        # Use EasyOCR for text detection
        result = reader.readtext(np.array(screen))
        detected_text = " ".join([text[1] for text in result])
        return detected_text
    except Exception as e:
        print(f"Error with EasyOCR: {e}")
        return None

def clean_ocr_output(text):
    """
    Clean OCR output dynamically for all languages by removing noise and irrelevant lines.
    """
    print(f"Debug: Raw OCR Output: {text}")

    # Remove non-printable characters and excessive whitespace
    cleaned_text = re.sub(r"[^\w\s\?\.,:;!\"'()\-]", "", text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    # Extract meaningful lines (filter out short or irrelevant lines)
    meaningful_lines = [
        line.strip() for line in cleaned_text.splitlines()
        if len(line.split()) > 2 or "?" in line
    ]

    # Rejoin meaningful lines
    final_text = " ".join(meaningful_lines)

    print(f"Debug: Cleaned OCR Output: {final_text}")
    return final_text



# Normalize text
def normalize_text(text):
    # Perform basic cleanup and normalization
    text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text



# Generate response using Cohere
def generate_response(prompt):
    try:
        # Decrypt the API key
        api_key = decrypt_api_key()
        co = cohere.Client(api_key)

        # Create the prompt
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
        print(f"Error generating response: {e}")
        return "Failed to get a response."


# Clean the AI response
def clean_response(response, original_prompt):
    response = response.replace(original_prompt, "").strip()
    response = response.replace("Question:", "").replace("Answer:", "").strip()
    return response

# Automate typing directly without cursor positioning
def type_response(response):
    try:
        print(f"Debug: Typing response: {response}")  # Debugging: Typing response
        pyautogui.typewrite(response, interval=0.01)  # Assume user has clicked the input field
        pyautogui.press("enter")
    except Exception as e:
        print(f"Error typing response: {e}")



def process_chat(root):
    global last_question_global

    popup = PopupStatus(root)  # Initialize the popup
    popup.update_status("Waiting for user to click on text box...")

    # Simulated user action to click the text box
    time.sleep(1)  # Replace with an event-based system later
    popup.update_status("Processing OCR...")

    # Use EasyOCR if enabled, otherwise fallback to Tesseract
    if EASY_OCR_ENABLED:
        text = capture_screen_easyocr()
    else:
        text = capture_screen(lang="eng")

    if not text:
        popup.update_status("Failed: No text detected.")
        return

    print("Debug: OCR Output (Raw):", text)

    popup.update_status("Cleaning OCR output...")
    text = clean_ocr_output(text)
    print("Debug: OCR Output (Cleaned):", text)

    popup.update_status("Detecting question...")
    last_question = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if "?" in line:  # Detect questions
            last_question = line
            break

    if not last_question:
        popup.update_status("Failed: No question detected.")
        return

    if last_question == last_question_global:
        popup.update_status("Skipped: No new question.")
        return

    print(f"Debug: Detected question: {last_question}")
    last_question_global = last_question  # Update the global state

    popup.update_status("Generating response...")
    ai_response = generate_response(last_question)

    if "Failed" in ai_response:
        popup.update_status("Failed: AI response generation failed.")
        return

    ai_response = clean_response(ai_response, last_question)
    print(f"Debug: AI Response: {ai_response}")

    popup.update_status("Typing response...")
    type_response(ai_response)

    popup.update_status("Done!", is_done=True)




# GUI
def main():
    global root  # Ensure `root` is globally accessible if needed
    root = tk.Tk()
    root.title("LOOK SMART AI")
    root.geometry("300x200")

    ttk.Button(root, text="Process Chat", command=lambda: process_chat(root)).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

    root.mainloop()



if __name__ == "__main__":
    main()
