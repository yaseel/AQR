import tkinter as tk
from tkinter import messagebox
import mss
import requests
import pytesseract
import pyautogui
import threading
import time
import cv2
import numpy as np
from langdetect import detect
from PIL import ImageGrab
from PIL import Image

def detect_language(text):
    try:
        return detect(text)  # Returns a language code (e.g., "en", "fr", "es")
    except Exception as e:
        return "eng"  # Default to English if detection fails

def capture_screen(lang="eng"):
    try:
        # Capture the screen
        screen = ImageGrab.grab()
        # Convert the screen to a NumPy array for processing
        screen_np = np.array(screen)

        # Convert to grayscale
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        # Apply adaptive thresholding for better text visibility
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Convert back to PIL Image for pytesseract
        processed_image = Image.fromarray(thresh)

        # Save processed image for debugging (optional)
        processed_image.save("processed_screenshot.png")

        # Run OCR
        text = pytesseract.image_to_string(processed_image, lang=lang)
        return text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to capture screen: {e}")
        return None

# Function to generate AI response
def generate_response(prompt):
    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer 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"}  # Replace with your API key

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prompt})
            response.raise_for_status()
            return response.json()[0]["generated_text"]
        except requests.exceptions.RequestException as e:
            if attempt < 2:
                time.sleep(5)  # Wait 5 seconds before retrying
            else:
                return f"Error: {e}"

def detect_and_focus_text_box():
    try:
        # Capture the screen
        screen = ImageGrab.grab()
        gray_screen = screen.convert("L")  # Convert to grayscale for OCR

        # Run OCR and get bounding box data
        data = pytesseract.image_to_data(gray_screen, output_type=pytesseract.Output.DICT)

        # Look for placeholder text or labels near text boxes
        keywords = ["Type a message", "Write something", "Enter message"]  # Add platform-specific hints
        for i, text in enumerate(data["text"]):
            if any(keyword.lower() in text.lower() for keyword in keywords):
                # Get bounding box coordinates
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                print(f"Detected text box at: x={x}, y={y}, width={w}, height={h}")

                # Move the mouse to the center of the detected box and click
                pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.5)
                pyautogui.click()
                return True

        # If no matching text box is found
        messagebox.showerror("Error", "Text box not found on screen.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Failed to detect text box: {e}")
        return False

# Function to automate typing
def type_response(response):
    try:
        # Detect and focus on the text box
        if not detect_and_focus_text_box():
            return  # Exit if the text box isn't found

        # Type the response
        for chunk in [response[i:i+50] for i in range(0, len(response), 50)]:
            pyautogui.typewrite(chunk, interval=0.1)
            pyautogui.press("enter")
            time.sleep(0.5)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to type response: {e}")


def type_response_threaded(response):
    thread = threading.Thread(target=type_response, args=(response,))
    thread.start()

# Main function to handle the process
def process_chat():
    text = capture_screen(lang="eng")  # Change "eng" if the language is different
    if not text:
        messagebox.showerror("Error", "No text detected on the screen.")
        return

    print("OCR Output:", text)  # Debugging: Print the raw OCR output

    last_question = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]  # Clean up lines
    for line in reversed(lines):
        if "?" in line:  # Detect questions
            last_question = line
            break

    if not last_question:
        messagebox.showinfo("Info", "No question detected on the screen.")
        return

    ai_response = generate_response(last_question)
    if ai_response:
        messagebox.showinfo("AI Response", ai_response)
        if messagebox.askyesno("Type Response", "Do you want to type this response automatically?"):
            type_response(ai_response)

# GUI Setup
def set_language(option_var):
    global selected_language
    selected_language = option_var.get()

def main():
    global selected_language
    selected_language = "eng"  # Default language

    root = tk.Tk()
    root.title("LOOK SMART AI")

    bg_color = "#282c34"  # Dark gray
    fg_color = "white"  # Text color
    button_bg = "#007acc"  # Blue
    button_fg = "white"
    exit_bg = "#cc0000"  # Red

    # Add a dropdown for language selection
    language_options = {"English": "eng", "French": "fra", "Spanish": "spa"}
    option_var = tk.StringVar(root)
    option_var.set("English")  # Default value
    dropdown = tk.OptionMenu(root, option_var, *language_options.keys(), command=set_language)
    dropdown.pack(pady=10)

    process_button = tk.Button(
        root, text="Process Chat", command=lambda: print("Processing chat..."),
        font=("Arial", 12), bg=button_bg, fg=button_fg, activebackground=button_bg, activeforeground=button_fg
    )
    process_button.pack(pady=10)

    exit_button = tk.Button(
        root, text="Exit", command=root.quit,
        font=("Arial", 12), bg=exit_bg, fg=button_fg, activebackground=exit_bg, activeforeground=button_fg
    )
    exit_button.pack(pady=10)

    root.tk.call("tk", "scaling", 1.0)

    root.geometry("300x200")
    root.mainloop()


if __name__ == "__main__":
    main()
