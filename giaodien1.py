import tkinter as tk
from tkinter import messagebox
import serial
import threading
import time

class MotorControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Motor Control")

        # Serial connection
        self.serial_conn = serial.Serial('COM5', 115200, timeout=1)

        # Desired Speed Label and Entry
        self.desired_speed_label = tk.Label(master, text="Desired Speed (RPM):")
        self.desired_speed_label.pack()

        self.desired_speed_entry = tk.Entry(master)
        self.desired_speed_entry.pack()

        self.set_speed_button = tk.Button(master, text="Set Speed", command=self.set_speed)
        self.set_speed_button.pack()

        # Direction Buttons
        self.forward_button = tk.Button(master, text="Forward", command=self.set_forward)
        self.forward_button.pack()

        self.reverse_button = tk.Button(master, text="Reverse", command=self.set_reverse)
        self.reverse_button.pack()

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_motor)
        self.stop_button.pack()

        # Display Current Speed
        self.current_speed_label = tk.Label(master, text="Current Speed (RPM): 0")
        self.current_speed_label.pack()

        # Display Pulse Count
        self.pulse_count_label = tk.Label(master, text="Pulse Count: 0")
        self.pulse_count_label.pack()

        # Display Error
        self.error_label = tk.Label(master, text="Error: 0")
        self.error_label.pack()

        # Start a thread to read serial data
        self.reading_thread = threading.Thread(target=self.read_serial_data)
        self.reading_thread.daemon = True
        self.reading_thread.start()

    def set_speed(self):
        try:
            desired_speed = int(self.desired_speed_entry.get())
            command = f"D{desired_speed}\n"
            self.serial_conn.write(command.encode())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the speed.")

    def set_forward(self):
        command = "F\n"
        self.serial_conn.write(command.encode())

    def set_reverse(self):
        command = "R\n"
        self.serial_conn.write(command.encode())

    def stop_motor(self):
        command = "S\n"
        self.serial_conn.write(command.encode())

    def read_serial_data(self):
        while True:
            if self.serial_conn.in_waiting > 0:
                data = self.serial_conn.readline().decode('utf-8').strip()
                if "Current Speed:" in data:
                    parts = data.split(", ")
                    current_speed = parts[0].split(": ")[1]
                    pulse_count = parts[1].split(": ")[1]
                    error = parts[3].split(": ")[1]

                    self.current_speed_label.config(text=f"Current Speed (RPM): {current_speed}")
                    self.pulse_count_label.config(text=f"Pulse Count: {pulse_count}")
                    self.error_label.config(text=f"Error: {error}")

            time.sleep(0.1)

    def on_closing(self):
        self.serial_conn.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
