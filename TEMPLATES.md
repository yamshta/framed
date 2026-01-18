# カスタムテンプレートの作成

Framed は拡張性を考慮して設計されています。`src/framed/templates/` にディレクトリを追加することで、新しいレイアウトテンプレートを作成できます。

## 📁 ディレクトリ構成

各テンプレートは独立したディレクトリとして管理し、以下のファイルが必要です：

```
src/framed/templates/<template_name>/
├── __init__.py       # テンプレートクラスの実装
├── template.yaml     # デフォルト設定値
└── sample.png        # テンプレートのプレビュー画像（必須）
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

## 3. サンプル画像 (`sample.png` または `samples/`)

テンプレートのプレビュー用に、以下のいずれかを含めてください：

*   `sample.png`: 1枚の代表的なサンプル画像
*   `samples/`: 複数のサンプル画像を含むディレクトリ（例: `01.png`, `02.png`...）。特に「Perspective Flow」のように複数枚で構成されるテンプレートの場合、全体の流れがわかるように複数枚用意することを推奨します。

これらはユーザー（および開発者）がテンプレートの外観を把握するためのプレビューとして機能します。
