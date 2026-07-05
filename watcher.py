"""
watcher.py

Main event loop for the OpenCode Supervisor.
"""

import time

from config import (
    RESOURCE_EXHAUSTED_WAIT,
    EXIT_LOOP_WAIT,
    STALL_WAIT,
    RESOURCE_PROMPT,
    STALL_PROMPT,
    RESOURCE_EXHAUSTED,
    PROCESS_STARTED,
    STREAM_STARTED,
    PROCESS_CANCELLED,
    PROCESS_ABORTED,
    EXIT_LOOP,
    LOOP,
)

from log_monitor import LogMonitor
from state_machine import Supervisor, SupervisorState

from actions import (
    send_prompt,
    abort_and_continue,
    send_completion_email,
    notify,
)


monitor = LogMonitor()
supervisor = Supervisor()


print("=" * 60)
print("OpenCode Supervisor Started")
print("=" * 60)


# -------------------------------------------------------
# Timers
# -------------------------------------------------------

resource_wait_until = None

exit_wait_until = None

stall_deadline = None


# -------------------------------------------------------
# Main Loop
# -------------------------------------------------------

while True:

    now = time.time()

    event = monitor.poll()

    if event:

        # Ignore unrelated sessions once we're tracking one
        if (
            supervisor.session is not None
            and
            event.session is not None
            and
            not supervisor.is_current_session(event.session)
        ):
            continue

        # ---------------------------------------------
        # PROCESS STARTED
        # ---------------------------------------------

        if event.event == PROCESS_STARTED:

            if supervisor.session is None:

                supervisor.start_session(
                    event.session
                )

            resource_wait_until = None

            supervisor.touch()

            stall_deadline = now + STALL_WAIT

            notify("PROCESS STARTED")

            continue

        # ---------------------------------------------
        # LOOP
        # ---------------------------------------------

        if event.event == LOOP:

            supervisor.touch()

            stall_deadline = now + STALL_WAIT

            if supervisor.state == SupervisorState.WAITING_EXIT:

                notify("Loop resumed.")

                supervisor.resume()

                exit_wait_until = None

            continue

        # ---------------------------------------------
        # STREAM
        # ---------------------------------------------

        if event.event == STREAM_STARTED:

            supervisor.touch()

            continue

        # ---------------------------------------------
        # RESOURCE EXHAUSTED
        # ---------------------------------------------

        if event.event == RESOURCE_EXHAUSTED:

            notify("Worker exhausted.")

            supervisor.worker_detected()

            resource_wait_until = (
                now +
                RESOURCE_EXHAUSTED_WAIT
            )

            continue

        # ---------------------------------------------
        # EXIT LOOP
        # ---------------------------------------------

        if event.event == EXIT_LOOP:

            notify("Exit loop.")

            supervisor.exit_detected()

            exit_wait_until = (
                now +
                EXIT_LOOP_WAIT
            )

            continue

        # ---------------------------------------------
        # USER CANCELLED
        # ---------------------------------------------

        if event.event == PROCESS_CANCELLED:

            notify("User cancelled.")

            supervisor.reset_session()

            exit_wait_until = None

            stall_deadline = None

            resource_wait_until = None

            continue

        # ---------------------------------------------
        # ABORTED
        # ---------------------------------------------

        if event.event == PROCESS_ABORTED:

            notify("Aborted.")

            continue

    # -------------------------------------------------------
    # Resource Retry Timer
    # -------------------------------------------------------

    if (
        resource_wait_until is not None
        and
        now >= resource_wait_until
    ):

        notify("Retrying after ResourceExhausted.")

        send_prompt(
            RESOURCE_PROMPT
        )

        # We just interacted with OpenCode,
        # so reset the activity timer.
        supervisor.touch()

        supervisor.resume()

        resource_wait_until = None

        stall_deadline = now + STALL_WAIT

    # -------------------------------------------------------
    # Completion Timer
    # -------------------------------------------------------

    if (
        exit_wait_until is not None
        and
        now >= exit_wait_until
    ):

        notify("Task completed.")

        supervisor.completed()

        send_completion_email(
            supervisor
        )

        supervisor.reset_session()

        exit_wait_until = None

        resource_wait_until = None

        stall_deadline = None

    # -------------------------------------------------------
    # Thinking Timeout
    # -------------------------------------------------------

    if (

        stall_deadline is not None

        and

        supervisor.state == SupervisorState.RUNNING

        and

        now >= stall_deadline

    ):

        notify("Thinking timeout detected.")

        supervisor.stall_detected()

        abort_and_continue(
            STALL_PROMPT
        )

        # We have just sent a new prompt.
        supervisor.touch()

        supervisor.resume()

        stall_deadline = now + STALL_WAIT

    # -------------------------------------------------------

    time.sleep(0.2)