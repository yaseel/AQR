import tkinter as tk
from tkinter import ttk
import pytesseract
import pyautogui
import requests
import cohere
import os
import time
import re
from spellchecker import SpellChecker
import cv2
import numpy as np
from PIL import ImageGrab, Image


# OCR-related functions
def capture_screen(lang="eng"):
    try:
        # Capture the screen
        screen = ImageGrab.grab()
        screen_np = np.array(screen)

        # Convert to grayscale
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Convert back to PIL Image for pytesseract
        processed_image = Image.fromarray(thresh)

        # Save processed image for debugging
        processed_image.save("processed_screenshot.png")
        print("Debug: Processed screenshot saved as 'processed_screenshot.png'.")

        # Run OCR
        text = pytesseract.image_to_string(processed_image, lang=lang)
        return text
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None


# Clean OCR text
def clean_ocr_output(text):
    print(f"Debug: Raw OCR Output: {text}")  # Debugging: Raw OCR output
    cleaned_text = re.sub(r"[^a-zA-Z0-9\s\?\.,]", "", text)
    corrections = {
        "thie": "third",
        "wes": "was",
        "presitient": "president",
        "Ge": "the",
        "united sketas": "United States",
    }
    for error, correction in corrections.items():
        cleaned_text = cleaned_text.replace(error, correction)

    print(f"Debug: Cleaned OCR Output: {cleaned_text}")  # Debugging: Cleaned OCR output
    return cleaned_text.strip()


# Normalize text
def normalize_text(text):
    spell = SpellChecker()
    words = text.split()
    corrected_words = [spell.correction(word) if spell.correction(word) else word for word in words]
    return " ".join(corrected_words)


# Generate response using Cohere
def generate_response(prompt):
    try:
        api_key = os.getenv("COHERE_API_KEY")
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
        print(f"Error generating response: {e}")
        return "Failed to get a response."


# Clean the AI response
def clean_response(response, original_prompt):
    response = response.replace(original_prompt, "").strip()
    response = response.replace("Question:", "").replace("Answer:", "").strip()
    return response


# Detect and focus on text box
def detect_and_focus_text_box():
    try:
        screen = ImageGrab.grab()
        gray_screen = screen.convert("L")
        data = pytesseract.image_to_data(gray_screen, output_type=pytesseract.Output.DICT)
        keywords = ["Type a message", "Write something", "Enter message"]
        for i, text in enumerate(data["text"]):
            if any(keyword.lower() in text.lower() for keyword in keywords):
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                print(f"Debug: Detected text box at x={x}, y={y}, w={w}, h={h}.")
                pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.5)
                pyautogui.click()
                return True
        fallback_click()
        return False
    except Exception as e:
        print(f"Error detecting text box: {e}")
        return False


# Fallback for text box focus
def fallback_click():
    print("Debug: Using fallback click.")
    pyautogui.moveTo(500, 800, duration=0.5)
    pyautogui.click()


# Automate typing
def type_response(response):
    try:
        if not detect_and_focus_text_box():
            fallback_click()
        print(f"Debug: Typing response: {response}")  # Debugging: Typing response
        pyautogui.typewrite(response, interval=0.1)
        pyautogui.press("enter")
    except Exception as e:
        print(f"Error typing response: {e}")


# Process chat without interruptions
def process_chat():
    text = capture_screen(lang="eng")
    if not text:
        print("Debug: No text detected on the screen.")
        return

    # Log raw OCR output
    print("Debug: OCR Output (Raw):", text)

    # Clean and normalize the OCR text
    text = clean_ocr_output(text)
    print("Debug: OCR Output (Cleaned):", text)

    # Detect the last question
    last_question = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if "?" in line:
            last_question = line
            break

    if not last_question:
        print("Debug: No question detected.")
        return

    print(f"Debug: Detected question (Before Normalization): {last_question}")
    last_question = normalize_text(last_question)
    print(f"Debug: Detected question (After Normalization): {last_question}")

    # Generate AI response
    ai_response = generate_response(last_question)

    # Clean the AI response
    ai_response = clean_response(ai_response, last_question)
    print(f"Debug: AI Response: {ai_response}")

    # Type the AI response automatically
    type_response(ai_response)


# GUI
def main():
    root = tk.Tk()
    root.title("LOOK SMART AI")
    root.geometry("300x200")

    ttk.Button(root, text="Process Chat", command=process_chat).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
