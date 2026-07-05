"""
actions.py

Desktop automation and email utilities for the
OpenCode Supervisor.
"""

import subprocess
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    WINDOW_TITLE,
    ESCAPE_PRESSES,
    ESCAPE_DELAY,
    TYPE_DELAY,
    EMAIL_ENABLED,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_TO,
    EMAIL_SUBJECT,
)


# ==========================================================
# Utility
# ==========================================================

def run(command):

    try:
        subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

    except Exception as e:
        print(e)


# ==========================================================
# Window Control
# ==========================================================

def focus_opencode():

    run([
        "hyprctl",
        "dispatch",
        "focuswindow",
        f"title:^{WINDOW_TITLE}$"
    ])

    time.sleep(0.5)


# ==========================================================
# Keyboard
# ==========================================================

def press_escape():

    run(["wtype", "-k", "Escape"])


def press_enter():

    run(["wtype", "-k", "Return"])


def press_escape_twice():

    for _ in range(ESCAPE_PRESSES):

        press_escape()

        time.sleep(ESCAPE_DELAY)


def type_text(text):

    try:

        subprocess.run(
            ["wtype", text],
            check=False
        )

    except Exception as e:

        print(e)


def send_prompt(prompt):

    focus_opencode()

    time.sleep(TYPE_DELAY)

    type_text(prompt)

    time.sleep(TYPE_DELAY)

    press_enter()


def abort_and_continue(prompt):

    focus_opencode()

    press_escape_twice()

    time.sleep(2)

    type_text(prompt)

    time.sleep(TYPE_DELAY)

    press_enter()


# ==========================================================
# Email
# ==========================================================

def send_email(subject, body):

    if not EMAIL_ENABLED:
        return

    try:

        msg = MIMEMultipart()

        msg["From"] = EMAIL_USERNAME
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.starttls()

        server.login(
            EMAIL_USERNAME,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_USERNAME,
            EMAIL_TO,
            msg.as_string()
        )

        server.quit()

        print("Email sent successfully.")

    except Exception as e:

        print("Email Error:", e)


def send_completion_email(supervisor):

    started = datetime.fromtimestamp(
        supervisor.start_time
    ).strftime("%d-%b-%Y %H:%M:%S")

    finished = datetime.fromtimestamp(
        supervisor.finish_time
    ).strftime("%d-%b-%Y %H:%M:%S")

    body = f"""
OpenCode Supervisor Report

==================================================

Task Status
-----------

✅ Completed Successfully


Session
-------

{supervisor.session}


Started
-------

{started}


Finished
--------

{finished}


Duration
--------

{supervisor.runtime_string()}


Recovery Summary
----------------

Worker Exhausted Recoveries

{supervisor.worker_retries}


Thinking Recoveries

{supervisor.stall_retries}


Completed Jobs

{supervisor.completed_jobs}


==================================================

Supervisor Status

The OpenCode Supervisor is still running and
waiting for the next task.

==================================================
"""

    send_email(
        EMAIL_SUBJECT,
        body
    )


# ==========================================================
# Debug
# ==========================================================

def notify(text):

    print(
        f"[Supervisor] {text}"
    )