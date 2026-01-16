# Phase 3: 統計ダッシュボードとエクスポート機能

## 概要

タスクの統計情報を可視化し、様々な形式でエクスポートする機能を実装します。

## 実装機能

### 3.1 統計ダッシュボード（CLI版）

**コマンド**: `ai-task-manager stats`

**表示内容**:
- タスク総数（全体・ステータス別・優先度別）
- 完了率（全体・カテゴリ別）
- 期限超過タスク数
- 今週・今月の進捗サマリー
- カテゴリ別タスク分布
- タグ別タスク分布
- 優先度別の進捗状況

**表示例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 AI Task Manager - 統計ダッシュボード
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 全体サマリー
─────────────────────────────────────────────────
  総タスク数       : 45 件
  完了タスク       : 28 件 (62.2%)
  進行中           : 12 件 (26.7%)
  未着手           : 4 件 (8.9%)
  キャンセル       : 1 件 (2.2%)

⚠️  期限超過       : 3 件

📅 今週の進捗
─────────────────────────────────────────────────
  新規作成         : 8 件
  完了             : 5 件
  進捗率           : 62.5%

📅 今月の進捗
─────────────────────────────────────────────────
  新規作成         : 23 件
  完了             : 15 件
  進捗率           : 65.2%

🏷️  カテゴリ別統計
─────────────────────────────────────────────────
  Work             : 25 件 (完了: 15, 進行中: 8, 未着手: 2)
  Personal         : 12 件 (完了: 8, 進行中: 3, 未着手: 1)
  Study            : 8 件 (完了: 5, 進行中: 1, 未着手: 2)

⭐ 優先度別統計
─────────────────────────────────────────────────
  高               : 10 件 (完了: 7, 残り: 3)
  中               : 28 件 (完了: 18, 残り: 10)
  低               : 7 件 (完了: 3, 残り: 4)

🏷️  タグ別統計
─────────────────────────────────────────────────
  urgent           : 8 件
  planning         : 12 件
  coding           : 15 件
```

**オプション**:
- `--category <name>`: 特定カテゴリに絞る
- `--period <week|month|year>`: 期間を指定
- `--json`: JSON形式で出力

---

### 3.2 HTMLダッシュボード（Chart.js）

**コマンド**: `ai-task-manager dashboard`

**生成内容**:
- インタラクティブなHTMLダッシュボード
- Chart.jsによるグラフ可視化
- リアルタイムフィルタリング

**グラフの種類**:
1. **ドーナツチャート**: ステータス別タスク分布
2. **横棒グラフ**: カテゴリ別タスク数
3. **折れ線グラフ**: 週次・月次の完了推移
4. **円グラフ**: 優先度別分布

**機能**:
- レスポンシブデザイン
- ダークモード対応
- データのエクスポート（JSON, CSV）
- プリント最適化

**オプション**:
- `--output <path>`: 出力先（デフォルト: dashboard.html）
- `--open`: 生成後にブラウザで開く
- `--theme <light|dark>`: テーマ指定

---

### 3.3 エクスポート機能

#### 3.3.1 PNG出力

**コマンド**: `ai-task-manager export png`

**機能**:
- ガントチャートのPNG出力
- Playwright/Puppeteerを使用してHTMLをレンダリング
- 高解像度出力対応

**オプション**:
- `--range <YYYY-MM>`: 表示期間
- `--output <path>`: 出力先
- `--width <px>`: 画像幅（デフォルト: 1920）
- `--height <px>`: 画像高さ（デフォルト: 1080）

#### 3.3.2 CSV出力

**コマンド**: `ai-task-manager export csv`

**機能**:
- タスクデータをCSV形式でエクスポート
- Excel対応（BOM付きUTF-8）

**カラム**:
```
ID,タイトル,説明,カテゴリ,優先度,ステータス,進捗率,開始日,期限,完了日,親タスクID,タグ,作成日,更新日
```

**オプション**:
- `--output <path>`: 出力先
- `--category <name>`: カテゴリフィルタ
- `--status <status>`: ステータスフィルタ

#### 3.3.3 PDF出力（オプション）

**コマンド**: `ai-task-manager export pdf`

**機能**:
- ガントチャートのPDF出力
- WeasyPrint/Playwright使用
- A4横向き、高品質出力

**オプション**:
- `--range <YYYY-MM>`: 表示期間
- `--output <path>`: 出力先
- `--paper-size <A4|A3|Letter>`: 用紙サイズ

---

### 3.4 設定ファイルサポート

**ファイル**: `~/.ai-task-manager/config.yaml` または `./config.yaml`

**設定項目**:
```yaml
# データベース設定
database:
  path: ./data/tasks.db

# デフォルト表示設定
display:
  default_category: null
  default_priority: medium
  date_format: "%Y-%m-%d"
  timezone: Asia/Tokyo

# ガントチャート設定
gantt:
  default_width: 80
  default_range: current_month
  auto_open_browser: false
  html_output_dir: ./output

# ダッシュボード設定
dashboard:
  theme: light
  auto_refresh: false
  default_period: month

# エクスポート設定
export:
  png_width: 1920
  png_height: 1080
  csv_encoding: utf-8-sig  # Excel対応
  pdf_paper_size: A4

# 通知設定（Phase 4用）
notifications:
  enabled: false
  deadline_warning_days: 3
```

**読み込み優先順位**:
1. `./config.yaml`（プロジェクトローカル）
2. `~/.ai-task-manager/config.yaml`（ユーザーグローバル）
3. デフォルト値

**実装**:
- PyYAMLを使用
- バリデーション機能
- 設定ファイル生成コマンド: `ai-task-manager init-config`

---

## ファイル構成

```
ai_task_manager/
├── commands/
│   ├── stats.py           # 統計コマンド
│   ├── dashboard.py       # ダッシュボードコマンド
│   └── export.py          # エクスポートコマンド
├── visualization/
│   ├── statistics.py      # 統計計算ロジック
│   └── templates/
│       └── dashboard.html # ダッシュボードテンプレート
├── exporters/
│   ├── csv_exporter.py    # CSV出力
│   ├── png_exporter.py    # PNG出力
│   └── pdf_exporter.py    # PDF出力
├── config.py              # 設定ファイル読み込み
└── utils/
    └── config_validator.py # 設定バリデーション
```

---

## 依存関係追加

```txt
# requirements.txt に追加
pyyaml>=6.0
```

```txt
# requirements-dev.txt に追加（オプション）
playwright>=1.40.0  # PNG/PDF出力用
weasyprint>=60.0    # PDF出力用（代替）
```

---

## 実装順序

1. **統計計算ロジック** (`visualization/statistics.py`)
   - データベースから統計情報を取得
   - 集計関数の実装

2. **CLI統計コマンド** (`commands/stats.py`)
   - ASCII表示での統計情報出力
   - JSON出力対応

3. **CSV エクスポート** (`exporters/csv_exporter.py`)
   - シンプルで依存関係なし
   - Excel対応

4. **設定ファイルサポート** (`config.py`)
   - YAML読み込み
   - バリデーション

5. **HTMLダッシュボード** (`commands/dashboard.py`, `templates/dashboard.html`)
   - Chart.js統合
   - インタラクティブなUI

6. **PNG/PDF エクスポート** (`exporters/png_exporter.py`, `pdf_exporter.py`)
   - Playwrightまたはその他のツール使用
   - オプション機能（依存関係が重い）

---

## テスト方法

```bash
# 統計表示
python3 -m ai_task_manager.cli stats

# 統計をJSON出力
python3 -m ai_task_manager.cli stats --json

# ダッシュボード生成
python3 -m ai_task_manager.cli dashboard --open

# CSV エクスポート
python3 -m ai_task_manager.cli export csv --output tasks.csv

# 設定ファイル生成
python3 -m ai_task_manager.cli init-config

# 設定ファイル確認
cat ~/.ai-task-manager/config.yaml
```

---

## 完了目標

- 実装時間: 6-8時間
- 優先度: 中
- 依存: Phase 1, Phase 2完了
