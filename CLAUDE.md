# Framed - Development Rules

このプロジェクトの詳細な開発ガイドは [`AGENTS.md`](./AGENTS.md) を参照してください。

## Quick Reference

- **プロジェクト**: iOS App Storeスクリーンショット自動生成ツール
- **言語**: Python 3.10+
- **重要**: 既存実装（`docs/screenshots/scripts/process_screenshots.py`）の完全移植
- **品質基準**: 既存スクリーンショット（`fastlane/screenshots/ja/*.png`）と完全一致

## 最重要ルール

1. レイアウトパラメータは推測で調整しない → 既存コードを参照
2. `xcresulttool` には必ず `--legacy` フラグを付ける
3. 最終出力は必ず **1290x2796** にリサイズ
4. ヒラギノフォント（W8/W6）は `index=0` 指定が必須

詳細は [`AGENTS.md`](./AGENTS.md) を確認してください。
