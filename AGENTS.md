# Framed - AI Agent Development Guide

## What (何)
iOS App Store用スクリーンショット自動生成ツール。XCUITestの実行、画像抽出、デバイスフレーム合成、テキスト追加を一括処理します。

## Why (なぜ)
iOSアプリのスクリーンショット生成プロセスを自動化し、`.xcresult`ファイルからの直接抽出、デバイスフレーム合成、リサイズ処理を単一のワークフローで効率的に行うため。Pillowを使用した高精度の画像処理を提供します。

## Tech Stack (技術スタック)
- **言語**: Python 3.10+
- **主要ライブラリ**: 
  - Pillow (画像処理)
  - PyYAML (設定管理)
  - Click (CLIフレームワーク)
- **外部ツール**: 
  - xcrun xcresulttool (画像抽出、Xcode 16.2+は`--legacy`フラグ必須)
  - xcodebuild (UITest実行)

## Project Structure (プロジェクト構造)
```
framed/
├── src/framed/
│   ├── api.py         # テンプレートインターフェース定義
│   ├── runner.py      # オーケストレーション (xcodebuild実行、ステータスバー設定)
│   ├── extractor.py   # .xcresultからの画像抽出
│   ├── processor.py   # フレーム合成・テキスト追加（テンプレート委譲）
│   ├── config.py      # YAML設定読み込み
│   ├── simctl.py      # Simulator制御ユーティリティ
│   └── templates/
│       └── standard/  # 標準テンプレート（フォルダ管理）
│           ├── __init__.py  # StandardTemplateクラス
│           └── sample.png   # サンプル出力画像
├── resources/
│   └── bezel.png      # iPhoneベゼル画像（透過PNG）
├── README.md          # ユーザー向けドキュメント
└── AGENTS.md          # このファイル（開発者/AI向け）
```

## Core Principles (開発原則)

### 0. テンプレートシステム
レイアウトロジックを `Template` インターフェースとして抽象化し、各テンプレートはフォルダで管理します：

- **api.py**: `Template` 抽象基底クラスを定義
- **templates/standard/**: 標準「テキスト上部 + デバイス下部」レイアウト
  - `__init__.py`: `StandardTemplate` クラス実装
  - `template.yaml`: デフォルト設定（色、フォントサイズなど）
  - `sample.png`: サンプル出力画像（**必須**）
- **templates/panoramic/**: パノラマ背景「連続波形 + テキスト + デバイス」レイアウト
  - `__init__.py`: `PanoramicTemplate` クラス実装
  - `template.yaml`: デフォルト設定（`panoramic_color` など）
  - `sample.png`: サンプル出力画像（**必須**）

**重要**: 新しいテンプレートを追加する際は、必ず `sample.png` と `template.yaml` を含めてください。
`template.yaml` に定義された値は、ユーザーの `framed.yaml` 設定がない場合のデフォルト値として使用されます。

### 0.5. ステータスバー固定化
`runner.py` でテスト実行前に以下を実行：
1. `xcrun simctl boot "デバイス名"` でシミュレータを明示的に起動
2. `xcrun simctl status_bar "デバイス名" override --time "9:41" ...` で設定

この順序により、プロジェクトの Scheme ファイルを変更せずにステータスバーを制御できます。

### 1. レイアウト定数
以下のパラメータレイアウト基準として使用します：

```python
# Layout Constants
CANVAS_WIDTH = 1350          # 作業用キャンバス幅
CANVAS_HEIGHT = 2868         # 作業用キャンバス高さ
SCREENSHOT_WIDTH = 1206      # スクリーンショット幅
SCREENSHOT_HEIGHT = 2622     # スクリーンショット高さ
HEADER_MARGIN = 200          # 上部余白
LINE_SPACING = 30            # 行間
CAPTION_SPACING = 60         # タイトルとサブタイトルの間隔
PHONE_TOP_OFFSET = 150       # テキスト終了後のデバイス配置オフセット
APP_STORE_SIZE = (1290, 2796)  # 最終出力サイズ (iPhone 15 Pro Max 6.7")
```

### 2. .xcresult トラバーサルロジック
`xcresulttool` で以下の階層を正確に辿ります：

```
.xcresult
└─ actions -> _values
   └─ actionResult -> testsRef -> id -> _value
      └─ testableSummaries -> _values
         └─ tests -> _values
            └─ summaryRef -> id -> _value
               └─ activitySummaries -> _values
                  └─ attachments -> _values
                     └─ payloadRef -> id -> _value (ここをexport)
```

**重要な実装ポイント**:
- `actionResult`は直接`testsRef`を持つ（`id`を持たない）
- `xcresulttool get object`と`export`の両方に`--legacy`フラグが必要
- `export`コマンド: `xcrun xcresulttool export --legacy --path <xcresult> --id <payload_ref> --output-path <out> --type file`

### 3. 画像処理パイプライン
`Processor._process_image()` は以下の順序で処理：

1. **スクリーンショットリサイズ**: 元画像 → 1206x2622
2. **ベゼル合成**:
   - スクリーンショットに角丸マスク適用（`radius=80`）
   - ベゼル中央にスクリーンショットを配置
   - ベゼルを上から重ねる（Dynamic Island等を正しく表示）
3. **テキスト描画**:
   - 設定されたフォント（`framed.yaml`参照）またはヒラギノフォント
   - 中央揃え、行ごとにY座標を加算
4. **デバイス配置**: 
   - テキスト終了位置 + 150px
   - 収まらない場合は自動縮小
5. **最終リサイズ**: 1350x2868 → **1290x2796** (App Store標準)
## Configuration Hierarchy (設定の優先順位)

設定値は以下の順序で解決されます（上が優先）：

1.  **個別スクリーンショット設定** (`framed.yaml` の `screenshots` セクション)
2.  **プロジェクト共通設定** (`framed.yaml` のルート `template_settings` セクション)
3.  **テンプレートデフォルト** (`templates/NAME/template.yaml`)
4.  **ハードコードされたフォールバック** (ソースコード内)

※ 詳しい設定方法やコマンドの使い方は [README.md](README.md) を参照してください。

### 4. フォント処理
`framed.yaml` でフォントを指定可能：
```yaml
config:
  font_bold: "/path/to/BoldFont.ttf"
  font_regular: "/path/to/RegularFont.ttf"
```
未指定時のデフォルト（macOS）:
- タイトル: `/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc` (95pt)
- サブタイトル: `/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc` (45pt)

## When Making Changes (変更時の注意)

### 新規追加が許可される場面
- 新しいデバイスサイズのサポート（iPad等）
- 多言語対応の拡張（中国語、韓国語等）
- 追加の画像効果（影、グラデーション、背景パターン等）
- パノラマ背景の追加

### 避けるべきこと
❌ レイアウト定数の無用な変更
❌ ハードコードされた数値の変更（必ず定数化してクラス変数に）
❌ デバッグプリントの残置（本番コードには不要）

## Testing & Verification (テストと検証)

### 品質確認の基準
新しく生成された画像は、以下の品質を満たす必要があります：
- サイズ: 1290 x 2796 (iPhone 6.7インチ用)
- テキストとデバイスがバランスよく配置されていること
- ベゼルの角丸処理が正しく行われていること

### 検証コマンド例
```bash
# 1. 生成
cd /path/to/your/project
framed run

# 2. サイズ確認
sips -g pixelWidth -g pixelHeight \
  screenshots_framed/framed/iPhone\ 17_ja/*.png
```

## Common Patterns (よくあるパターン)

### スクリーンショット名のマッピング
```swift
// UITest code
attachment.name = "inbox"  // ← この名前が重要
```

```yaml
# framed.yaml
screenshots:
  "inbox":  # ← UITestの名前と一致させる
    title:
      ja: "ふたりの距離が\n近くなる"
```

## Architecture Notes (アーキテクチャノート)

### Runner (オーケストレーション)
- `xcodebuild test`の実行
- `.xcresult`の一時ディレクトリ管理
- Extractor → Processorの順次実行

### Extractor (画像抽出)
- `.xcresult`のJSON構造トラバース
- `xcresulttool`コマンドの実行
- デバイス・言語ごとのディレクトリ作成

### Processor (画像加工)
- ベゼル合成（PIL/Pillowベース）
- フォント描画（Configurable）
- App Store標準サイズへのリサイズ

## Additional Resources (追加リソース)

- **ユーザー向けREADME**: `README.md`
- **テンプレート作成ガイド**: `TEMPLATES.md`
- **パッケージングガイド**: `docs/PACKAGING.md`
- **Pillow Documentation**: https://pillow.readthedocs.io/
