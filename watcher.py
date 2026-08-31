"""
watcher.py

Main event loop for the OpenCode Supervisor.
"""

import time

from config import (
    RESOURCE_EXHAUSTED_WAIT,
    EXIT_LOOP_WAIT,
    #STALL_WAIT,
    RESOURCE_PROMPT,
    STALL_PROMPT,
    RESOURCE_EXHAUSTED,
    PROCESS_STARTED,
    STREAM_STARTED,
    PROCESS_CANCELLED,
    PROCESS_ABORTED,
    EXIT_LOOP,
    LOOP,
    THINKING_TIMEOUT,
    THINKING_VERIFY_WAIT,
    THINKING_HARD_TIMEOUT,
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

#stall_deadline = None

thinking_started_at = None
thinking_long = False
thinking_hard_timeout_at = None
thinking_verifying = False
thinking_verify_until = None


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

            thinking_started_at = None
            thinking_long = False
            thinking_hard_timeout_at = None
            thinking_verifying = False
            thinking_verify_until = None

            if supervisor.session is None:

                supervisor.start_session(
                    event.session
                )

            resource_wait_until = None
            exit_wait_until = None

            supervisor.touch()

#            stall_deadline = now + STALL_WAIT

            notify("PROCESS STARTED")

            continue

        # ---------------------------------------------
        # LOOP
        # ---------------------------------------------

        if event.event == LOOP:

            supervisor.touch()

            #stall_deadline = now + STALL_WAIT

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

            thinking_started_at = now
            thinking_long = False
            thinking_hard_timeout_at = (
                now + THINKING_HARD_TIMEOUT
            )
            thinking_verifying = False
            thinking_verify_until = None

            continue

        # ---------------------------------------------
        # RESOURCE EXHAUSTED
        # ---------------------------------------------

        if event.event == RESOURCE_EXHAUSTED:

            # Already waiting to retry this failure.
            if resource_wait_until is not None:
                continue

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

            # If the model has been thinking for 5+ minutes,
            # verify whether OpenCode actually continues.
            if (
                thinking_started_at is not None
                and
                thinking_long
            ):

                thinking_verifying = True

                thinking_verify_until = (
                    now + THINKING_VERIFY_WAIT
                )

                notify(
                    "Long thinking ended. "
                    "Starting 2-minute verification."
                )

            supervisor.exit_detected()

            if thinking_long:

                # Delay normal completion handling while we verify
                # whether OpenCode starts another process.
                exit_wait_until = None

            else:

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

            #stall_deadline = None

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

 #       stall_deadline = now + STALL_WAIT

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

        #stall_deadline = None

    # -------------------------------------------------------
    # Thinking Timeout
    # -------------------------------------------------------

    if (
        thinking_started_at is not None
    ):

        thinking_elapsed = (
            now - thinking_started_at
        )

        # ---------------------------------------------------
        # 5-minute threshold
        # ---------------------------------------------------

        if (
            not thinking_long
            and
            thinking_elapsed >= THINKING_TIMEOUT
        ):

            thinking_long = True

            notify(
                "Thinking exceeded 5 minutes."
            )

        # ---------------------------------------------------
        # 8-minute hard timeout
        # ---------------------------------------------------

        if (
            thinking_hard_timeout_at is not None
            and
            now >= thinking_hard_timeout_at
            and
            not thinking_verifying
        ):

            notify(
                "Thinking exceeded 8 minutes. "
                "Timeout confirmed."
            )

            supervisor.stall_detected()

            supervisor.resume()

            abort_and_continue(
                STALL_PROMPT
            )

            supervisor.touch()

            thinking_started_at = None
            thinking_long = False
            thinking_hard_timeout_at = None
            thinking_verifying = False
            thinking_verify_until = None
            exit_wait_until = None

        # ---------------------------------------------------
        # 2-minute verification after EXIT_LOOP
        # ---------------------------------------------------

        elif (
            thinking_verifying
            and
            thinking_verify_until is not None
            and
            now >= thinking_verify_until
        ):

            notify(
                "No new process after EXIT_LOOP. "
                "Thinking timeout confirmed."
            )

            supervisor.stall_detected()

            abort_and_continue(
                STALL_PROMPT
            )

            supervisor.touch()

            supervisor.resume()

            thinking_started_at = None
            thinking_long = False
            thinking_hard_timeout_at = None
            thinking_verifying = False
            thinking_verify_until = None

    # -------------------------------------------------------

    time.sleep(0.2)