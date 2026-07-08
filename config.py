"""
============================================================
OpenCode Supervisor Configuration
============================================================
Modify this file to change prompts, timeouts or email settings.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# OpenCode
# ==========================================================

# OpenCode log file
LOG_FILE = (
    Path.home()
    / ".local"
    / "share"
    / "opencode"
    / "log"
    / "opencode.log"
)

# Hyprland window title
#WINDOW_TITLE = "OpenCode"
WINDOW_TITLE = r"^OC \|"

# ==========================================================
# Timers (seconds)
# ==========================================================

# Poll log file every 200ms
POLL_INTERVAL = 0.2

# Wait after ResourceExhausted before retrying
RESOURCE_EXHAUSTED_WAIT = 150

# Wait after "exiting loop"
# If no request activity occurs during this period,
# assume the task has completed.
EXIT_LOOP_WAIT = 300      # 5 minutes

# Maximum inactivity allowed for the active message.
# If exceeded, assume the model is stuck thinking.
STALL_WAIT = 900          # 15 minutes

# Prevent duplicate retries
RETRY_COOLDOWN = 60

# ==========================================================
# Recovery Prompts
# ==========================================================

RESOURCE_PROMPT = (
    "The previous session stopped because of a worker request "
    "limit. Continue exactly from where you stopped. "
    "Do not restart or repeat previous work."
)

STALL_PROMPT = (
    "The previous response appeared to be stuck thinking for "
    "a long time. I manually stopped it. Continue exactly "
    "from where you stopped. Do not restart or repeat previous work."
)

# ==========================================================
# Keyboard behaviour
# ==========================================================

# Number of Escape key presses before sending STALL_PROMPT
ESCAPE_PRESSES = 2

ESCAPE_DELAY = 0.5

TYPE_DELAY = 0.2

# ==========================================================
# Email Notification
# ==========================================================

EMAIL_ENABLED = True

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

EMAIL_TO = os.getenv("EMAIL_TO")

EMAIL_SUBJECT = "✅ OpenCode Task Completed"

# ==========================================================
# Internal Event Names
# ==========================================================

RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"

PROCESS_STARTED = "PROCESS_STARTED"

STREAM_STARTED = "STREAM_STARTED"

EXIT_LOOP = "EXIT_LOOP"

PROCESS_CANCELLED = "PROCESS_CANCELLED"

PROCESS_ABORTED = "PROCESS_ABORTED"

# ==========================================================
# Additional Events
# ==========================================================

LOOP = "LOOP"

# ==========================================================
# Log Messages
# ==========================================================

RESOURCE_KEYWORD = "ResourceExhausted"

EXIT_LOOP_KEYWORD = 'message="exiting loop"'

PROCESS_KEYWORD = "message=process"

STREAM_KEYWORD = "message=stream"

ABORT_KEYWORD = "error=Aborted"

CANCEL_KEYWORD = "message=cancel"

# These messages are ignored when checking whether
# the current request is making progress.
IGNORED_MESSAGES = {
    "cleanup",
    "tracking",
    "formatting",
    "touching file",
    "evaluated",
    "loading",
    "bootstrapping",
    "init",
    "creating instance",
    "watcher backend",
    "project copy refresh started",
    "project copy refresh done",
    "booting location services",
    "shell tool using shell",
    "all LSPs are disabled",
    "all formatters are disabled",
    "created",
    "fromDirectory",
}

# ==========================================================
# Debug
# ==========================================================

DEBUG = True