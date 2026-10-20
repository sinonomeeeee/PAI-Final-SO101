#!/usr/bin/env python3

import csv
from pathlib import Path

import lerobot.scripts.lerobot_rollout as lr
from lerobot.rollout.configs import RolloutConfig


TRIAL_DURATION = 40.0

RESULT_DIR = Path.home() / "vla_real_eval"
CSV_PATH = RESULT_DIR / "results.csv"

CONDITIONS = [
    ("nominal", 10),
    ("left_shift", 10),
    ("right_shift", 10),
]


def reset_trial_state(strategy):
    """
    Clear policy/inference temporal state between trials
    without unloading the model or disconnecting the robot.
    """
    if strategy._engine is not None:
        strategy._engine.reset()

    if strategy._interpolator is not None:
        strategy._interpolator.reset()

    strategy._cached_obs_processed = None
    strategy._warmup_flushed = False


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
            "SmolVLA",
            condition,
            trial,
            result,
            notes,
        ])


@lr.parser.wrap()
def persistent_eval(cfg: RolloutConfig):

    # -----------------------------------------
    # Force evaluation settings
    # -----------------------------------------
    cfg.duration = TRIAL_DURATION
    cfg.return_to_initial_position = False
    cfg.display_data = False

    if cfg.strategy.type != "base":
        raise ValueError(
            "This evaluator must use --strategy.type=base"
        )

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
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
    print(" Loading SmolVLA ONCE")
    print(" Please wait...")
    print("==========================================")
    print()

    # Heavy part happens only here
    ctx = lr.build_rollout_context(
        cfg,
        shutdown_event,
    )

    strategy = lr.create_strategy(cfg.strategy)

    try:
        # Starts inference engine once
        strategy.setup(ctx)

        print()
        print("==========================================")
        print(" SmolVLA READY")
        print(" Model will remain loaded for all trials.")
        print(" Each trial = 40 seconds.")
        print("==========================================")

        for condition, num_trials in CONDITIONS:

            print()
            print("##########################################")
            print(f" PHASE: {condition}")
            print(f" Trials: {num_trials}")
            print("##########################################")

            if condition == "nominal":
                print("Object: ORIGINAL / NOMINAL position")
            elif condition == "left_shift":
                print("Object: LEFT-shifted position")
            elif condition == "right_shift":
                print("Object: RIGHT-shifted position")

            input("\nPress ENTER to enter this phase...")

            for trial in range(1, num_trials + 1):

                if shutdown_event.is_set():
                    print("Shutdown requested.")
                    return

                print()
                print("==========================================")
                print(" SMOLVLA REAL ROBOT EVALUATION")
                print(f" Condition : {condition}")
                print(f" Trial     : {trial}/{num_trials}")
                print(f" Duration  : {TRIAL_DURATION:.0f} s")
                print("==========================================")

                print()
                print("Reposition the object / reset the scene now.")
                print("The robot will NOT move until you press ENTER.")

                input("\n>>> Press ENTER to START the 40-second trial <<< ")

                # Important:
                # clear previous action chunk / temporal state,
                # but DO NOT reload SmolVLA.
                reset_trial_state(strategy)

                print()
                print("==========================================")
                print(" START")
                print(" 40-second evaluation window begins NOW")
                print("==========================================")
                print()

                # BaseStrategy.run() creates a fresh timer internally.
                strategy.run(ctx)

                print()
                print("==========================================")
                print(" TIME UP — 40 seconds")
                print(" Judge task completion NOW.")
                print("==========================================")

                result = ask_result()

                notes = input(
                    "Notes (ENTER if none): "
                ).strip()

                save_result(
                    condition,
                    trial,
                    result,
                    notes,
                )

                print()
                print(
                    f"Saved: SmolVLA,{condition},"
                    f"{trial},{result},{notes}"
                )

                if trial < num_trials:
                    print()
                    print("------------------------------------------")
                    print("Preparation time.")
                    print("Reset the scene / reposition the object.")
                    print("There is NO countdown during this period.")
                    print("------------------------------------------")

        print()
        print("==========================================")
        print(" SMOLVLA EVALUATION COMPLETED")
        print("==========================================")
        print(f"Results: {CSV_PATH}")

    except KeyboardInterrupt:
        print()
        print("Interrupted by user.")

    finally:
        print()
        print("Stopping inference and disconnecting robot...")
        strategy.teardown(ctx)


if __name__ == "__main__":
    persistent_eval()
