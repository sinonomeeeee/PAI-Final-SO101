#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY="$REPO_ROOT/models/act"

RESULT_DIR="$HOME/act_real_eval"
CSV="$RESULT_DIR/results.csv"

mkdir -p "$RESULT_DIR"

if [ ! -f "$CSV" ]; then
    echo "model,condition,trial,result,notes" > "$CSV"
fi

run_trial () {
    CONDITION="$1"
    TRIAL="$2"

    echo
    echo "======================================"
    echo " ACT REAL ROBOT EVALUATION"
    echo " Condition : $CONDITION"
    echo " Trial     : $TRIAL"
    echo " Duration  : 40 s"
    echo "======================================"
    echo

    case "$CONDITION" in
        nominal)
            echo "Setup: object at ORIGINAL / NOMINAL position."
            ;;
        left_shift)
            echo "Setup: move object 3 cm to the LEFT from nominal."
            ;;
        right_shift)
            echo "Setup: move object 3 cm to the RIGHT from nominal."
            ;;
    esac

    echo
    echo "Reposition the object now."
    read -p "Press ENTER when everything is ready..."

    echo
    echo "Starting 40-second rollout..."
    echo

    lerobot-rollout \
        --strategy.type=base \
        --policy.path="$POLICY" \
        --robot.type=so101_follower \
        --robot.port=/dev/ttyACM0 \
        --robot.id=so101_follower \
        --robot.cameras="{arm: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}" \
        --task="pick up the object and place it on the target area" \
        --duration=40 \
        --device=cuda \
        --fps=30 \
        --display_data=false \
        --return_to_initial_position=false

    echo
    echo "Result:"
    echo "  1 = success"
    echo "  2 = grasp_failure"
    echo "  3 = transport_failure"
    echo "  4 = place_failure"
    echo "  5 = other_failure"

    while true; do
        read -p "Choose [1-5]: " R

        case "$R" in
            1) RESULT="success"; break ;;
            2) RESULT="grasp_failure"; break ;;
            3) RESULT="transport_failure"; break ;;
            4) RESULT="place_failure"; break ;;
            5) RESULT="other_failure"; break ;;
            *) echo "Please enter 1-5." ;;
        esac
    done

    read -p "Notes (ENTER if none): " NOTES
    NOTES=$(echo "$NOTES" | tr ',' ';')

    echo "ACT,$CONDITION,$TRIAL,$RESULT,$NOTES" >> "$CSV"

    echo
    echo "Saved:"
    tail -1 "$CSV"

    echo
    echo "--------------------------------------"
    echo "Next trial preparation"
    echo "Reposition the object and reset the scene."
    echo "The next trial will NOT start until you press ENTER."
    echo "--------------------------------------"
}

echo
echo "======================================"
echo " PHASE 1: NOMINAL x10"
echo "======================================"

for i in $(seq 1 10); do
    run_trial "nominal" "$i"
done

echo
echo "======================================"
echo " PHASE 2: LEFT SHIFT x10"
echo " Move object 3 cm LEFT"
echo "======================================"
read -p "Press ENTER when ready to start LEFT trials..."

for i in $(seq 1 10); do
    run_trial "left_shift" "$i"
done

echo
echo "======================================"
echo " PHASE 3: RIGHT SHIFT x10"
echo " Move object 3 cm RIGHT"
echo "======================================"
read -p "Press ENTER when ready to start RIGHT trials..."

for i in $(seq 1 10); do
    run_trial "right_shift" "$i"
done

echo
echo "======================================"
echo " ACT evaluation completed"
echo "======================================"
echo "Results:"
echo "$CSV"
