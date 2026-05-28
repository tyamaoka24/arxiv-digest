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
- [ ] ogawa の正しい INSPIRE BAI を確認・登録 (2026-04-14 に homonym 由来の誤 BAI を除去。実 subscriber に BAI があれば `tools/setup_inspire.py` を再実行、無ければ `inspire_id: null` のまま継続)

### 派生 (2026-04-14 redact の副作用)

- [ ] **odakin の主な共同研究者 5 名を `research-collab/collaborators.yaml` に stub 登録**。現状 public profile の「see private registry」が実体を指していない。名前の具体は local backup branch (下記) にのみ残存する pre-redact 版を参照。1 名について漢字表記ゆれが既存 `ogawa` エントリと類似しており別人/同一人物か要確認
- [ ] **orphan 監視**: 2026-04-14 に public repo の history を force-push で rewrite した。残る orphan 状態のノード (詳細 SHA はここに書かない) を GitHub が自然 GC するまでは SHA 直アクセスで旧内容取得可能。1 ヶ月後に origin での 404 化を確認。監視対象 SHA は local backup branch (下記) の `rev-parse HEAD~n` で復元可能
- [ ] **local backup branch 削除**: pre-rewrite history を保持するローカルブランチがある (push 済みでない)。上記 orphan 監視完了後に削除

### 完了 (詳細は DESIGN.md / git log)

- **2026-05-28** (`3bae379`): email delivery channel 追加 (PR #3、 tyamaoka24 さんから、 SMTP/STARTTLS、 HTML + plain-text multipart、 score-badge 色分け)。 maintainer 側 polish (= `c8d56e2`) で (1) Subject の RFC 2047 encoding (= Outlook/Thunderbird での mojibake 防止)、 (2) `EMAIL_TO` の comma-separated multi-recipient 対応 (`email.utils.getaddresses` で display name 内 comma も正しく parse)、 (3) docstring の precedence 修正 (config > env > default)。 8 件 parsing test + Subject RFC 2047 round-trip 検証済。 4 軸 sweep clean
- 2026-04-14: onda プロファイル追加 + Discord mention ID の layer 3 委譲 (設計は DESIGN.md「Discord mention ID を collaborator layer に委譲」セクション)
- 2026-04-14: homonym 由来の誤 INSPIRE データ除去 (ogawa)
- 2026-04-08: archive/ 自動 commit + push 実装 (設計は DESIGN.md)
- 2026-03-31: ogawa プロファイル追加、arxiv_categories 二層構造、scheduled task 統合

## 過去の修正 (詳細は git log)

- **2026-03-31** (`65e7ffe`): ogawa プロファイル追加 + `arxiv_categories` 二層構造 (`inspire_arxiv_categories` 自動 + `arxiv_categories` 手動 union) + `setup_inspire` の対話改善 (BAI 確認、`lookup_author`)。
- **2026-03-30** (`685d2f0`, `819ec81`): Mode B 統合パイプライン (`fetch_all` → スコアリング → `post_all`)、Discord `mention_target` バグ修正、`SKILL-takeda.md` 削除。
- **2026-03-24**: takeda プロファイル追加 (修論:波束形式量子干渉)、マルチプロファイル state ファイル分離、SKILL.md → リポ symlink 化 + バックエンド sync ルール明文化。
