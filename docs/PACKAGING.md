# Packaging & Distribution Guide

このドキュメントでは、`pip` を使用したインストール、動作検証、および更新方法について解説します。

## 1. 開発中の動作確認 (Verification)

開発段階（ローカル）での動作確認には、主に2つのアプローチがあります。

### A. 開発用モード (Editable Install)
開発中は基本的にこのモードを使用します。ソースコードへの変更が即座にコマンドに反映されます。

```bash
# プロジェクトルートで実行
pip install -e .
```

*   **メリット**: 変更のたびに再インストールやビルドが不要。
*   **注意点**: ファイルコピーが行われないため、`MANIFEST.in` の設定ミス（リソース漏れ）に気づきにくい。

### B. パッケージング検証 (Clean Install)
リリース前や、リソースファイル (`.yaml`, `.png` 等) が正しくパッケージに含まれているか確認する場合に行います。

**検証手順:**

1.  検証用のクリーンな環境を作成（推奨）
    ```bash
    python3 -m venv .venv_test
    source .venv_test/bin/activate
    ```
2.  編集モード**なし**でインストール
    ```bash
    # 現在のディレクトリをインストール
    pip install .
    ```
3.  動作確認
    ```bash
    # 任意のディレクトリに移動して実行
    cd /tmp
    framed run
    ```
    これで「ファイルが見つからない」等のエラーが出なければ、パッケージングは成功しています。

---

## 2. インストール・更新コマンド (Usage)

利用シーンごとのコマンド一覧です。

| シチュエーション | コマンド | 解説 |
| :--- | :--- | :--- |
| **開発者 (初期)** | `pip install -e .` | ソースコードへのシンボリックリンクを作成。 |
| **開発者 (ライブラリ追加時)** | `pip install -e .` | `pyproject.toml` の依存関係が増えた場合に再実行。 |
| **リリース前検証** | `pip install --upgrade .` | ローカルのソースを使って再ビルド・インストール。 |
| **ユーザー (インストール)** | `pip install git+https://github.com/yamshta/framed.git` | GitHubから直接インストール。 |
| **ユーザー (更新)** | `pip install --upgrade git+https://github.com/yamshta/framed.git` | 最新版を取得して更新。強制更新が必要な場合は `--force-reinstall` を付与。 |

## 3. 推奨ワークフロー

1.  普段の開発は `pip install -e .` 環境で行う。
2.  画像や設定ファイルを追加した際は、`MANIFEST.in` を更新する。
3.  GitHubへプッシュする前に、一度 `pip install .` (または `pip install --upgrade .`) を行い、リソース読み込みエラーが出ないか確認する。
