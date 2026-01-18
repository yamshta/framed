# カスタムテンプレートの作成

Framed は拡張性を考慮して設計されています。`src/framed/templates/` にディレクトリを追加することで、新しいレイアウトテンプレートを作成できます。

## 📁 ディレクトリ構成

各テンプレートは独立したディレクトリとして管理し、以下のファイルが必要です：

```
src/framed/templates/<template_name>/
├── __init__.py       # テンプレートクラスの実装
├── template.yaml     # デフォルト設定値
└── samples/          # サンプル出力とテスト用設定
    ├── framed.yaml   # サンプル生成用の設定ファイル
    ├── raw/          # -> sample_raws/ja/ へのシンボリックリンク
    └── *.png         # 生成されたサンプル画像
```

### 共有素材ディレクトリ

全テンプレートで共通の生スクリーンショットは `sample_raws/` に配置します：

```
framed/
├── sample_raws/
│   └── ja/                 # 日本語用の生スクリーンショット
│       ├── onboarding.png
│       ├── home_empty.png
│       └── ...
└── src/framed/templates/
    └── <template_name>/samples/
        └── raw/ -> ../../../../../../sample_raws/ja  # シンボリックリンク
```

## 1. 実装 (`__init__.py`)

テンプレートクラスは `framed.api.Template` を継承し、`process` メソッドを実装する必要があります。

```python
from PIL import Image, ImageDraw
from ...api import Template

class MyCustomTemplate(Template):
    """
    テンプレートの説明。
    """
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        """
        最終的な画像を合成します。
        
        Args:
            screenshot: XCUITestから取得した生のスクリーンショット画像
            text_config: framed.yaml から読み込まれた設定（title, subtitle, 色設定など）
            device_frame: オプションのデバイスフレーム（スクリーンショット合成済み）
            index: 現在のスクリーンショットのインデックス (0始まり)
            total: スクリーンショットの総数
        
        Returns:
            Image.Image: 合成後の最終画像 (通常は 1290x2796)
        """
        
        # 1. デフォルト値付きで設定を取得
        bg_color = text_config.get('background_color', '#FFFFFF')
        
        # 2. キャンバスの作成
        canvas = Image.new('RGB', (1290, 2796), bg_color)
        draw = ImageDraw.Draw(canvas)
        
        # 3. 独自のレイアウトを描画...
        # ...
        
        return canvas
```

**注意**: ディレクトリをPythonパッケージとして認識させるため、`__init__.py` である必要があります。`Processor` はこれらのディレクトリを自動的に探索し、`Template` を継承したクラスをインスタンス化します。

## 2. 設定 (`template.yaml`)

テンプレートで使用するキー（色やテキストサイズなど）のデフォルト値を定義します。ここで定義したキーは、ユーザーの `framed.yaml` の `template_settings` で上書き可能になります。

```yaml
description: "マーケティング用のカスタムレイアウト"
defaults:
  background_color: "#FFFFFF"
  accent_color: "#FF0000"
  circle_radius: 50
```

ユーザーは以下のコマンドで設定可能な項目を確認できます：
```bash
framed template-help --name <template_name>
```

## 3. サンプル (`samples/`)

各テンプレートの `samples/` ディレクトリには以下を含めます：

1. **`framed.yaml`**: サンプル生成用の設定ファイル
2. **`raw/`**: 共有素材へのシンボリックリンク
3. **生成されたサンプル画像** (`.png`)

### サンプル生成方法

新しい `framed generate-samples` コマンドを使用すると、全テンプレート（または特定のテンプレート）のサンプルを一括生成できます。

```bash
# 全テンプレートのサンプルを生成
framed generate-samples

# 特定のテンプレートのみ生成
framed generate-samples --template cascade
```

このコマンドは自動的に以下の処理を行います：
1. `sample_raws/ja/` から生スクリーンショットを読み込み
2. 既存のサンプル画像をクリーンアップ
3. 各テンプレートの `samples/framed.yaml` に基づいて生成
4. 一時ファイルを削除

手動で生成する場合は、各ディレクトリで以下を実行します：
```bash
cd src/framed/templates/<template_name>/samples
framed run --skip-capture
```

## 4. Cascade テンプレート（グループ機能）

Cascade テンプレートは複数のスクリーンショットを1枚の画像に合成します。
`groups` キーを使用して、どのスクリーンショットをグループ化するかを定義します：

```yaml
template: "cascade"

groups:
  - output: "01_cascade.png"
    screens: ["onboarding", "home_empty", "recording"]
    template: "cascade"
  - output: "02_inbox.png"
    screens: ["inbox"]
    template: "standard"
```

### CascadeTemplate クラス

```python
class CascadeTemplate(StandardTemplate):
    def process_group(self, device_frames: list[Image.Image], text_configs: list[dict], lang: str) -> Image.Image:
        """複数のデバイスフレームを1枚の画像に合成"""
        ...
```

## 利用可能なテンプレート

| テンプレート | 説明 |
|---|---|
| `standard` | 基本レイアウト（タイトル + サブタイトル + 中央デバイス） |
| `panoramic` | 連続する波形背景を持つレイアウト |
| `perspective` | パースペクティブ変形 + パノラマ背景 |
| `cascade` | 複数デバイスをカスケード状に配置 |
