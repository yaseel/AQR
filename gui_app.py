import tkinter as tk
from tkinter import ttk, messagebox
import pytesseract
import pyautogui
import threading
import requests
import cohere
import time
import re
from spellchecker import SpellChecker
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
        # Capture the screen
        screen = ImageGrab.grab()  # Take a screenshot
        screen_np = np.array(screen)  # Convert to a NumPy array

        # Convert to grayscale
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding for dynamic contrast enhancement
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Convert back to PIL Image for pytesseract
        processed_image = Image.fromarray(thresh)

        # Save processed image for debugging
        processed_image.save("processed_screenshot.png")
        print("Debug Image Saved: processed_screenshot.png")

        # Run OCR on the processed image
        text = pytesseract.image_to_string(processed_image, lang=lang)
        return text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to capture screen: {e}")
        return None



def generate_response(prompt):
    try:
        co = cohere.Client("REDACTED")  # Replace with your actual API key

        # Update the prompt to include clear instructions
        instruction_prompt = (
            "Answer the following question clearly and concisely. "
            "Do not repeat the question.\n\n"
            f"Question: {prompt}\n"
            "Answer:"
        )

        response = co.generate(
            model="command-xlarge-nightly",
            prompt=instruction_prompt,
            max_tokens=100,  # Adjust as needed
        )
        return response.generations[0].text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Failed to get a response."


def clean_response(response, original_prompt):
    # Remove parts of the response that repeat the original prompt
    response = response.replace(original_prompt, "").strip()

    # Optionally, strip common prefixes like "Question:" or "Answer:"
    response = response.replace("Question:", "").replace("Answer:", "").strip()

    return response

def clean_ocr_output(text):
    # Remove non-alphanumeric characters except for spaces and punctuation
    cleaned_text = re.sub(r"[^a-zA-Z0-9\s\?\.,]", "", text)

    # Replace common OCR errors with corrections
    corrections = {
        "thie": "third",
        "wes": "was",
        "presitient": "president",
        "Ge": "the",
        "united sketas": "United States"
    }
    for error, correction in corrections.items():
        cleaned_text = cleaned_text.replace(error, correction)

    return cleaned_text.strip()

def normalize_text(text):
    spell = SpellChecker()
    words = text.split()
    corrected_words = [spell.correction(word) if spell.correction(word) else word for word in words]
    return " ".join(corrected_words)


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
    text = capture_screen(lang="eng")
    if not text:
        messagebox.showerror("Error", "No text detected on the screen.")
        return

    print("OCR Output (Raw):", text)  # Debugging: Raw OCR output

    # Clean and normalize the OCR text
    text = clean_ocr_output(text)
    print("OCR Output (Cleaned):", text)  # Debugging: Cleaned OCR output

    # Detect the last question from the OCR output
    last_question = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if "?" in line:  # Detect questions
            last_question = line
            break

    if not last_question:
        messagebox.showinfo("Info", "No question detected on the screen.")
        return

    # Normalize the detected question
    last_question = normalize_text(last_question)

    print(f"Detected question: {last_question}")  # Debugging

    # Generate AI response
    ai_response = generate_response(last_question)

    # Clean the AI response to remove any repeated question
    ai_response = clean_response(ai_response, last_question)

    # Show the response
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
