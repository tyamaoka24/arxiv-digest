# arxiv-digest Session

## 現在の状態
**安定運用中**: Mode B（ローカル scheduled task）で平日朝に自動配信

### 配信中プロファイル
| プロファイル | チャンネル | スケジュール |
|------------|-----------|------------|
| odakin | Mastodon (Vivaldi Social) | 平日 10:31 |
| takeda | Discord (#arxiv-digest) | 平日 10:31（同時） |
| ogawa | Discord (#arxiv-digest) | 平日 10:31（同時） |
| onda | Discord (#arxiv-digest) | 平日 10:31（同時、2026-04-14 追加） |

## 要対応（学校 Mac で pull 後）

- [x] **`arxiv-digest` の backend prompt を SKILL.md と同期する**（2026-04-02 完了: `update_scheduled_task` で prompt を再設定）

## 残タスク

### 2026-04-14 の onda 追加に付随

- [ ] **他マシン (学校 Mac 等) で `.env` 生成**: `research-collab` を clone + `git-crypt unlock` 後、`python3 -m tools.sync_mentions` 一発で `DISCORD_MENTION_*` が生成される (helper は 2026-04-14 で実装)。scheduled task がそこで走っている場合、env 未設定だと mention は無言スキップ (fail soft) になるので即時の不具合は出ないが、メンションが消える
- [ ] **新 subscriber への事前告知**: 明日 (2026-04-15) 朝 10:31 ごろから Discord `#arxiv-digest` で mention 付き配信が始まる。一言入れておくべき
- [x] **ogawa エントリの PII 補完** (2026-04-14 完了: name_en / name_ja / affiliation を collaborators.yaml に追加)
- [x] **arxiv-digest/CLAUDE.md の profile 表を更新** (2026-04-14 完了: onda 行追加、stale 表記修正、設計参照を明記)
- [x] **subscriber profile の PII redact (全 3 名)** (2026-04-14 完了: option iii 採用 → takeda/ogawa/onda の interest_profile.txt / SESSION.md / DESIGN.md から実名・所属・named collaborators を削除、詳細は research-collab に集約)
- [ ] **README.md / SKILL.md に `.env` の `DISCORD_MENTION_*` 項目を明示**: 新しいマシンでの setup 時に webhook と並んで用意すべき env var であることを記載

### 継続タスク

- [ ] Bluesky / Slack チャンネル追加

### 派生 (2026-04-14 redact の副作用)

- [ ] **odakin の主な共同研究者 5 名を `research-collab/collaborators.yaml` に stub 登録**。現状 public profile の「see private registry」が実体を指していない。名前の具体は local backup branch (下記) にのみ残存する pre-redact 版を参照。1 名について漢字表記ゆれが既存 `ogawa` エントリと類似しており別人/同一人物か要確認
- [ ] **orphan 監視**: 2026-04-14 に public repo の history を force-push で rewrite した。残る orphan 状態のノード (詳細 SHA はここに書かない) を GitHub が自然 GC するまでは SHA 直アクセスで旧内容取得可能。1 ヶ月後に origin での 404 化を確認。監視対象 SHA は local backup branch (下記) の `rev-parse HEAD~n` で復元可能
- [ ] **local backup branch 削除**: pre-rewrite history を保持するローカルブランチがある (push 済みでない)。上記 orphan 監視完了後に削除

### 完了

- [x] 学校 Mac で `git pull` → scheduled task 統合（2026-03-31 完了）
- [x] ogawa プロファイル追加（2026-03-31 完了）
- [x] arxiv_categories 二層構造実装（2026-03-31 完了）
- [x] archive/ 自動 commit + push（2026-04-08 完了）
- [x] onda プロファイル追加 + Discord mention ID を layer 3 に委譲（2026-04-14 完了）

## 直近の修正（2026-04-14）

### onda プロファイル追加 + Discord mention ID を layer 3 (collaborators.yaml) に委譲

- **onda プロファイル**: 新規 subscriber を追加。arxiv categories: astro-ph.CO / astro-ph.IM / astro-ph.HE / hep-ph / gr-qc。INSPIRE BAI なし。詳細 (identity / affiliation / 研究文脈) は `research-collab/collaborators.yaml` 参照。
- **Discord mention ID 設計見直し**: 公開リポに平文で保持されていた数値 ID を、`research-collab/collaborators.yaml` (layer 3, git-crypt) を canonical source とし、arxiv-digest 側は `mention_target_env: DISCORD_MENTION_<NAME>` で env 変数名のみを持つ設計に変更。`.env` は gitignored で実値を保持。詳細: `DESIGN.md`
- **影響範囲**: `claude-config/conventions/collaborators.md` schema に `discord_id` field 追加、`research-collab/collaborators.yaml` に takeda/ogawa/onda 追加、`src/channels/discord.py` に `mention_target_env` サポート追加、3 プロファイルの config.yaml を書き換え
- **既存 git history の Discord ID**: 過去の public コミット (takeda/ogawa) には平文のまま残存。history purge は効果/コスト比で見送り
- **scheduled task**: プロファイルは auto-discover なので onda は自動で拾われる。SKILL.md 変更なし → `update_scheduled_task` 不要

## 過去の修正（2026-04-08）

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
