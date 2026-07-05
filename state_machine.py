"""
state_machine.py

State manager for the OpenCode Supervisor.
"""

import time
from enum import Enum, auto


class SupervisorState(Enum):
    IDLE = auto()
    RUNNING = auto()
    WAITING_RESOURCE = auto()
    WAITING_EXIT = auto()
    WAITING_STALL = auto()


class Supervisor:

    def __init__(self):

        self.reset_all()

    # =====================================================
    # Complete Reset
    # =====================================================

    def reset_all(self):

        self.finish_time = None

        self.state = SupervisorState.IDLE

        self.session = None

        self.start_time = None

        self.last_activity = None

        self.exit_time = None

        self.worker_retries = 0

        self.stall_retries = 0

        self.completed_jobs = 0

        self.email_sent = False

    # =====================================================
    # New Session
    # =====================================================

    def start_session(self, session):

        # Ignore if already supervising another session

        if self.session is not None:

            return

        self.session = session

        self.state = SupervisorState.RUNNING

        self.start_time = time.time()

        self.last_activity = time.time()

        self.email_sent = False

        print(f"[Supervisor] Tracking session {session}")

    # =====================================================
    # Ignore other sessions
    # =====================================================

    def is_current_session(self, session):

        if self.session is None:

            return False

        return session == self.session

    # =====================================================
    # Activity
    # =====================================================

    def touch(self):

        self.last_activity = time.time()

    # =====================================================
    # Worker Exhausted
    # =====================================================

    def worker_detected(self):

        self.state = SupervisorState.WAITING_RESOURCE

        self.worker_retries += 1

    # =====================================================
    # Exit Loop
    # =====================================================

    def exit_detected(self):

        self.state = SupervisorState.WAITING_EXIT

        self.exit_time = time.time()

    # =====================================================
    # Thinking Stall
    # =====================================================

    def stall_detected(self):

        self.state = SupervisorState.WAITING_STALL

        self.stall_retries += 1

    # =====================================================
    # Continue
    # =====================================================

    def resume(self):

        self.state = SupervisorState.RUNNING

        self.touch()

    # =====================================================
    # Runtime
    # =====================================================

    def runtime_seconds(self):

        if self.start_time is None:
            return 0

        if self.finish_time is not None:
            return int(self.finish_time - self.start_time)

        return int(time.time() - self.start_time)

    def runtime_string(self):

        total = self.runtime_seconds()

        h = total // 3600

        m = (total % 3600) // 60

        s = total % 60

        return f"{h}h {m}m {s}s"

    # =====================================================
    # Completion
    # =====================================================

    def completed(self):
        
        self.finish_time = time.time()

        self.completed_jobs += 1

        self.email_sent = True

    # =====================================================
    # Ready for next task
    # =====================================================

    def reset_session(self):

        self.session = None

        self.state = SupervisorState.IDLE

        self.start_time = None

        self.last_activity = None

        self.exit_time = None

        self.worker_retries = 0

        self.stall_retries = 0

        self.email_sent = False

        self.finish_time = None

    # =====================================================
    # Debug
    # =====================================================

    def __str__(self):

        return f"""
================ Supervisor ================

State          : {self.state.name}

Session        : {self.session}

Runtime        : {self.runtime_string()}

Worker Retry   : {self.worker_retries}

Thinking Retry : {self.stall_retries}

Completed Jobs : {self.completed_jobs}

============================================
"""