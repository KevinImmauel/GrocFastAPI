import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
import subprocess
import datetime
import os
import requests
import json
import tkinter as tk
from tkinter import ttk
import qrcode
from PIL import Image, ImageTk

# API URL
API_URL = "https://bf61-2401-4900-1cb8-e062-683a-35ad-efc1-f04a.ngrok-free.app/predict/"

# Prices per kg
price_per_kg = {
    "apple": 72,
    "tomato": 26,
    "banana": 36,
    "grapes": 75
}

# Initialize GPIO and HX711
def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup()
    print("Bye!")
    sys.exit()

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
referenceUnit = -192.5
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()

# Ensure the "images" directory exists
os.makedirs("images", exist_ok=True)

class WeightTrackingApp:
    def __init__(self, root):
        self.serial_no = 1  # Initialize the serial number inside the class
        self.item_data = {}  # Store item data in the class
        self.previous_weight = 0
        self.stable_weight = 0
        self.start_stable_time = None
        self.items_weights = []
        
        # GUI Setup
        self.root = root
        self.root.attributes("-fullscreen", True)
        self.root.title("Automated Billing System")

        # Title Label
        self.title_label = tk.Label(self.root, text="Automated Billing System", font=("Helvetica", 36, "bold"))
        self.title_label.pack(pady=20)

        columns = ("Index", "Name", "Weight (grams)", "Price")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)
        self.tree.heading("Index", text="Index")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Weight (grams)", text="Weight (grams)")
        self.tree.heading("Price", text="Price")
        self.tree.column("Index", width=100, anchor=tk.CENTER)
        self.tree.column("Name", width=200, anchor=tk.CENTER)
        self.tree.column("Weight (grams)", width=200, anchor=tk.CENTER)
        self.tree.column("Price", width=200, anchor=tk.CENTER)

        # Increase font size for table
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 18, "bold"))
        style.configure("Treeview", font=("Helvetica", 16))

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Button to delete the last row
        self.delete_button = tk.Button(self.root, text="Delete Last Row", command=self.delete_last_row, font=("Helvetica", 24), height=2, width=20)
        self.delete_button.pack(side=tk.BOTTOM, pady=10)

        # Button to clear all rows
        self.clear_button = tk.Button(self.root, text="Clear All", command=self.clear_all, font=("Helvetica", 24), height=2, width=20)
        self.clear_button.pack(side=tk.BOTTOM, pady=10)

        # Button to Checkout
        self.checkout_button = tk.Button(self.root, text="Checkout", command=self.checkout, font=("Helvetica", 24), height=2, width=20)
        self.checkout_button.pack(side=tk.BOTTOM, pady=10)

        # Canvas to display QR code
        self.qr_canvas = tk.Canvas(self.root, width=200, height=200)
        self.qr_canvas.pack(pady=20)

        # Start the periodic check for weight
        self.update_weight()

    # Function to update the table
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_weight = 0
        total_price = 0
        for index, (key, value) in enumerate(self.item_data.items(), start=1):
            self.tree.insert("", tk.END, values=(index, value["name"], value["weight"], value["price"]))
            total_weight += value["weight"]
            total_price += value["price"]

        # Add the total row with cumulative weight and price
        self.tree.insert("", tk.END, values=("Total", "Total", total_weight, total_price))

    # Button actions
    def delete_last_row(self):
        if self.item_data:
            self.item_data.pop(max(self.item_data.keys()))
            self.update_table()

    def clear_all(self):
        self.item_data.clear()  # Clear the item data dictionary
        self.update_table()  # Update the table to show no items
        # Don't clear the QR code canvas

    def checkout(self):
        total_price = sum(item["price"] for item in self.item_data.values())
        total_weight = sum(item["weight"] for item in self.item_data.values())
        print(f"Total Weight: {total_weight} grams")
        print(f"Total Price: {total_price} INR")
        # Display total in a message box or log it
        checkout_message = f"Total Weight: {total_weight} grams\nTotal Price: {total_price} INR"
        print(checkout_message)

        # Generate and display the QR code for google.com
        self.generate_qr_code("https://www.google.com")

    def generate_qr_code(self, url):
        # Generate QR code for the given URL
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        # Convert to an image and display it in the canvas
        img = qr.make_image(fill="black", back_color="white")
        img = img.resize((200, 200))  # Resize for display
        img_tk = ImageTk.PhotoImage(img)

        # Display the QR code on the canvas
        self.qr_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.qr_canvas.image = img_tk  # Keep a reference to prevent garbage collection

    # Function to capture image and send to API
    def capture_and_send_image(self, image_path):
        try:
            print("Sending image to API...")
            with open(image_path, 'rb') as image_file:
                files = {'file': ('image.jpg', image_file, 'image/jpeg')}
                response = requests.post(API_URL, files=files)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending image to API: {e}")
            return None

    # Periodic check for weight
    def update_weight(self):
        weight = hx.get_weight(5)
        print(f"Raw weight reading: {weight}")

        if weight < 0:
            weight = 0  # Ignore negative weights

        if abs(weight) < 1:
            self.stable_weight = 0
            self.start_stable_time = None
        else:
            if abs(weight - self.stable_weight) <= 1:
                if self.start_stable_time is None:
                    self.start_stable_time = time.time()

                elapsed_time = time.time() - self.start_stable_time
                if elapsed_time >= 2:
                    print(f"Stable weight detected: {round(weight, 2)} grams")
                    if abs(weight - self.previous_weight) > 1:
                        self.items_weights.append(round(weight, 2))
                        print(f"Item added with weight: {round(weight, 2)} grams")
                        self.previous_weight = weight

                        item_count = len(self.items_weights)
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        image_path = f"images/item_{item_count}_{timestamp}.jpg"
                        command = ["libcamera-still", "-r", "-n", "-o", image_path]

                        try:
                            subprocess.run(command, check=True)
                            print(f"Image captured: {image_path}")
                            api_response = self.capture_and_send_image(image_path)

                            # Parse API response
                            detected_item = "unknown"
                            confidence = 0
                            if api_response and "results" in api_response and len(api_response["results"]) > 0:
                                first_result = api_response["results"][0]
                                detected_item = list(first_result.keys())[0]
                                confidence = first_result[detected_item]

                            # Only process items with confidence >= 0.3
                            if confidence >= 0.3:
                                # Calculate price
                                price = 0
                                if detected_item in price_per_kg:
                                    price = round(weight * (price_per_kg[detected_item] / 1000), 2)

                                # Debugging output
                                print(f"API Response: {api_response}")
                                print(f"Detected Item: {detected_item}, Confidence: {confidence}")
                                print(f"Weight: {weight}g, Price: {price} INR")

                                # Add data to dictionary
                                self.item_data[self.serial_no] = {"name": detected_item, "weight": round(weight, 2), "price": price}
                                self.serial_no += 1  # Increment the serial number

                                # Update the table
                                self.update_table()

                        except subprocess.CalledProcessError as e:
                            print(f"Failed to capture image: {e}")

                    self.stable_weight = 0
                    self.start_stable_time = None
            else:
                self.stable_weight = weight
                self.start_stable_time = None

        # Schedule the next check
        self.root.after(100, self.update_weight)  # Check again after 100ms

if __name__ == "__main__":
    root = tk.Tk()
    app = WeightTrackingApp(root)
    root.mainloop()
