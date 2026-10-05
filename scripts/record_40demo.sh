#!/usr/bin/env bash
set -e

cd ~/robot_ws/lerobot

source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot-so101

RUN="so101_dataset_v2_40demo_$(date +%Y%m%d_%H%M%S)"

echo "========================================"
echo " SO-101 Imitation Learning Data Capture"
echo "========================================"
echo "Follower : /dev/ttyACM0"
echo "Leader   : /dev/ttyACM1"
echo "Camera   : /dev/video0"
echo "Dataset  : ./data/$RUN"
echo
echo "Recording:"
echo "  n / Right Arrow = finish successful episode"
echo "  r / Left Arrow  = discard and rerecord episode"
echo "  q / Esc         = quit"
echo
echo "Reset phase:"
echo "  n / Right Arrow = start next episode"
echo

read -p "Press Enter when the first scene is ready..."

python -c '
import time

from lerobot.motors.feetech.feetech import FeetechMotorsBus

# The SO-101 Leader used in this project contains motors
# with mixed firmware versions.
FeetechMotorsBus._assert_same_firmware = lambda self: None

original_sync_read = FeetechMotorsBus._sync_read

def leader_sequential_sync_read(
    self,
    addr,
    length,
    motor_ids,
    *,
    num_retry=0,
    raise_on_error=True,
    err_msg="",
):
    # Keep the standard sync-read implementation for the Follower.
    if self.port != "/dev/ttyACM1":
        return original_sync_read(
            self,
            addr,
            length,
            motor_ids,
            num_retry=num_retry,
            raise_on_error=raise_on_error,
            err_msg=err_msg,
        )

    # Sequential reads are used for the Leader because group sync-read
    # was unstable with the mixed motor firmware configuration.
    values = {}
    last_comm = 0

    for motor_id in motor_ids:
        value = None

        for _ in range(10):
            raw, comm, error = self._read(
                addr,
                length,
                motor_id,
                num_retry=0,
                raise_on_error=False,
            )

            last_comm = comm

            if comm == 0 and error == 0:
                value = raw
                break

            time.sleep(0.002)

        if value is None:
            raise ConnectionError(
                f"Leader ID{motor_id} failed sequential read after 10 attempts"
            )

        values[motor_id] = value
        time.sleep(0.001)

    return values, last_comm

FeetechMotorsBus._sync_read = leader_sequential_sync_read

from lerobot.scripts.lerobot_record import main
main()
' \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so101_follower \
  --robot.cameras="{arm: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader \
  --dataset.repo_id="local/$RUN" \
  --dataset.root="./data/$RUN" \
  --dataset.num_episodes=40 \
  --dataset.episode_time_s=300 \
  --dataset.reset_time_s=3600 \
  --dataset.fps=30 \
  --dataset.single_task="pick up the object and place it on the target area" \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2 \
  --dataset.push_to_hub=false \
  --display_data=false
