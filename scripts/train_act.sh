#!/usr/bin/env bash
set -e

cd ~/robot_ws/lerobot
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot-so101

DATASET_DIR=$(ls -dt ./data/so101_dataset_v2_40demo_* | head -n 1)
DATASET_NAME=$(basename "$DATASET_DIR")

echo "Dataset: $DATASET_DIR"

lerobot-train \
  --dataset.repo_id="local/$DATASET_NAME" \
  --dataset.root="$DATASET_DIR" \
  --policy.type=act \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --output_dir=outputs/train/act_so101_40demo_v2 \
  --job_name=act_so101_40demo_v2 \
  --steps=10000 \
  --batch_size=8 \
  --num_workers=4 \
  --save_freq=2000 \
  --wandb.enable=false
