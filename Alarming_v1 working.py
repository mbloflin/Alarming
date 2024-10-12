import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
import time
import winsound
import darkdetect
import logging

# Setup logging
logging.basicConfig(filename="alarm_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

class AlarmClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Alarm Clock")
        self.root.geometry("500x600")

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

        ttk.Label(root, text="Set Alarm Time:", font=("Helvetica", 14)).pack(pady=15)

        time_frame = ttk.Frame(root)
        time_frame.pack(pady=10)

        self.hour_spin = ttk.Spinbox(time_frame, from_=1, to=12, textvariable=self.hour_var, width=5, format="%02.0f", font=("Helvetica", 12))
        self.hour_spin.pack(side="left", padx=5)
        ttk.Label(time_frame, text=":", font=("Helvetica", 14)).pack(side="left")
        self.minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f", font=("Helvetica", 12))
        self.minute_spin.pack(side="left", padx=5)
        self.ampm_spin = ttk.Combobox(time_frame, textvariable=self.ampm_var, values=["AM", "PM"], width=5, font=("Helvetica", 12), state="readonly")
        self.ampm_spin.pack(side="left", padx=5)

        # Duration selection
        ttk.Label(root, text="Alarm Duration (seconds):", font=("Helvetica", 14)).pack(pady=10)
        self.duration_spin = ttk.Spinbox(root, from_=10, to=300, textvariable=self.duration_var, width=8, font=("Helvetica", 12))
        self.duration_spin.pack(pady=5)

        # Recurring Option
        ttk.Checkbutton(root, text="Recurring Alarm", variable=self.recurring_var, style="TCheckbutton").pack(pady=10)

        # Days of the Week Selection
        days_frame = ttk.Frame(root)
        days_frame.pack(pady=10)
        ttk.Label(days_frame, text="Days:", font=("Helvetica", 14)).pack(side="left")
        for day, var in self.days_vars.items():
            ttk.Checkbutton(days_frame, text=day, variable=var, style="TCheckbutton").pack(side="left", padx=5)

        # Set Alarm Button
        self.set_alarm_button = ttk.Button(root, text="Set Alarm", command=self.set_alarm)
        self.set_alarm_button.pack(pady=20)

        # Stop Alarm Button
        self.stop_alarm_button = ttk.Button(root, text="Stop All Alarms", command=self.stop_all_alarms, state="disabled")
        self.stop_alarm_button.pack(pady=10)

        # Alarms Listbox
        ttk.Label(root, text="Scheduled Alarms:", font=("Helvetica", 14)).pack(pady=10)
        self.alarm_listbox = tk.Listbox(root, width=50, height=10)
        self.alarm_listbox.pack(pady=10)

        # Alarm time and flags
        self.stop_alarm_flag = False

    def set_dark_theme(self):
        style = ttk.Style()
        style.theme_use("clam")  # Use the 'clam' theme as a base
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("TButton", background="#555555", foreground="#ffffff")
        style.configure("TSpinbox", background="#3e3e3e", foreground="#ffffff", arrowsize=20, fieldbackground="#3e3e3e")
        style.configure("TCombobox", fieldbackground="#3e3e3e", foreground="#ffffff", arrowsize=20)
        style.configure("TCheckbutton", background="#2e2e2e", foreground="#ffffff")
        style.map("TButton", background=[("active", "#444444")], foreground=[("active", "#ffffff")])
        self.root.configure(background="#2e2e2e")

    def set_alarm(self):
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
            "is_recurring": is_recurring
        }
        self.alarms.append(alarm_details)
        self.alarm_listbox.insert(tk.END, f"Alarm set for {alarm_time.strftime('%I:%M %p')} (Recurring: {', '.join(recurring_days) if is_recurring else 'No'})")
        logging.info(f"Alarm set for {alarm_time.strftime('%I:%M %p')} (Recurring: {', '.join(recurring_days) if is_recurring else 'No'})")

        # Start checking for the alarm
        self.check_alarms()

    def check_alarms(self):
        now = datetime.now()
        for alarm in self.alarms:
            alarm_time = alarm["time"]
            recurring_days = alarm["recurring_days"]
            is_recurring = alarm["is_recurring"]

            if now >= alarm_time:
                if is_recurring:
                    current_day = now.strftime("%a")
                    if current_day in recurring_days:
                        logging.info(f"Alarm ringing for {current_day} at {now.strftime('%I:%M %p')}.")
                        self.ring_alarm(alarm)
                else:
                    logging.info(f"Alarm ringing at {now.strftime('%I:%M %p')}.")
                    self.ring_alarm(alarm)

        self.root.after(1000, self.check_alarms)  # Check again after 1 second

    def ring_alarm(self, alarm):
        self.stop_alarm_flag = False
        self.stop_alarm_button.config(state="normal")
        duration = alarm["duration"]
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_alarm_flag:
                logging.info("Alarm stopped manually.")
                break
            winsound.Beep(1000, 500)  # Beep at 1000 Hz for 500 ms
            time.sleep(0.5)
        self.stop_alarm_button.config(state="disabled")
        if not self.stop_alarm_flag:
            logging.info("Alarm finished.")
            messagebox.showinfo("Alarm", "Alarm finished!")

        # Remove non-recurring alarms after they ring
        if not alarm["is_recurring"]:
            self.alarms.remove(alarm)
            self.update_alarm_listbox()

    def stop_all_alarms(self):
        self.stop_alarm_flag = True
        self.stop_alarm_button.config(state="disabled")
        logging.info("All alarms stopped manually.")

    def update_alarm_listbox(self):
        self.alarm_listbox.delete(0, tk.END)
        for alarm in self.alarms:
            alarm_time = alarm["time"]
            recurring_days = alarm["recurring_days"]
            is_recurring = alarm["is_recurring"]
            self.alarm_listbox.insert(tk.END, f"Alarm set for {alarm_time.strftime('%I:%M %p')} (Recurring: {', '.join(recurring_days) if is_recurring else 'No'})")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmClock(root)
    root.mainloop()