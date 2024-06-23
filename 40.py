import cv2
import pytesseract
import numpy as np
from tkinter import Tk, filedialog, Toplevel, Frame
from tkinter import Button as TkButton
from tkinter import Label as TkLabel
from tkinter import ttk
from PIL import Image, ImageTk
import pyttsx3
import ctypes

# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize pyttsx3
engine = pyttsx3.init()

# Global variable to store the file path of the most recent processed image
last_processed_image_path = None

# Function to upload an image
def upload_image():
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename()  # Open file dialog to choose an image
    root.deiconify()  # Show the main window again
    if file_path:
        process_image(file_path)

# Function to process the uploaded image
def process_image(file_path, speak_result=False):
    global last_processed_image_path  # Access the global variable

    # Load the image
    image = cv2.imread(file_path)

    # Preprocessing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)

    # Find contours in the edged image
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    # Loop over the contours to find the number plate
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)

        if len(approx) == 4:
            number_plate_contour = approx
            break

    # Masking the number plate region
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [number_plate_contour], 0, 255, -1)
    new_image = cv2.bitwise_and(image, image, mask=mask)

    # OCR on the number plate region
    plate_text = pytesseract.image_to_string(new_image)

    # Replace 'O' with '0' and 'S' with '5' in the 3rd and 4th place elements
    plate_text = plate_text[:2] + plate_text[2:].replace('O', '0').replace('S', '5')

    # Extract the first two alphanumeric characters
    first_two_chars = ''.join(c for c in plate_text[:2] if c.isalnum())

    # Extract the remaining alphanumeric characters, excluding null characters
    remaining_characters = ''.join(c.upper() for c in plate_text[2:] if c.isalnum())

    # Construct the modified plate text with a gap after the first two characters
    modified_plate_text = f"{first_two_chars} {' '.join(remaining_characters.split())}"

    print("Modified Plate Text:", modified_plate_text)

    # Classify the output based on the registration number
    state, district = classify_state_and_district(modified_plate_text)

    # Print the state and district for debugging
    print("Classified State:", state)
    print("Classified District:", district)

    # Update the result label
    result_text = "Detected Number Plate: " + modified_plate_text + "\nState: " + state + "\nDistrict: " + district
    result_label.config(text=result_text)

    # Store the file path of the most recent processed image
    last_processed_image_path = file_path

    # Speak the detected number plate, state, and district if requested
    if speak_result:
        speak_text = "Detected number plate is " + modified_plate_text + " from " + state + " " + district
        engine.say(speak_text)
        engine.runAndWait()


def classify_state_and_district(registration_number): 
    state_district_mapping = {
        'KA': ("Karnataka", {
            '01': "Bidar",
            '02': "Gulbarga",
            '03': "Bellary",
            '04': "Raichur",
            '05': "Koppal",
            # Add more district codes and names as needed
        }),
        'DL': ("dheli", {
            '01': "North Delhi",
            '02': "Central Delhi",
            '03': "South Delhi",
            '04': "New Delhi",
            '38': "East Delhi",
            # Add more district codes and names as needed
        }),
        'AP': ("Andhra Pradesh", {
            '01': "Srikakulam",
            '02': "Vizianagaram",
            '03': "Visakhapatnam",
            '04': "East Godavari",
            '09': "West Godavari",  # Updated district code
            # Add more district codes and names as needed
        }),
        'MH': ("Maharashtra", {
            '01': "Amravati",
            '02': "Aurangabad",
            '03': "Kolhapur",
            '04': "Mumbai City",
            '12': "Mumbai Suburban",
            # Add more district codes and names as needed
        }),
        # Add more state codes and districts as needed
    }

    # Extract state code and district code from the registration number
    state_code = registration_number[:2]
    district_code = registration_number[3:5]

    # Replace 'O' with '0' and 'S' with '5' in the district code
    district_code = district_code.replace('O', '0').replace('S', '5')

    # Lookup state and district based on the extracted codes
    state, districts = state_district_mapping.get(state_code, ("Unknown", {}))
    district = districts.get(district_code, "Unknown")

    return state, district

# Function to minimize the window
def minimize_window():
    root.overrideredirect(False)
    root.iconify()

# Function to exit the application
def exit_app():
    root.destroy()

# Function to exit full-screen mode
def exit_fullscreen(event):
    root.attributes('-fullscreen', False)

# Function to clear the image and restart the program
def clear_image():
    result_label.config(text="")  # Clear the result label
    # Add any other necessary cleanup or reset operations here

# Function to speak out the result
def speak_result():
    global last_processed_image_path  # Access the global variable
    if last_processed_image_path:
        process_image(last_processed_image_path, speak_result=True)

# Create the Tkinter window
root = Tk()
root.title("Number Plate Detection")

# Set the window to full-screen mode
root.attributes('-fullscreen', True)

# Get screen width and height
user32 = ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Set the geometry of the root window to match screen resolution
root.geometry(f"{screen_width}x{screen_height}")

# Bind the Escape key to the exit_fullscreen function
root.bind('<Escape>', exit_fullscreen)

# Set the background image
bg_image = Image.open("09.jpg")  # Replace "04.jpg" with the path to your image
bg_photo = ImageTk.PhotoImage(bg_image.resize((screen_width, screen_height)))  # Resize image to screen resolution
bg_label = TkLabel(root, image=bg_photo)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# Create a frame for the result label with a border
result_frame = Frame(root, bd=2, relief="solid", bg="white")
result_frame.place(relx=0.5, rely=0.8, anchor="center")  # Place the frame at the middle bottom

# Label to display result
result_label = TkLabel(result_frame, text="", bg=result_frame.cget("bg"), fg="black", font=("Arial", 16), justify="center")
result_label.pack(padx=0, pady=0)  # Added padding inside the frame

# Define custom style for stadium-shaped buttons
style = {'background': 'green', 'foreground': 'light green', 'relief': 'flat', 'font': ("arial", 24), 'borderwidth': 30}  # Increased font size and borderwidth

# Button to upload image
upload_button = ttk.Button(root, text="Upload Image", command=upload_image, style='Custom.TButton')
upload_button.place(relx=0.5, rely=0.5, anchor="center")  # Place the button at the middle

# Button to speak out the result
voice_button = ttk.Button(root, text="Voice", command=speak_result, style='Custom.TButton')
voice_button.place(relx=0.5, rely=0.55, anchor="center")  

# Button to clear the image and restart the program
clear_button = ttk.Button(root, text="Clear", command=clear_image, style='Custom.TButton')
clear_button.place(relx=0.5, rely=0.6, anchor="center")  # Place the button below the voice button

# Create a Toplevel window for the minimize and exit buttons
button_window = Toplevel(root)
button_window.overrideredirect(True)  # Remove the window border
button_window.geometry("+%d+0" % (root.winfo_screenwidth() - 100))  # Position the window in the top-right corner

# Minimize button
minimize_button = TkButton(button_window, text="_", font=("Arial", 12), command=minimize_window, bg='light grey', bd=0)
minimize_button.pack(side="left", padx=5)

# Exit button
exit_button = TkButton(button_window, text="X", font=("Arial", 12), command=exit_app, bg='light grey', bd=0)
exit_button.pack(side="left", padx=5)

style_name = 'Custom.TButton'
s = ttk.Style()
s.configure(style_name, borderwidth=0, background='green')
s.map(style_name, background=[('active', 'orange')])  # Missing line

root.mainloop()
 