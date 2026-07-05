from pathlib import Path
import subprocess
import threading
import time

LOG = Path.home() / ".local/share/opencode/log/opencode.log"

RESOURCE_WAIT = 90
STALL_WAIT = 60

RESOURCE_PROMPT = (
    "The previous session stopped because of a worker request limit. "
    "Just continue from where you stopped. "
    "Do not start from the beginning."
)

STALL_PROMPT = (
    "The previous response appears to have stalled. "
    "Continue exactly from where you stopped. "
    "Do not restart or repeat previous work."
)

last_activity = time.time()

waiting_for_exit = False
resource_cooldown = False


def focus_opencode():
    subprocess.run(
        ["hyprctl", "dispatch", "focuswindow", "title:^OpenCode$"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def send_prompt(prompt):
    print("Sending prompt...")

    focus_opencode()

    time.sleep(0.4)

    subprocess.run(["wtype", prompt])

    time.sleep(0.2)

    subprocess.run(["wtype", "-k", "Return"])


def handle_resource():
    global resource_cooldown

    if resource_cooldown:
        return

    resource_cooldown = True

    print("ResourceExhausted detected.")

    time.sleep(RESOURCE_WAIT)

    send_prompt(RESOURCE_PROMPT)

    time.sleep(30)

    resource_cooldown = False


def wait_after_exit():
    global waiting_for_exit
    global last_activity

    start = last_activity

    print("Waiting for more logs...")

    time.sleep(STALL_WAIT)

    if last_activity == start:
        print("No activity. Assuming stalled.")
        send_prompt(STALL_PROMPT)
    else:
        print("Activity resumed.")

    waiting_for_exit = False


print("Watching OpenCode log...")

with open(LOG, "r") as f:

    f.seek(0, 2)

    while True:

        line = f.readline()

        if not line:
            time.sleep(0.2)
            continue

        last_activity = time.time()

        print(line.strip())

        if "ResourceExhausted" in line:
            threading.Thread(
                target=handle_resource,
                daemon=True
            ).start()

        elif 'message="exiting loop"' in line:

            if not waiting_for_exit:
                waiting_for_exit = True

                threading.Thread(
                    target=wait_after_exit,
                    daemon=True
                ).start()