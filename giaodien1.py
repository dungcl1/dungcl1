import tkinter as tk
from tkinter import messagebox
import serial
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MotorControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Motor Control")

        # Serial connection
        try:
            self.serial_conn = serial.Serial('COM5', 115200, timeout=1)
        except serial.SerialException as e:
            messagebox.showerror("Serial Error", f"Could not open port: {e}")
            master.destroy()
            return

        # Frame for Desired Speed and PID Controls
        frame_controls = tk.Frame(master)
        frame_controls.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Frame for Desired Speed
        frame_speed = tk.Frame(frame_controls)
        frame_speed.pack(padx=10, pady=10, fill=tk.X)

        self.desired_speed_label = tk.Label(frame_speed, text="Desired Speed (RPM):", font=("Helvetica", 14))
        self.desired_speed_label.grid(row=0, column=0, padx=5, pady=5)

        self.desired_speed_entry = tk.Entry(frame_speed, font=("Helvetica", 14))
        self.desired_speed_entry.grid(row=0, column=1, padx=5, pady=5)

        # Frame for PID Controls
        frame_pid = tk.Frame(frame_controls)
        frame_pid.pack(padx=10, pady=10, fill=tk.X)

        self.kp_label = tk.Label(frame_pid, text="Kp:", font=("Helvetica", 14))
        self.kp_label.grid(row=1, column=0, padx=5, pady=5)

        self.kp_entry = tk.Entry(frame_pid, font=("Helvetica", 14))
        self.kp_entry.grid(row=1, column=1, padx=5, pady=5)

        self.ki_label = tk.Label(frame_pid, text="Ki:", font=("Helvetica", 14))
        self.ki_label.grid(row=2, column=0, padx=5, pady=5)

        self.ki_entry = tk.Entry(frame_pid, font=("Helvetica", 14))
        self.ki_entry.grid(row=2, column=1, padx=5, pady=5)

        self.kd_label = tk.Label(frame_pid, text="Kd:", font=("Helvetica", 14))
        self.kd_label.grid(row=3, column=0, padx=5, pady=5)

        self.kd_entry = tk.Entry(frame_pid, font=("Helvetica", 14))
        self.kd_entry.grid(row=3, column=1, padx=5, pady=5)

        # Start button
        self.start_button = tk.Button(frame_pid, text="Start", command=self.start_motor, font=("Helvetica", 14))
        self.start_button.grid(row=4, column=0, columnspan=2, padx=5, pady=10)

        # Frame for Direction Buttons
        frame_direction = tk.Frame(frame_controls)
        frame_direction.pack(padx=10, pady=10, fill=tk.X)

        self.forward_button = tk.Button(frame_direction, text="Forward", command=self.set_forward, font=("Helvetica", 14), width=10)
        self.forward_button.grid(row=0, column=0, padx=5, pady=5)

        self.reverse_button = tk.Button(frame_direction, text="Reverse", command=self.set_reverse, font=("Helvetica", 14), width=10)
        self.reverse_button.grid(row=0, column=1, padx=5, pady=5)

        self.stop_button = tk.Button(frame_direction, text="Stop", command=self.stop_motor, font=("Helvetica", 14), width=10)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)

        # Frame for Displaying Data
        frame_display = tk.Frame(frame_controls)
        frame_display.pack(padx=10, pady=10, fill=tk.X)

        self.output_speed_label = tk.Label(frame_display, text="Output Speed (RPM):", font=("Helvetica", 14))
        self.output_speed_label.grid(row=0, column=0, padx=5, pady=5)

        self.output_speed_value = tk.Label(frame_display, text="0.00000", font=("Helvetica", 14))
        self.output_speed_value.grid(row=0, column=1, padx=5, pady=5)

        self.error_label = tk.Label(frame_display, text="Error:", font=("Helvetica", 14))
        self.error_label.grid(row=1, column=0, padx=5, pady=5)

        self.error_value = tk.Label(frame_display, text="0.00000", font=("Helvetica", 14))
        self.error_value.grid(row=1, column=1, padx=5, pady=5)

        # Frame for Graph
        frame_graph = tk.Frame(master)
        frame_graph.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Motor Speed vs Desired Speed')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Speed (RPM)')
        self.line1, = self.ax.plot([], [], label='Output Speed')
        self.line2, = self.ax.plot([], [], label='Desired Speed')
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_graph)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.output_speed_data = []
        self.desired_speed_data = []
        self.time_data = []
        self.start_time = time.time()

        # Start a thread to read serial data
        self.reading_thread = threading.Thread(target=self.read_serial_data)
        self.reading_thread.daemon = True
        self.reading_thread.start()

    def start_motor(self):
        try:
            desired_speed = int(self.desired_speed_entry.get())
            kp_value = float(self.kp_entry.get())
            ki_value = float(self.ki_entry.get())
            kd_value = float(self.kd_entry.get())

            commands = [
                f"D{desired_speed}\n",
                f"KP{kp_value}\n",
                f"KI{ki_value}\n",
                f"KD{kd_value}\n"
            ]
            for command in commands:
                self.serial_conn.write(command.encode())
                time.sleep(0.1)  # Wait a bit between commands to ensure they are processed
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values for speed and PID constants.")

    def set_forward(self):
        command = "F\n"
        self.serial_conn.write(command.encode())

    def set_reverse(self):
        command = "R\n"
        self.serial_conn.write(command.encode())

    def stop_motor(self):
        command = "S\n"
        self.serial_conn.write(command.encode())
        self.reset_graph()  # Reset the graph data when the motor is stopped

    def read_serial_data(self):
        while True:
            if self.serial_conn.in_waiting > 0:
                data = self.serial_conn.readline().decode('utf-8').strip()
                if "Output Speed:" in data:
                    parts = data.split(", ")
                    output_speed_str = parts[0].split(": ")[1].replace(' RPM', '')
                    output_speed = round(float(output_speed_str) / 10.3, 5)  # Chỉ hiển thị 5 chữ số thập phân
                    desired_speed_entry_text = self.desired_speed_entry.get()

                    if desired_speed_entry_text:  # Kiểm tra xem người dùng đã nhập giá trị mong muốn chưa
                        desired_speed = float(desired_speed_entry_text)
                        error = round(desired_speed - output_speed, 5)  # Chỉ hiển thị 5 chữ số thập phân
                        self.error_value.config(text=f"{error:.5f}")  # Cập nhật giá trị lỗi với 5 chữ số thập phân
                    else:
                        self.error_value.config(text="N/A")

                    self.output_speed_value.config(text=f"{output_speed:.5f}")  # Cập nhật tốc độ đầu ra với 5 chữ số thập phân

                    self.update_graph(output_speed)

            time.sleep(0.1)

    def update_graph(self, output_speed):
        current_time = time.time() - self.start_time
        desired_speed = float(self.desired_speed_entry.get()) if self.desired_speed_entry.get() else 0

        self.time_data.append(current_time)
        self.output_speed_data.append(output_speed)
        self.desired_speed_data.append(desired_speed)

        self.line1.set_data(self.time_data, self.output_speed_data)
        self.line2.set_data(self.time_data, self.desired_speed_data)
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()

    def reset_graph(self):
        self.output_speed_data.clear()
        self.desired_speed_data.clear()
        self.time_data.clear()
        self.start_time = time.time()

        self.line1.set_data(self.time_data, self.output_speed_data)
        self.line2.set_data(self.time_data, self.desired_speed_data)
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()

    def on_closing(self):
        if self.serial_conn.is_open:
            self.serial_conn.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.geometry("1200x600")
    root.mainloop()
