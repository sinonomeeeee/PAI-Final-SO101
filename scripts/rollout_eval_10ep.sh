#!/usr/bin/env bash
set -e

cd ~/robot_ws/lerobot
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot-so101

POLICY="outputs/train/act_so101_40demo_v2/checkpoints/010000/pretrained_model"
RUN="rollout_so101_eval_10ep_$(date +%Y%m%d_%H%M%S)"

lerobot-rollout \
  --strategy.type=episodic \
  --policy.path="$POLICY" \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so101_follower \
  --robot.cameras="{arm: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --dataset.repo_id="local/$RUN" \
  --dataset.root="./data/$RUN" \
  --dataset.num_episodes=10 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=3600 \
  --dataset.single_task="pick up the object and place it on the target area" \
  --dataset.fps=30 \
  --dataset.push_to_hub=false \
  --device=cuda \
  --fps=30 \
  --display_data=false
