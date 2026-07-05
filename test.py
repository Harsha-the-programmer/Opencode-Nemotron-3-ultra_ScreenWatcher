from log_monitor import LogMonitor
import time

monitor = LogMonitor()

while True:

    event = monitor.poll()

    if event:
        print(event)

    time.sleep(0.2)