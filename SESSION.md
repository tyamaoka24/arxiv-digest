# arxiv-digest Session

## 現在の状態
**安定運用中**: Mode B（ローカル scheduled task）で平日朝に自動配信

## 残タスク
- [ ] Bluesky / Slack チャンネル追加
- [ ] Discord チャンネルの E2E テスト（Webhook + mention_target 動作確認）

## 直近の修正（2026-03-24）

### 障害: scheduled task の SKILL.md 二重管理問題
- **症状**: registered SKILL.md（`~/.claude/scheduled-tasks/`）が 3/16 のまま更新されず、リポ版（3/19）と乖離
- **根本原因**: コピーの二重管理で同期が手動依存だった
- **対策**: registered → リポへの symlink に変更。CONVENTIONS.md §9 に汎用ルール追記
- inspire-monthly も同様に symlink 化（正本: `physics-research/skill/SKILL.md`）

### GitHub Actions の Mode A 停止
- **症状**: `--profile odakin` で Mode A が並行動作、API クレジット枯渇で 3/18 から 5 日間失敗
- **対策**: ワークフローから `--profile odakin` を除去（テンプレートデフォルトに戻す）
