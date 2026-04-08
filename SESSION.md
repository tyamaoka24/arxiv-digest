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
- [x] **archive/ 自動 commit + push**（2026-04-08 完了: 6 日分 cross-session 蓄積を検出 → 根治のため `commit_archives_to_git()` を `src/archive.py` に追加 → `post_all` 末尾で呼び出し）
- [ ] Bluesky / Slack チャンネル追加

## 直近の修正（2026-04-08）

### archive/ 自動 commit + push 導入

毎日 cron で生成される `archive/{year}/{month}/*.json` が **6 日分 (04-02 〜 04-07)** uncommitted のまま蓄積していたのを発見。原因は post_all.py がアーカイブ書き込みをしても commit しない設計で、生成主体と commit 主体が分離していたこと。CLAUDE.md には「git 管理」と明記されていたので、この乖離はバグ。

`src/archive.py` に新関数 `commit_archives_to_git()` を追加し、`post_all.py` の archive ループ末尾で呼ぶ。設計上の安全策:

- **scoped**: `git add archive/` のみ。`src/`、`profiles/`、`config.yaml` 等の WIP に触らない
- **idempotent**: `git diff --cached --quiet` で空コミット防止 (同日複数回 run しても commit しない)
- **cross-machine 安全**: `git fetch` → behind > 0 のときのみ `git pull --rebase --autostash`
- **best-effort**: fetch / rebase / commit / push のどの段階で失敗しても warning print → return。例外を投げない
- **push 失敗許容**: 次回 run が catch up

`commit_archives_to_git` が呼ばれるのは **モード B のみ**。モード A (`post.py`、template 利用者向け) は手動コントロールを残すため auto-commit しない。

**横断的対処** (claude-config / odakin-prefs 側): `git-state-nudge.sh` に「porcelain hash が >24h 同一」を検出する STALE_DIRT 警告を追加 (cross-session WIP leakage の汎用 safety net)、`push-workflow.md` に解釈ガイドを追加。

### DESIGN.md 新規作成

設計判断の正本を残すための `DESIGN.md` をリポに新設。書き起こした内容:

- **二つの実行モード (mode A / mode B) の分離**: 過去の判断を文書化。なぜ並立か、SKILL.md と scorer.py の duplication を許容する理由
- **自動アーカイブと git commit の所有権 (2026-04-08)**: 今回の `commit_archives_to_git` 設計の Why / What / 検討した代替案 (7 案、表形式)、設計判断の小項目 (scope / idempotency / cross-machine 安全 / best-effort / push 失敗の扱い / mode A 不参加)、claude-config STALE_DIRT との分業
- **「Generator owns commit」原則**: 「自動で生成されるもの (cron / scheduled task / script) は、生成主体が commit 責任を持つ」という今回獲得した原則を記録
- **SKILL.md / scheduled task 二重構造**: 既存規約だが、04-08 で「Python 完結により SKILL.md 不変」を選んだ判断の根拠として再記述

CLAUDE.md「How to Resume」と「自動更新ルール」を更新し、DESIGN.md への参照を追加 (重要な判断時に DESIGN.md にも残すよう義務化)。

## 過去の修正 (詳細は git log)

- **2026-03-31** (`65e7ffe`): ogawa プロファイル追加 + `arxiv_categories` 二層構造 (`inspire_arxiv_categories` 自動 + `arxiv_categories` 手動 union) + `setup_inspire` の対話改善 (BAI 確認、`lookup_author`)。
- **2026-03-30** (`685d2f0`, `819ec81`): Mode B 統合パイプライン (`fetch_all` → スコアリング → `post_all`)、Discord `mention_target` バグ修正、`SKILL-takeda.md` 削除。
- **2026-03-24**: takeda プロファイル追加 (修論:波束形式量子干渉)、マルチプロファイル state ファイル分離、SKILL.md → リポ symlink 化 + バックエンド sync ルール明文化。
