# arxiv-digest Session

## 現在の状態
**安定運用中**: Mode B（ローカル scheduled task）で平日朝に自動配信

### 配信中プロファイル
| プロファイル | チャンネル | スケジュール |
|------------|-----------|------------|
| odakin | Mastodon (Vivaldi Social) | 平日 10:31 |
| takeda | Discord (#arxiv-digest) | 平日 10:31（同時） |
| ogawa | Discord (#arxiv-digest) | 平日 10:31（同時） |

## 要対応（学校 Mac で pull 後）

- [x] **`arxiv-digest` の backend prompt を SKILL.md と同期する**（2026-04-02 完了: `update_scheduled_task` で prompt を再設定）

## 残タスク
- [x] 学校 Mac で `git pull` → scheduled task 統合（2026-03-31 完了: `arxiv-digest-takeda` 無効化、統合版 SKILL.md で1本運用）
- [x] ogawa プロファイル追加（2026-03-31 完了: Discord 同チャンネル）
- [x] arxiv_categories 二層構造実装（2026-03-31 完了: INSPIRE 自動 + 手動 extras）
- [ ] Bluesky / Slack チャンネル追加

## 直近の修正（2026-03-31）

### ogawa プロファイル追加 + arxiv_categories 二層構造 + setup_inspire 改善

- `profiles/ogawa/` 追加: Discord 同 webhook (`DISCORD_WEBHOOK_URL_TAKEDA`)
- `src/config.py`: `_merge_categories()` 追加 — `inspire_arxiv_categories`（自動）+ `arxiv_categories`（手動）を union
- `tools/setup_inspire.py`:
  - `extract_categories()` + `update_profile_config()` 追加 — config.yaml の `inspire_bai` / `inspire_name` / `inspire_affiliation` / `inspire_arxiv_categories` を自動設定
  - 初回セットアップ時のみ著者確認（`Continue? [Y/n]`）、同 BAI 再実行はスキップ
  - BAI 直接指定時に `lookup_author()` で著者名を表示して確認（間違い BAI 防止）
  - 月次 `check_for_profile_updates()` は `main()` を経由しないので確認ダイアログなし
- `tools/fetch_inspire.py`: `lookup_author()` 追加 — BAI から著者名・所属を取得
- `src/profile_update.py`: `inspire_name` を使った強化 author matching、月次更新で name/affiliation を保持

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
- **配信先**: Discord #arxiv-digest チャンネル
- **環境変数**: `DISCORD_WEBHOOK_URL_TAKEDA`（.env に設定済み）

### マルチプロファイル対応
- fetch/post でプロファイル別のステートファイルを使用（`today_papers_{profile}.json` / `scored_papers_{profile}.json`）
- Discord チャンネルで `env_var` フィールドによるプロファイル別 webhook URL をサポート
- odakin の SKILL.md もプロファイル別ファイル名に更新

### 障害: scheduled task の SKILL.md 二重管理問題（修正済み）
- ローカル SKILL.md はリポへの symlink に変更済み
- ただし **バックエンドは SKILL.md を実行時に読まない**。SKILL.md 編集後は `update_scheduled_task` で prompt を同期する必要あり（CLAUDE.md に明記済み）
- inspire-monthly で同期漏れが発覚し修正（2026-04-01）
