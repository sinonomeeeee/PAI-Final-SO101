# SO-101実機タスクにおける3種類の模倣学習方策の比較検討

Physical AI応用1講座 最終課題

## 概要

本プロジェクトでは、SO-101ロボットアームを用いた物体移動タスクに対して、
以下の3種類の模倣学習方策を実装し、実機上で比較評価した。

- ACT (Action Chunking Transformer)
- Diffusion Policy
- SmolVLA

すべてのモデルについて、共通の40エピソードのデモンストレーションデータを使用した。

実機評価では、基準位置、左方向位置変更、右方向位置変更の3条件について、
各モデル30試行、合計90試行を実施し、成功率および失敗傾向を比較した。

## タスク

SO-101を用いて、机上に配置した消しゴムを指定された目標領域まで移動させる。

1試行の制限時間は40秒とし、
40秒以内に物体の50%以上が目標領域内に入った場合を成功と判定した。

物体の移動方法は把持・搬送に限定せず、
押し動作によって目標領域まで移動した場合も成功としている。

## デモンストレーションデータ

SO-101 Leaderを人間が操作し、
Followerを追従させるLeader-Follower方式で実機デモンストレーションを収集した。

- デモンストレーション数: 40エピソード
- 総フレーム数: 19,701
- カメラ: アーム搭載RGBカメラ
- 解像度: 640 x 480
- フレームレート: 30 fps
- 状態 / 行動: 各6次元
- タスク指示: Move the object to the target area

## 比較モデル

### ACT

40エピソードのデモンストレーションを使用して学習した。

- 学習ステップ数: 10,000
- 最終モデル: models/act/

### Diffusion Policy

ACTと同一の40エピソードを使用して学習した。

- 学習ステップ数: 20,000
- 最終モデル: models/diffusion_policy/
- 実機評価時のdenoising steps: 30

GTX 1070上での実機推論速度と軌道生成のバランスを考慮し、
最終評価では30 denoising stepsを使用した。

### SmolVLA

事前学習済みSmolVLAを基盤として、
同一の40エピソードを用いてLoRAファインチューニングを行った。

- 学習ステップ数: 20,000
- 最終LoRA adapter: models/smolvla/

SmolVLAについてはLoRA adapterのみを保存しているため、
実行時には対応する事前学習済みbase modelが必要となる。

## 実機評価

各モデルについて以下の30試行を実施した。

- 基準位置: 10試行
- 左方向位置変更: 10試行
- 右方向位置変更: 10試行

合計90試行で比較した。

### 成功率

| モデル | 基準位置 | 左方向位置変更 | 右方向位置変更 | 総合結果 |
| --- | ---: | ---: | ---: | ---: |
| ACT | 5/10 (50%) | 1/10 (10%) | 0/10 (0%) | 6/30 (20.0%) |
| Diffusion Policy | 7/10 (70%) | 1/10 (10%) | 3/10 (30%) | 11/30 (36.7%) |
| SmolVLA | 4/10 (40%) | 6/10 (60%) | 6/10 (60%) | 16/30 (53.3%) |

### 失敗内訳

| モデル | 把持失敗 | 搬送失敗 | 配置失敗 | その他 |
| --- | ---: | ---: | ---: | ---: |
| ACT | 22 | 1 | 1 | 0 |
| Diffusion Policy | 15 | 1 | 1 | 2 |
| SmolVLA | 12 | 2 | 0 | 0 |

ACTでは把持失敗が多く、特に物体位置を変更した条件で成功率が低下した。

Diffusion Policyは基準位置で最も高い成功率を示したが、
位置変更条件では成功率が低下した。

SmolVLAは位置変更条件において60%の成功率を維持し、
通常の把持・搬送だけでなく、
物体を押して目標領域まで移動させる成功例も確認された。

## 実機評価スクリプト

ACT:

    ./scripts/run_act_eval.sh

Diffusion Policy:

    python scripts/run_diffusion_persistent_eval.py [LeRobot rollout arguments]

SmolVLA:

    python scripts/run_smolvla_persistent_eval.py [LeRobot rollout arguments]

ロボットのシリアルポートおよびカメラデバイス番号は、
使用する環境に応じて変更する必要がある。

## ハードウェア・実行環境

- Robot: SO-101
- OS: Ubuntu 24.04.2 LTS
- CPU: Intel Core i7-8700 @ 3.20 GHz
- Memory: 8 GB
- GPU: NVIDIA GeForce GTX 1070 8 GB
- Inference device: CUDA
- Camera: Innomaker U20CAM-1080p-S1
- Camera input: 640 x 480 / 30 fps

## プロジェクト構成

    PAI-Final-SO101/
    ├── README.md
    ├── models/
    │   ├── act/
    │   ├── diffusion_policy/
    │   └── smolvla/
    ├── scripts/
    │   ├── record_40demo.sh
    │   ├── train_act.sh
    │   ├── train_smolvla.sh
    │   ├── run_act_eval.sh
    │   ├── run_diffusion_persistent_eval.py
    │   └── run_smolvla_persistent_eval.py
    ├── results/
    │   └── evaluation.md
    ├── transfer/
    ├── .gitattributes
    └── .gitignore

## Large Files

学習済みモデルおよび一部のデータファイルはGit LFSで管理している。

リポジトリをcloneする場合はGit LFSをインストールした上で、

    git lfs install
    git clone <repository-url>

を実行する。
