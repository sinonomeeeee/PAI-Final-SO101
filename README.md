# SO-101を用いたACT模倣学習によるPick-and-Place

Physical AI応用1講座 最終課題

## 概要

本プロジェクトでは、SO-101ロボットアームを用いて、  
模倣学習による実機Pick-and-Placeタスクを実装した。

Leader-Follower方式による遠隔操作で実機デモンストレーションを収集し、  
LeRobotのACT（Action Chunking with Transformers）を用いて方策を学習した。

学習後はLeaderによる操作を行わず、  
アーム搭載カメラの画像とロボットの関節状態を入力として、  
SO-101 Followerが自律的にPick-and-Placeを実行する。

## タスク内容

使用したタスク指示は以下の通りである。

```text
pick up the object and place it on the target area
```

机上の物体を把持し、指定したターゲット領域まで移動して配置する  
Pick-and-Placeタスクを対象とした。

## システム構成

### ハードウェア

- SO-101 Leader
- SO-101 Follower
- アーム搭載USBカメラ
- Ubuntu PC
- NVIDIA GPU

### ソフトウェア

- LeRobot
- ACT（Action Chunking with Transformers）
- PyTorch
- OpenCV
- CUDA
- Git / GitHub

## デモンストレーションデータの収集

SO-101 Leaderを人間が操作し、その動作をSO-101 Followerに追従させる  
Leader-Follower方式で実機デモンストレーションを収集した。

データ収集にはLeRobotのrecording pipelineを使用した。

収集条件は以下の通りである。

- デモンストレーション数: 40エピソード
- カメラ解像度: 640 × 480
- データセットFPS: 30
- カメラ位置: ロボットアーム上
- タスク: Pick-and-Place

各エピソードでは、できるだけ一貫した初期状態から操作を開始し、  
物体を把持してターゲット領域へ配置するまでの一連の動作を記録した。

データ収集用スクリプト:

```bash
./scripts/record_40demo.sh
```

## ACTによる模倣学習

収集した40エピソードのデモンストレーションを用いて、  
ACT policyを学習した。

主な学習設定は以下の通りである。

- Policy: ACT
- デモンストレーション数: 40エピソード
- 学習ステップ数: 10,000
- バッチサイズ: 8
- 使用デバイス: CUDA

学習用スクリプト:

```bash
./scripts/train_act.sh
```

## 自律実行

学習後はLeaderを切り離し、  
SO-101 Follower単体で自律実行を行った。

推論時の入力として、

- アーム搭載カメラ画像
- ロボットの関節状態

を使用し、ACT policyがロボットのactionを生成する。

単一試行用スクリプト:

```bash
./scripts/rollout_single.sh
```

## 実機評価

学習済みpolicyを用いて10回の実機試行を実施した。

10回評価用スクリプト:

```bash
./scripts/rollout_eval_10ep.sh
```

### 評価結果

| 条件 | 試行回数 | 成功回数 | 成功率 |
| --- | ---: | ---: | ---: |
| 学習時と同様の条件 | 7 | 7 | 100% |
| 学習データに含まれない物体位置 | 2 | 0 | 0% |
| 物体を反転した条件（把持時に滑り） | 1 | 0 | 0% |
| 合計 | 10 | 7 | 70% |

学習時と同様の条件では、7試行すべてでPick-and-Placeに成功した。

一方、学習データに含まれていない物体位置では失敗し、  
物体を反転した試行では把持時に滑りが発生した。

この結果から、学習データに近い条件では安定した動作が可能である一方、  
未知位置や物体の物理的条件の変化に対する汎化性能には  
改善の余地があることが確認できた。

## プロジェクト構成

```text
PAI-Final-SO101/
├── README.md
├── scripts/
│   ├── record_40demo.sh
│   ├── train_act.sh
│   ├── rollout_single.sh
│   └── rollout_eval_10ep.sh
├── results/
│   └── evaluation.md
└── .gitignore
```

## 補足

データセット、学習済みモデルのcheckpoint、および提出用動画は、  
ファイルサイズの都合上、本GitHubリポジトリには含めていない。

本リポジトリには、  
データ収集、ACT学習、自律実行、および評価に使用した  
コードと実行スクリプトを収録している。
