#!/usr/bin/env bash
set -e

cd ~/robot_ws/lerobot
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot-so101

POLICY="outputs/train/act_so101_40demo_v2/checkpoints/010000/pretrained_model"

read -p "Press Enter when the scene is ready..."

lerobot-rollout \
  --strategy.type=base \
  --policy.path="$POLICY" \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so101_follower \
  --robot.cameras="{arm: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --task="pick up the object and place it on the target area" \
  --device=cuda \
  --fps=30 \
  --display_data=false \
  --return_to_initial_position=false
