# Framed

**Framed** は、iOSアプリのApp Store用スクリーンショット作成を完全に自動化するコマンドラインツールです。
XCUITestの実行から画像抽出、デバイスフレーム合成、テキスト追加まで、一括で処理します。

## ✨ 特徴

*   **完全自動化**: テスト実行 → 画像抽出 → フレーム合成 → テキスト追加を1コマンドで完了
*   **`.xcresult` ネイティブ**: `xcodebuild` が生成するテスト結果バンドルを直接解析し、劣化のないPNGを抽出
*   **ステータスバー固定化**: シミュレータのステータスバーを「9:41」に自動設定（プロジェクトファイル変更不要）
*   **名前ベース設定**: SwiftUI / XCUITest コード内で指定した `attachment.name` をキーに、YAMLで各画面の設定を管理
*   **App Store標準出力**: iPhone 15 Pro Max (6.7") 形式 (1290x2796) で自動出力
*   **テンプレートシステム**: 複数のレイアウトスタイルに対応可能な拡張可能アーキテクチャ
*   **グローバル設定上書き**: プロジェクト共通の設定（色、フォント等）を一括管理し、個別画面のみ上書き可能
*   **クリーン**: 中間ファイル（`.xcresult`）を一時ディレクトリで処理し、プロジェクトを汚さない

## 🚀 インストール

```bash
# リポジトリのルートで
pip install -e .
```

## 💻 コマンド一覧

| コマンド | 説明 |
| --- | --- |
| `framed init` | 初期化（`framed.yaml` のひな形作成） |
| `framed run` | スクリーンショット生成の全工程を実行 |
| `framed list-templates` | 利用可能なテンプレート一覧を表示 |
| `framed template-help` | テンプレートごとの設定項目を表示 |
| `framed generate-samples` | 全テンプレートのサンプル画像を生成 |

### サンプル画像の生成

テンプレートのサンプル画像を生成するには `generate-samples` コマンドを使用します。

```bash
# 全テンプレートのサンプルを生成
framed generate-samples

# 特定のテンプレートのみ生成
framed generate-samples --template cascade
```

## 📖 使い方

### 1. UITestコードの準備

UITest内で、スクリーンショットを撮りたいタイミングに `XCTAttachment` を追加し、**識別可能な名前** を付けます。

```swift
func testCaptureInbox() {
    let app = XCUIApplication()
    app.launchArguments = ["--debug-inbox"]
    app.launch()
    
    sleep(2) // 画面が安定するまで待機
    
    // スクリーンショット撮影
    let screenshot = XCUIScreen.main.screenshot()
    let attachment = XCTAttachment(screenshot: screenshot)
    
    // ★重要: この名前が framed.yaml のキーと一致する必要があります
    attachment.name = "inbox"
    
    attachment.lifetime = .keepAlways
    add(attachment)
}
```

### 2. 設定ファイルの作成 (`framed.yaml`)

プロジェクトルートに `framed.yaml` を作成し、プロジェクト設定と各画面のメタデータを定義します。

```yaml
# テンプレート設定（ルートレベル）
template: "panoramic"
template_settings:
  panoramic_color: "#E5E5EA" # プロジェクト全体でパノラマ背景色を統一
  text_color: "#000000"

# 基本設定
config:
  output_dir: "docs/screenshots_framed"
  project: "MyApp.xcodeproj"
  scheme: "MyApp-UITests"

devices:
  - name: "iPhone 17"

languages:
  - ja
  - en

screenshots:
  "inbox":  # XCUITest で指定した attachment.name と一致
    # 個別設定（必要な場合のみ上書き）
    title:
      ja: "ふたりの距離が\n近くなる"
      en: "Stay close\nwith your loved one"
    subtitle:
      ja: "離れていても相手の今日がわかる"
      en: "Know each other's day"
  
  "home_empty":
    title:
      ja: "1日3問\n声で答えるだけ"
      en: "Just 3 questions daily\nwith your voice"
    subtitle:
      ja: "質問があるから迷わない"
      en: "Guided by questions"
```

### 3. 設定の確認
利用可能なテンプレート一覧を表示するには：
```bash
framed list-templates
```

テンプレートごとの利用可能な設定（`template_settings`）を確認するには：

```bash
framed template-help --name panoramic
```

### 4. デバイスベゼルの配置

iPhoneのベゼル画像（透過PNG）を `resources/bezel.png` に配置します。
標準的なiPhoneフレーム画像を使用してください。

### 5. 実行

```bash
framed run
```

実行後、以下のように出力されます:

```text
docs/screenshots_framed/
  raw/
    iPhone 17_ja/
      inbox.png
      home_empty.png
      ...
  framed/
    iPhone 17_ja/
      inbox.png      # ← デバイスフレーム + テキスト合成済み (1290x2796)
      home_empty.png
      ...
```

`framed/` ディレクトリの画像がApp Storeへアップロード可能な最終成果物です。

## 🛠️ 仕組み

### 1. Capture (テスト実行)

#### ステータスバー設定
テスト実行前に、以下の処理を自動実行します：
1. **シミュレータを明示的に起動** (`simctl boot "デバイス名"`)
2. **ステータスバーをオーバーライド** (`simctl status_bar override --time "9:41"`)

これにより、プロジェクトの Scheme ファイルを変更することなく、全てのスクリーンショットで時刻が「9:41」に固定されます。

#### テスト実行
`xcodebuild test` を実行し、XCUITestを動かしながらスクリーンショットを含んだ `.xcresult` バンドルを一時ディレクトリに生成します。

### 2. Extract (画像抽出)
`xcresulttool` を使用してバンドル内部を探索し、以下の階層を辿ります:

```
.xcresult
  └─ actions
      └─ actionResult
          └─ testsRef
              └─ testableSummaries
                  └─ tests (test groups)
                      └─ summaryRef
                          └─ activitySummaries
                              └─ attachments  # ← ここから画像を export
```

`XCTAttachment` に付けられた `name` をファイル名として、PNGをエクスポートします。

### 3. Process (フレーム合成・テキスト追加)

抽出された画像に対して、以下の処理を行います:

1. **スクリーンショットのリサイズ**: 1206 x 2622 に統一
2. **ベゼル合成**: 
   - ベゼル画像（透過PNG）を読み込み
   - スクリーンショットに角丸マスク（radius=80）を適用
   - ベゼルの中央にスクリーンショットを配置
   - ベゼルを上から重ねて合成（Dynamic Islandなどを正しく表示）
3. **テキスト追加**:
   - ヒラギノ角ゴシック W8（タイトル用、95pt）
   - ヒラギノ角ゴシック W6（サブタイトル用、45pt）
   - タイトルとサブタイトルを上部に中央揃えで配置
4. **デバイス配置**: テキスト終了位置から150px下に配置し、収まらない場合は自動縮小
5. **最終リサイズ**: 1290 x 2796（iPhone 15 Pro Max / 6.7" 標準）にリサイズ

この処理ロジックは、既存の `docs/screenshots/scripts/process_screenshots.py` から完全移植されており、既存のスクリーンショットと同じ品質を保証します。

## 📐 レイアウトパラメータ

- **作業キャンバス**: 1350 x 2868
- **スクリーンショットサイズ**: 1206 x 2622
- **ヘッダー余白**: 200px
- **行間**: 30px
- **キャプション間隔**: 60px
- **デバイスとテキストの間隔**: 150px
- **最終出力サイズ**: 1290 x 2796（App Store iPhone 6.7" 標準）

## 🎨 カスタマイズ

### テンプレートの作成
独自のテンプレートを作成したい場合は、[TEMPLATES.md](TEMPLATES.md) を参照してください。

### フォントの変更

`Processor` クラスの `_load_hiragino_font` メソッドでフォントパスを変更できます。
デフォルトはヒラギノ角ゴシック W8/W6 です。

### ベゼルのカスタマイズ

異なるデバイスのベゼルを使用する場合は、`resources/bezel.png` を差し替えてください。
ベゼルは透過PNGで、中央部分が透明である必要があります。

## ⚠️ 要件

*   macOS
*   Xcode 16.2+ (`xcrun xcresulttool` での `--legacy` フラグサポート)
*   Python 3.10+
*   Pillow（画像処理ライブラリ）

## 🐛 トラブルシューティング

### スクリーンショットが抽出されない

- UITestコードで `attachment.lifetime = .keepAlways` が設定されているか確認
- `attachment.name` が設定されているか確認
- テストが成功しているか確認（失敗したテストの画像は抽出されません）

### ベゼルからはみ出す / サイズが合わない

- `resources/bezel.png` のサイズを確認
- ベゼルは約1206 x 2622のスクリーンショットに対応している必要があります

### 日本語が文字化けする

- ヒラギノ角ゴシックフォントがシステムにインストールされているか確認
- macOSの標準フォントディレクトリ（`/System/Library/Fonts/`）にアクセスできるか確認

## 📝 ライセンス

MIT
