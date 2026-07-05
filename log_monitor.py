"""
log_monitor.py

Non-blocking OpenCode log monitor.
"""

import re
from config import *


class LogEvent:

    def __init__(
        self,
        event,
        session=None,
        timestamp=None,
        raw=""
    ):

        self.event = event
        self.session = session
        self.timestamp = timestamp
        self.raw = raw

    def __repr__(self):

        return f"<{self.event} session={self.session}>"



class LogMonitor:

    SESSION_REGEX = re.compile(r"session\.id=([^\s]+)")
    TIMESTAMP_REGEX = re.compile(r"timestamp=([^\s]+)")

    def __init__(self):

        self.file = open(
            LOG_FILE,
            "r",
            encoding="utf-8",
            errors="ignore"
        )

        # Ignore previous logs
        self.file.seek(0, 2)

    # -------------------------------------------------

    def extract(self, regex, line):

        m = regex.search(line)

        if m:
            return m.group(1)

        return None

    # -------------------------------------------------

    def parse(self, line):

        session = self.extract(
            self.SESSION_REGEX,
            line
        )

        timestamp = self.extract(
            self.TIMESTAMP_REGEX,
            line
        )

        # Ignore startup noise
        lower = line.lower()

        for item in IGNORED_MESSAGES:

            if item.lower() in lower:

                return None

        if RESOURCE_KEYWORD in line:

            return LogEvent(
                RESOURCE_EXHAUSTED,
                session,
                timestamp,
                line
            )

        if EXIT_LOOP_KEYWORD in line:

            return LogEvent(
                EXIT_LOOP,
                session,
                timestamp,
                line
            )

        if "message=loop" in line:

            return LogEvent(
                LOOP,
                session,
                timestamp,
                line
            )

        if PROCESS_KEYWORD in line:

            return LogEvent(
                PROCESS_STARTED,
                session,
                timestamp,
                line
            )

        if STREAM_KEYWORD in line:

            return LogEvent(
                STREAM_STARTED,
                session,
                timestamp,
                line
            )

        if CANCEL_KEYWORD in line:

            return LogEvent(
                PROCESS_CANCELLED,
                session,
                timestamp,
                line
            )

        if ABORT_KEYWORD in line:

            return LogEvent(
                PROCESS_ABORTED,
                session,
                timestamp,
                line
            )

        return None

    # -------------------------------------------------

    def poll(self):

        line = self.file.readline()

        if not line:

            # clear EOF flag
            self.file.seek(self.file.tell())

            return None

        return self.parse(line)

    # -------------------------------------------------

    def close(self):

        self.file.close()