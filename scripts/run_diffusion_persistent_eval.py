#!/usr/bin/env python3

import csv
import select
import sys
import time
from pathlib import Path

import lerobot.scripts.lerobot_rollout as lr
from lerobot.rollout.configs import RolloutConfig
from lerobot.rollout.strategies.core import send_next_action
from lerobot.utils.robot_utils import precise_sleep


TRIAL_DURATION = 40.0

RESULT_DIR = Path.home() / "diffusion_real_eval"
CSV_PATH = RESULT_DIR / "results.csv"

CONDITIONS = [
    ("nominal", 10),
    ("left_shift", 10),
    ("right_shift", 10),
]


def get_robot(ctx):
    return ctx.hardware.robot_wrapper.inner


def disable_robot_torque(ctx):
    try:
        get_robot(ctx).bus.disable_torque()
        print("\n[ROBOT] Torque OFF — you can move the arm by hand.")
    except Exception as e:
        print(f"\n[WARNING] Could not disable torque: {e}")


def enable_robot_torque(ctx):
    try:
        get_robot(ctx).bus.enable_torque()
        print("[ROBOT] Torque ON")
    except Exception as e:
        print(f"[WARNING] Could not enable torque: {e}")


def reset_trial_state(strategy):
    if strategy._engine is not None:
        strategy._engine.reset()

    if strategy._interpolator is not None:
        strategy._interpolator.reset()

    strategy._cached_obs_processed = None
    strategy._warmup_flushed = False


def run_trial(strategy, ctx):
    """
    Press s once to mark success.
    No ENTER is required.
    """
    import os
    import select
    import termios
    import tty

    engine = strategy._engine
    cfg = ctx.runtime.cfg
    robot = ctx.hardware.robot_wrapper
    interpolator = strategy._interpolator

    control_interval = interpolator.get_control_interval(cfg.fps)
    start_time = time.perf_counter()

    engine.resume()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    print()
    print("==========================================")
    print(" START")
    print(" Maximum duration: 40 seconds")
    print(" When SUCCESS condition is reached:")
    print(" >>> press s once <<<")
    print("==========================================")
    print()

    try:
        tty.setcbreak(fd)

        while not ctx.runtime.shutdown_event.is_set():

            # Check success key FIRST
            readable, _, _ = select.select([fd], [], [], 0)

            if readable:
                key = os.read(fd, 1).decode(errors="ignore").lower()

                if key == "s":
                    print()
                    print("==========================================")
                    print(" SUCCESS CONFIRMED")
                    print(" Ending this trial.")
                    print("==========================================")
                    return True

            # Then check timeout
            if (time.perf_counter() - start_time) >= TRIAL_DURATION:
                print()
                print("==========================================")
                print(" TIME UP — 40 seconds")
                print("==========================================")
                return False

            loop_start = time.perf_counter()

            obs = robot.get_observation()

            obs_processed = strategy._process_observation_and_notify(
                ctx.processors,
                obs,
            )

            if strategy._handle_warmup(
                cfg.use_torch_compile,
                loop_start,
                control_interval,
            ):
                continue

            action_dict = send_next_action(
                obs_processed,
                obs,
                ctx,
                interpolator,
            )

            strategy._log_telemetry(
                obs_processed,
                action_dict,
                ctx.runtime,
            )

            dt = time.perf_counter() - loop_start

            if (sleep_t := control_interval - dt) > 0:
                precise_sleep(sleep_t)

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings,
        )

def ask_result():
    print()
    print("Result:")
    print("  1 = success")
    print("  2 = grasp_failure")
    print("  3 = transport_failure")
    print("  4 = place_failure")
    print("  5 = other_failure")

    mapping = {
        "1": "success",
        "2": "grasp_failure",
        "3": "transport_failure",
        "4": "place_failure",
        "5": "other_failure",
    }

    while True:
        value = input("Choose [1-5]: ").strip()

        if value in mapping:
            return mapping[value]

        print("Please enter 1-5.")

def save_result(condition, trial, result, notes):
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "DiffusionPolicy",
            condition,
            trial,
            result,
            notes,
        ])


@lr.parser.wrap()
def persistent_eval(cfg: RolloutConfig):

    cfg.duration = TRIAL_DURATION
    cfg.return_to_initial_position = False
    cfg.display_data = False

    if cfg.strategy.type != "base":
        raise ValueError("Use --strategy.type=base")

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            csv.writer(f).writerow([
                "model",
                "condition",
                "trial",
                "result",
                "notes",
            ])

    lr.init_logging()

    signal_handler = lr.ProcessSignalHandler(
        use_threads=True,
        display_pid=False,
    )
    shutdown_event = signal_handler.shutdown_event

    print()
    print("==========================================")
    print(" Loading Diffusion Policy ONCE")
    print(
        " Inference denoising steps =",
        cfg.policy.num_inference_steps,
    )
    print("==========================================")

    ctx = lr.build_rollout_context(
        cfg,
        shutdown_event,
    )

    strategy = lr.create_strategy(cfg.strategy)

    try:
        strategy.setup(ctx)
        disable_robot_torque(ctx)

        print()
        print("==========================================")
        print(" DIFFUSION POLICY READY")
        print(" Model remains loaded.")
        print(" Maximum trial duration = 40 s")
        print(" press s = success")
        print("==========================================")

        for condition, num_trials in CONDITIONS:

            print()
            print("##########################################")
            print(f" PHASE: {condition}")
            print("##########################################")

            if condition == "nominal":
                print("Object: ORIGINAL / NOMINAL position")
            elif condition == "left_shift":
                print("Object: 3 cm LEFT from nominal")
            else:
                print("Object: 3 cm RIGHT from nominal")

            input("\nPress ENTER to enter this phase...")

            for trial in range(1, num_trials + 1):

                if shutdown_event.is_set():
                    return

                print()
                print("==========================================")
                print(" DIFFUSION REAL ROBOT EVALUATION")
                print(f" Condition : {condition}")
                print(f" Trial     : {trial}/{num_trials}")
                print(" Max time  : 40 s")
                print("==========================================")

                print()
                print("Torque OFF.")
                print("Reset robot pose and object.")

                input(
                    "\n>>> Press ENTER when READY <<< "
                )

                enable_robot_torque(ctx)
                reset_trial_state(strategy)

                success = run_trial(
                    strategy,
                    ctx,
                )

                if success:
                    result = "success"

                    print()
                    print("Result automatically recorded as SUCCESS.")

                    # Early success: release torque now
                    disable_robot_torque(ctx)

                else:
                    print()
                    print("==========================================")
                    print(" 40 s reached.")
                    print(" Judge the state BEFORE torque is released.")
                    print("==========================================")

                    # Keep torque ON while judging the exact 40 s state
                    result = ask_result()

                    # Release only AFTER judgment
                    disable_robot_torque(ctx)

                notes = input(
                    "Notes (ENTER if none): "
                ).strip()

                save_result(
                    condition,
                    trial,
                    result,
                    notes,
                )

                print(
                    f"Saved: DiffusionPolicy,"
                    f"{condition},{trial},{result},{notes}"
                )

        print()
        print("==========================================")
        print(" DIFFUSION EVALUATION COMPLETED")
        print("==========================================")
        print(f"Results: {CSV_PATH}")

    except KeyboardInterrupt:
        print("\nEmergency / evaluation interrupted.")

    finally:
        try:
            disable_robot_torque(ctx)
        except Exception:
            pass

        print("Stopping inference and disconnecting robot...")
        strategy.teardown(ctx)


if __name__ == "__main__":
    persistent_eval()
