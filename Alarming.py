import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
import time
import winsound
import darkdetect
import logging
import pickle
import os
import pystray
from PIL import Image, ImageDraw
from threading import Thread

# Setup logging
logging.basicConfig(filename="alarm_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

class AlarmClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Alarm Clock")
        self.root.geometry("550x700")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Set dark mode if system is in dark mode
        if darkdetect.isDark():
            self.set_dark_theme()

        # Alarm list
        self.alarms = []
        
        # Time selection
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="00")
        self.ampm_var = tk.StringVar(value="AM")
                
        self.duration_var = tk.IntVar(value=60)  # Duration in seconds
        self.recurring_var = tk.BooleanVar(value=False)
        self.days_vars = {day: tk.BooleanVar(value=False) for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        self.label_var = tk.StringVar(value="")
        self.ampm_var_color_fix = None

        ttk.Label(root, text="Set Alarm Time:", font=("Helvetica", 14)).pack(pady=10)

        time_frame = ttk.Frame(root)
        time_frame.pack(pady=5)

        self.hour_spin = ttk.Spinbox(time_frame, from_=1, to=12, textvariable=self.hour_var, width=5, format="%02.0f", font=("Helvetica", 12))
        self.hour_spin.pack(side="left", padx=5)
        ttk.Label(time_frame, text=":", font=("Helvetica", 14)).pack(side="left")
        self.minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f", font=("Helvetica", 12))
        self.minute_spin.pack(side="left", padx=5)
        self.ampm_spin = ttk.Spinbox(time_frame, values=("AM", "PM"), textvariable=self.ampm_var, width=5, font=("Helvetica", 12))
        self.ampm_spin.pack(side="left", padx=5)

        # Duration selection
        ttk.Label(root, text="Alarm Duration (seconds):", font=("Helvetica", 14)).pack(pady=10)
        self.duration_spin = ttk.Spinbox(root, from_=10, to=300, textvariable=self.duration_var, width=8, font=("Helvetica", 12))
        self.duration_spin.pack(pady=5)

        # Recurring Option
        ttk.Checkbutton(root, text="Recurring Alarm", variable=self.recurring_var, style="TCheckbutton").pack(pady=10)

        # Days of the Week Selection
        days_frame = ttk.Frame(root)
        days_frame.pack(pady=5)
        ttk.Label(days_frame, text="Days:", font=("Helvetica", 14)).pack(side="left")
        for day, var in self.days_vars.items():
            ttk.Checkbutton(days_frame, text=day, variable=var, style="TCheckbutton").pack(side="left", padx=5)

        # Label for Alarm
        ttk.Label(root, text="Alarm Label (optional):", font=("Helvetica", 14)).pack(pady=10)
        self.label_entry = ttk.Entry(root, textvariable=self.label_var, width=30)
        self.label_entry.pack(pady=5)

        # Set Alarm Button
        self.set_alarm_button = ttk.Button(root, text="Set Alarm", command=self.set_alarm)
        self.ampm_var_color_fix = self.ampm_spin.bind("<Configure>", self.update_combobox_color)
        self.set_alarm_button.pack(pady=10)

        # Alarms Frame
        self.alarms_frame = ttk.Frame(root)
        self.alarms_frame.pack(pady=10, fill="both", expand=True)

        # Alarm time and flags
        self.stop_alarm_flag = False

        # Load alarms after initializing UI components
        self.load_alarms()

        # Start checking alarms
        self.check_alarms()

    def set_dark_theme(self):
        style = ttk.Style()
        style.theme_use("clam")  # Use the 'clam' theme as a base
        style.configure("TCombobox", fieldbackground="#3e3e3e", foreground="#ffffff", arrowsize=20, selectbackground="#2e2e2e", selectforeground="#ffffff")
        style = ttk.Style()
        style.theme_use("clam")  # Use the 'clam' theme as a base
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("TButton", background="#555555", foreground="#ffffff")
        style.configure("TSpinbox", background="#3e3e3e", foreground="#ffffff", arrowsize=20, fieldbackground="#3e3e3e")
        style.configure("TCombobox", fieldbackground="#3e3e3e", foreground="#ffffff", arrowsize=20)
        style.configure("TCheckbutton", background="#2e2e2e", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#3e3e3e", foreground="#ffffff")
        style.map("TButton", background=[("active", "#444444")], foreground=[("active", "#ffffff")])
        self.root.configure(background="#2e2e2e")

    def set_alarm(self):
        # Clear label field after setting alarm
        
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            ampm = self.ampm_var.get()
        except ValueError:
            messagebox.showerror("Invalid Time", "Please enter a valid time.")
            return

        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

        now = datetime.now()
        alarm_time = datetime(now.year, now.month, now.day, hour, minute)

        # Set recurring days
        recurring_days = [day for day, var in self.days_vars.items() if var.get()]
        is_recurring = self.recurring_var.get() and recurring_days

        # If the set time is earlier than now and not recurring, set it for the next day
        if alarm_time <= now and not is_recurring:
            alarm_time += timedelta(days=1)

        # Store the alarm details
        alarm_details = {
            "time": alarm_time,
            "duration": self.duration_var.get(),
            "recurring_days": recurring_days,
            "is_recurring": is_recurring,
            "label": self.label_var.get(),
            "enabled": True
        }
        self.alarms.append(alarm_details)
        self.add_alarm_card(alarm_details)
        self.label_var.set("")
        logging.info(f"Alarm set for {alarm_time.strftime('%I:%M %p')} (Recurring: {', '.join(recurring_days) if is_recurring else 'No'})")
        self.save_alarms()

    def add_alarm_card(self, alarm):
        card_frame = ttk.Frame(self.alarms_frame, relief="raised", borderwidth=2)
        card_frame.pack(fill="x", padx=10, pady=5)

        alarm_time_str = alarm["time"].strftime('%I:%M %p')
        label = alarm["label"] if alarm["label"] else "No Label"
        recurring_info = f"Recurring: {', '.join(alarm['recurring_days']) if alarm['is_recurring'] else 'No'}"

        ttk.Label(card_frame, text=f"{alarm_time_str} - {label}", font=("Helvetica", 12)).pack(side="left", padx=10)
        ttk.Label(card_frame, text=recurring_info, font=("Helvetica", 10)).pack(side="left", padx=10)

        toggle_button = ttk.Checkbutton(card_frame, text="Enabled", variable=tk.BooleanVar(value=alarm["enabled"]), command=lambda: self.toggle_alarm(alarm))
        toggle_button.pack(side="right", padx=5)
        edit_button = ttk.Button(card_frame, text="Edit", command=lambda: self.edit_alarm(alarm))
        edit_button.pack(side="right", padx=5)
        delete_button = ttk.Button(card_frame, text="Delete", command=lambda: self.delete_alarm(alarm, card_frame))
        delete_button.pack(side="right", padx=5)

    def toggle_alarm(self, alarm):
        alarm["enabled"] = not alarm["enabled"]
        logging.info(f"Alarm {'enabled' if alarm['enabled'] else 'disabled'}: {alarm['time'].strftime('%I:%M %p')}")
        self.save_alarms()

    def edit_alarm(self, alarm):
        # Set the fields to the selected alarm details for editing
        self.hour_var.set(alarm["time"].strftime("%I"))
        self.minute_var.set(alarm["time"].strftime("%M"))
        self.ampm_var.set(alarm["time"].strftime("%p"))
        self.duration_var.set(alarm["duration"])
        self.recurring_var.set(alarm["is_recurring"])
        self.label_var.set(alarm["label"])
        for day in self.days_vars:
            self.days_vars[day].set(day in alarm["recurring_days"])

        # Remove the alarm to be updated later
        self.alarms.remove(alarm)
        self.update_alarms_display()
        self.save_alarms()

    def delete_alarm(self, alarm, card_frame):
        self.alarms.remove(alarm)
        card_frame.pack_forget()
        logging.info(f"Alarm deleted: {alarm['time'].strftime('%I:%M %p')}")
        self.save_alarms()

    def check_alarms(self):
        now = datetime.now()
        for alarm in self.alarms:
            if alarm["enabled"] and now >= alarm["time"]:
                if alarm["is_recurring"]:
                    current_day = now.strftime("%a")
                    if current_day in alarm["recurring_days"]:
                        logging.info(f"Alarm ringing for {current_day} at {now.strftime('%I:%M %p')}.")
                        self.ring_alarm(alarm)
                else:
                    logging.info(f"Alarm ringing at {now.strftime('%I:%M %p')}.")
                    self.ring_alarm(alarm)

        self.root.after(1000, self.check_alarms)  # Check again after 1 second

    def ring_alarm(self, alarm):
        self.stop_alarm_flag = False
        duration = alarm["duration"]
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_alarm_flag:
                logging.info("Alarm stopped manually.")
                break
            winsound.Beep(1000, 500)  # Beep at 1000 Hz for 500 ms
            time.sleep(0.5)
        if not self.stop_alarm_flag:
            logging.info("Alarm finished.")
            messagebox.showinfo("Alarm", "Alarm finished!")

        # Remove non-recurring alarms after they ring
        if not alarm["is_recurring"]:
            self.alarms.remove(alarm)
            self.update_alarms_display()
            self.save_alarms()

    def update_combobox_color(self, event=None):
        if self.ampm_var_color_fix:
            self.ampm_spin.configure(foreground="#ffffff", background="#3e3e3e")

    def update_alarms_display(self):
        # Clear all alarm cards and re-add them
        for widget in self.alarms_frame.winfo_children():
            widget.destroy()
        for alarm in self.alarms:
            self.add_alarm_card(alarm)

    def save_alarms(self):
        with open("alarms.pkl", "wb") as f:
            pickle.dump(self.alarms, f)

    def load_alarms(self):
        if os.path.exists("alarms.pkl"):
            with open("alarms.pkl", "rb") as f:
                self.alarms = pickle.load(f)
            self.update_alarms_display()

    def hide_window(self):
        self.root.withdraw()
        self.show_tray_icon()

    def show_tray_icon(self):
        # Create a simple tray icon with a recognizable symbol
        image = Image.new('RGB', (64, 64), (0, 0, 0))  # Use black as the base color
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), fill=(255, 215, 0))  # Draw a yellow circle as a simple icon

        # Define the tray icon and its actions
        icon = pystray.Icon("alarm_clock", image, menu=pystray.Menu(
            pystray.MenuItem("Show", self.show_from_tray),
            pystray.MenuItem("Quit", self.quit_app)
        ), left_click=self.show_from_tray)

        # Start the tray icon in a separate thread
        Thread(target=icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        self.root.deiconify()
        icon.stop()

    def quit_app(self, icon, item):
        self.save_alarms()
        icon.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmClock(root)
    root.mainloop()