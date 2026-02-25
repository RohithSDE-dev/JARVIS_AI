import time
import datetime
import psutil

class AutonomousBrain:
    def __init__(self, comm_engine):
        self.comm = comm_engine
        self.last_alerts = {
            "battery": 0,
            "temp": 0,
            "greeting": None
        }

    def monitor_environment(self, core):
        """The background loop that watches everything."""
        while True:
            now = datetime.datetime.now()

            # 1. Proactive Greeting (Once a day)
            today = now.strftime("%Y-%m-%d")
            if now.hour == 9 and self.last_alerts["greeting"] != today:
                core.speak(f"Good morning, Rohith. All systems are nominal. It is currently {now.strftime('%I:%M %p')}.")
                self.last_alerts["greeting"] = today

            # 2. Battery Monitoring
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                # Warning if low and not charging
                if percent < 20 and not battery.power_plugged:
                    if time.time() - self.last_alerts["battery"] > 600: # Alert every 10 mins
                        core.speak(f"Tactical warning: Battery is at {percent} percent. Please connect a power source.")
                        self.last_alerts["battery"] = time.time()

            # 3. CPU Temperature (Common in Linux/Mac; Windows may vary)
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    current_temp = temps['coretemp'][0].current
                    if current_temp > 80: # If hotter than 80°C
                        core.speak(f"Warning: CPU temperature is high at {current_temp} degrees.")
            except AttributeError:
                pass # Temperature reading not supported on this OS without Admin

            time.sleep(30) # Check every 30 seconds