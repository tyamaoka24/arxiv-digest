# arxiv-digest Session

## 現在の状態
**安定運用中**: Mode B（ローカル scheduled task）で平日朝に自動配信

### 配信中プロファイル
| プロファイル | チャンネル | スケジュール |
|------------|-----------|------------|
| odakin | Mastodon (Vivaldi Social) | 平日 10:31 |
| takeda | Discord (東女物理研 #arxiv-digest) | 平日 10:31（同時） |

## 残タスク
- [x] 学校 Mac で `git pull` → scheduled task 統合（2026-03-31 完了: `arxiv-digest-takeda` 無効化、統合版 SKILL.md で1本運用）
- [ ] Bluesky / Slack チャンネル追加

## 直近の修正（2026-03-30）

### Discord mention_target バグ修正
- `discord.py` の `_format_paper()` に `mention_target` が入っていなかった
- ヘッダー投稿（最初の1件）にしかメンションが付かず、武田さんに通知が飛ばなかった
- Mastodon 版と同様に各論文投稿にも `mention_target` を含めるよう修正

### 全プロファイル一括配信対応
- `src/fetch_all.py` 新規: 全アクティブプロファイルのカテゴリを union → 1回の RSS 取得
- `src/post_all.py` 新規: 全プロファイルの scored_papers を一括配信（1件エラーでも残り続行）
- `src/config.py`: `list_active_profiles()` 追加（enabled チャンネルがあるプロファイルのみ返す）
- `skill/SKILL.md`: 統合版に書き換え（fetch_all → 全プロファイル順次スコアリング → post_all）
- `skill/SKILL-takeda.md`: 削除（統合版に吸収）
- **未完了**: 学校 Mac で scheduled task を統合（2本→1本）、symlink 更新

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
