#!/usr/bin/env bash
set -e

cd ~/robot_ws/lerobot
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot-so101

DATASET_DIR=$(ls -dt ./data/so101_dataset_v2_40demo_* | head -n 1)
DATASET_NAME=$(basename "$DATASET_DIR")

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --policy.input_features=null \
  --policy.output_features=null \
  --dataset.repo_id="local/$DATASET_NAME" \
  --dataset.root="$DATASET_DIR" \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --output_dir=outputs/train/smolvla_so101_40demo_v2 \
  --job_name=smolvla_so101_40demo_v2 \
  --steps=20000 \
  --batch_size=1 \
  --num_workers=2 \
  --save_freq=2000 \
  --policy.optimizer_lr=1e-3 \
  --policy.scheduler_decay_lr=1e-4 \
  --peft.method_type=LORA \
  --peft.r=16 \
  --peft.lora_alpha=16 \
  --wandb.enable=true
