# arxiv-digest Session

## 現在の状態
**安定運用中**: Mode B（ローカル scheduled task）で平日朝に自動配信

### 配信中プロファイル
| プロファイル | チャンネル | スケジュール |
|------------|-----------|------------|
| odakin | Mastodon (Vivaldi Social) | 平日 10:31 |
| takeda | Discord (東女物理研 #arxiv-digest) | 平日 10:37 |

## 残タスク
- [ ] Bluesky / Slack チャンネル追加
- [ ] Discord チャンネルの E2E テスト（odakin 用の Webhook + mention_target 動作確認）
- [ ] takeda プロファイルの初回配信確認（次の平日朝）
- [ ] satsuko3310 の Discord ユーザー ID を取得し mention_target に設定

## 直近の修正（2026-03-24）

### takeda プロファイル追加
- **修論**: 波束形式による量子干渉と測定過程の理論的再構成（二光子 double-double-slit）
- **カテゴリ**: quant-ph, physics.optics
- **配信先**: Discord（東女物理研サーバー #arxiv-digest チャンネル）
- **環境変数**: `DISCORD_WEBHOOK_URL_TAKEDA`（.env に設定済み）

### マルチプロファイル対応
- fetch/post でプロファイル別のステートファイルを使用（`today_papers_{profile}.json` / `scored_papers_{profile}.json`）
- Discord チャンネルで `env_var` フィールドによるプロファイル別 webhook URL をサポート
- odakin の SKILL.md もプロファイル別ファイル名に更新

### 障害: scheduled task の SKILL.md 二重管理問題（既解決）
- registered → リポへの symlink に変更済み
- inspire-monthly も同様に symlink 化
