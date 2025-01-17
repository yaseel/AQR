import tkinter as tk
from tkinter import ttk, messagebox
import pytesseract
import pyautogui
import threading
import requests
import time
import cv2
import numpy as np
from PIL import ImageGrab, Image

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        return "eng"

def capture_screen(lang="eng"):
    try:
        screen = ImageGrab.grab()
        gray = cv2.cvtColor(np.array(screen), cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed_image = Image.fromarray(thresh)
        processed_image.save("processed_screenshot.png")
        text = pytesseract.image_to_string(processed_image, lang=lang)
        return text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to capture screen: {e}")
        return None

def generate_response(prompt):
    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer YOUR_API_KEY"}
    for _ in range(3):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt})
            response.raise_for_status()
            return response.json()[0]["generated_text"]
        except requests.exceptions.RequestException:
            time.sleep(5)
    return "Failed to get a response."

def detect_and_focus_text_box():
    try:
        screen = ImageGrab.grab()
        gray_screen = screen.convert("L")
        data = pytesseract.image_to_data(gray_screen, output_type=pytesseract.Output.DICT)
        keywords = ["Type a message", "Write something", "Enter message"]
        for i, text in enumerate(data["text"]):
            if any(keyword.lower() in text.lower() for keyword in keywords):
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.5)
                pyautogui.click()
                return True
        return False
    except Exception:
        return False

def type_response(response):
    try:
        if not detect_and_focus_text_box():
            pyautogui.moveTo(500, 800)  # Example fallback coordinates
            pyautogui.click()
        pyautogui.typewrite(response, interval=0.1)
        pyautogui.press("enter")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to type response: {e}")

def process_chat():
    print("Process Chat button clicked!")
    text = capture_screen(lang="eng")
    if not text:
        messagebox.showerror("Error", "No text detected on the screen.")
        return
    print("OCR Output:", text)
    last_question = next((line for line in reversed(text.splitlines()) if "?" in line), None)
    if not last_question:
        messagebox.showinfo("Info", "No question detected on the screen.")
        return
    ai_response = generate_response(last_question)
    if ai_response:
        messagebox.showinfo("AI Response", ai_response)
        if messagebox.askyesno("Type Response", "Do you want to type this response automatically?"):
            type_response(ai_response)

def main():
    root = tk.Tk()
    root.title("LOOK SMART AI")
    bg_color, fg_color = "#282c34", "white"
    button_bg, button_fg, exit_bg = "#007acc", "white", "#cc0000"

    style = ttk.Style()
    style.configure("TButton", background=button_bg, foreground=button_fg)

    ttk.Button(root, text="Process Chat", command=process_chat).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

    root.geometry("300x200")
    root.mainloop()

if __name__ == "__main__":
    main()
