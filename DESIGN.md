# DESIGN — arxiv-digest

主要な設計判断とその理由を時系列で記録する。コードコメント・commit message
には書ききれない「なぜこの形なのか」「他の案を何故却下したか」を残す。

ライブな状態 (現状・残タスク) は SESSION.md、ユーザー向けの仕様は CLAUDE.md
を見ること。本ファイルは「過去の判断の参照先」。

---

## 二つの実行モード (mode A / mode B) の分離

### What

スコアリングを実行する経路として 2 つを並立させている:

| モード | エントリ | スコアラー | コスト | 用途 |
|---|---|---|---|---|
| **A** | `python3 -m src.main --profile <name>` | `src/scorer.py` (Anthropic API) | ~$0.01/日 | テンプレート利用者向け (GitHub Actions / 完全自動) |
| **B** | `src.fetch_all` → Claude が in-context スコアリング → `src.post_all` | Claude Code セッション (skill/SKILL.md 経由) | 無料 (Pro Max) | odakin 自身の運用 (scheduled task) |

両モードは同じプロファイル定義 (`profiles/<name>/`) と同じ配信レイヤー (`src/channels/`) を共有する。違うのは「論文をスコアリングする主体」だけ。

### Why

- **odakin 個人運用**は Claude Pro Max のサブスクで scheduled task が無料で回せる。Anthropic API を別途契約して duplicate 課金する理由がない
- **テンプレート利用者**は Claude Code を持っていない or 自前のサーバーで cron させたいケースがある。彼らには API + GitHub Actions の標準パスを残す必要がある
- 同じスコアリング品質を両モードで再現するために、Claude 用の指示は `skill/SKILL.md` に、API 用のプロンプトは `src/scorer.py` に書く (重複あり、整合性は人間が保つ)

### 検討した代替案と却下理由

| 案 | 内容 | 却下理由 |
|---|---|---|
| (A) Mode A だけ残す | Claude を捨てる、API + GitHub Actions に統一 | odakin の個人運用コストが上がる (Pro Max 重複課金)。Claude session の柔軟性 (途中で著者に対する文体調整など) も失う |
| (B) Mode B だけ残す | API ベースを捨てる、SKILL.md 単一責務 | テンプレート利用者は Claude Code を強制される。GitHub Template Repository としての汎用性が失われる |
| (C) 統合層を作って 1 つの呼び出しで両方走る | 抽象化の極致 | YAGNI。両者のインターフェース (Anthropic SDK vs in-context message) が違いすぎて統合層がオーバーエンジニアリング |
| **(D, 採用) 並立** | 2 経路を独立に維持、共通部分のみ共有 | 単純、各モードが他方を意識しない、failure mode が分離 |

### 設計判断の小項目

- **prompt の duplication は許容**: SKILL.md (mode B 用) と scorer.py (mode A 用) の指示文は意味的に同じだが文体が違う。整合性は CLAUDE.md の「reason/summary 文字数」項目で機械的にチェックできるよう threshold だけは表記揃えしてある。完全自動同期は YAGNI
- **配信レイヤーは共有**: `src/channels/` (mastodon / discord / etc.) は両モードで同じコードを通る。スコアリング結果の JSON schema (`scored_papers_<profile>.json`) は両モードで同一フォーマット


## 自動アーカイブと git commit の所有権 (2026-04-08)

### What

`src/archive.py` に 2 つの関数:

1. `archive_scored_papers(profile_name, ...)` — JSON snapshot を `archive/{year}/{month}/{date}_{profile}.json` に書き出す。
2. `commit_archives_to_git()` — `archive/` 配下を git commit + push する。

`post_all.py` (mode B のエントリ) は per-profile loop で前者を呼んだ後、loop の外で後者を 1 回呼ぶ。後者は best-effort で、どの段階で失敗しても warning を print して return するのみ — 例外を投げないので scheduled task の daily run を絶対に壊さない。

### Why

CLAUDE.md は「`archive/{year}/{month}/{date}_{profile}.json` に scored_papers を日次保存（git 管理）」と明記しているが、2026-04-08 朝の手動 sweep で `archive/` に **6 日分 (04-02 〜 04-07) の uncommitted ファイル** が蓄積していたことが発覚。原因は post_all.py が `archive_scored_papers` を呼んで file を書くだけで commit しない設計で、**「生成主体」と「commit 主体」が分離していた**。CLAUDE.md の意図 (git 管理) と実装が乖離していたバグ。

cron が毎日生成するファイルが uncommitted のまま蓄積するのは、典型的な cross-session WIP leakage。単一マシンでは 6 日でも誰も気付かないし、複数マシンに展開するとさらに状況が悪化する (片方のマシンの dirty が他方から見えない)。

### 採用した原則: Generator owns commit

> **「自動で生成されるもの (cron / scheduled task / script の出力) は、生成主体が commit 責任を持つ」**

これを守らないと「誰がいつ commit するか」が宙に浮き、結果として誰も commit せず dirty が累積する。今回はその典型例が顕在化した。

逆方向 (人間が編集するファイル) は人間規律 + safety net (claude-config の git-state-nudge.sh STALE_DIRT) が catch する。生成主体側 vs 人為編集側の責任分担を明確にすることで、両者の対処方針を取り違えなくなる。

### 検討した代替案と却下理由

| 案 | 内容 | 却下理由 |
|---|---|---|
| (A) `skill/SKILL.md` に「post_all 後に手動 commit」と書く | Claude が SKILL に従って commit する | (1) Claude が instruction を skip するリスク、(2) SKILL.md を編集すると `update_scheduled_task` でバックエンド prompt 同期が必須 (CLAUDE.md ルール) で sync drift 危険、(3) instruction が増えるほど skip 率上昇 |
| (B) 別 module (`src/git_helpers.py`) を新設 | 責務分離の極致 | archive と git commit はどちらも「archive の永続化」という同じ概念に属する。分けると「これは archive 関連? git 関連?」を読者が考える必要が出る |
| (C) post_all.py 内に直接書く | エントリポイントに集約 | エントリは「per-profile loop の orchestration」が責務。git 操作を埋めると post_all.py が肥大化、archive 関連ロジックが 2 ファイルに分散 |
| (D) `gh` CLI (subprocess で gh CLI を呼ぶ) | GitHub API 経由で commit | 重い、ネットワーク必須、subprocess に git を呼ぶのと比較して advantage 無し。普通の git commit + push で十分 |
| (E) GitPython (Python library) | 純 Python | dependency 追加 (CLAUDE.md「外部依存は pyyaml + anthropic のみ」と矛盾)、subprocess.run より遅い、複雑 |
| (F) hook 内で auto-commit (claude-config 側) | hook で検知 → そのまま commit | hook は「警告」が責務、auto-commit は意図がわからない変更を git history に流し込むので不適切 (cf. claude-config DESIGN.md「Generator owns commit」原則) |
| **(G, 採用) `src/archive.py` 内で `commit_archives_to_git()`** | archive モジュールが file 永続化と git 永続化の両方を持つ | 単一責任 (archive の永続化全般)、subprocess.run で軽量、Claude 依存なし、`post_all.py` の修正は import + 1 行呼び出しのみ |

### 設計判断の小項目

- **scope: `git add archive/` のみ**: ユーザーが `src/`、`profiles/`、`config.yaml` 等を編集中でも、その WIP に触らない。`git add .` や `git add -A` は禁物 — auto commit が unrelated WIP を巻き込むと「scheduled task が私の作業を勝手に commit した」事故が起きる
- **idempotent (空コミット防止)**: `git diff --cached --quiet` で staged 差分が無ければ commit しない。同日複数回 run しても 1 commit のみ。手動再 run も安全
- **cross-machine 安全 (`pull --rebase --autostash`)**: `git fetch` → `behind` を測定 → behind > 0 のときだけ `pull --rebase --autostash`。常時 rebase は不要 (overhead だけ増える)。autostash は post_all.py 自体が dirty を残さない設計と組み合わせて使うので、残ってる dirt は user 編集なら一度 stash されて pop される
- **best-effort (例外を投げない)**: fetch / rebase / commit / push のどの段階で失敗しても、warning を print して `return` する。scheduled task の daily run が transient な network 障害で吹き飛ばないことが最優先 (= post_all.py の他の処理は完了している、scoring と配信は成功している、archive ファイルは disk に書かれている)
- **push 失敗の扱い: 次回 run で catch up**: push が失敗しても local commit は成功している。次回 run で `behind > 0` ならば pull --rebase してから push し直す。完全に自己治癒する。最悪のケース (常時 push 失敗) は STALE_DIRT が catch するわけではないが、次回 run の `git push` がリトライするので少なくとも 1 日に 1 回は復旧チャンスがある
- **mode A (post.py) は対象外**: テンプレート利用者は手動コントロール (= 自分の好きなタイミングで commit + push) を残すべき。GitHub Actions で動かしてる人は workflow から git push する形がよくある。自動 commit が彼らの workflow と衝突しないように、mode B (= odakin 専用) でのみ呼ぶ

### 副次的な観察: STALE_DIRT との分業

claude-config 5ddd43f で git-state-nudge.sh に追加された STALE_DIRT signal は **人為編集の取りこぼしを catch する safety net**。arxiv-digest の cron 由来蓄積は STALE_DIRT が「警告を出す」ことしかできず、ファイルは依然 dirty のまま。

正しい分業:

- arxiv-digest 側 (`commit_archives_to_git`): cron generator が **自分で commit する** = **root cause level の対処**
- claude-config 側 (STALE_DIRT): generator にバグが残ったときの **fail-safe**

両方あるからこそ堅い。前者だけだと将来別の cron task で同じ間違いを繰り返したときに気付けない。後者だけだとファイルは dirty のままで毎日警告が出続ける。詳細は claude-config DESIGN.md「git-state-nudge.sh: cross-session WIP leakage の検出 — STALE_DIRT」セクション参照。


## SKILL.md / scheduled task の二重構造 (2026-04 経緯メモ)

### What

scheduled task の prompt は次の 3 箇所に存在する:

1. **`skill/SKILL.md`** (リポ内、git 管理) — git で差分追跡される source-of-truth (人間視点)
2. **`~/.claude/scheduled-tasks/<task-id>/SKILL.md`** (ローカル) — 1 への symlink (`ls -la` で確認可)
3. **Claude バックエンド側に保存された prompt** — `create_scheduled_task` / `update_scheduled_task` で書き込み、scheduled task 起動時に **これだけ** が読まれる。1 と 2 は実行時には一切参照されない

### Why この形

詳細は `~/Claude/claude-config/conventions/scheduled-tasks.md` にあるが要点だけ:

- **SKILL.md をリポに置く理由**: git で差分追跡・コードレビュー・複数端末同期 (`git pull` で内容共有)
- **バックエンドが SKILL.md を読まない理由**: Claude Code の scheduled task 仕様。`create_scheduled_task` 呼び出し時にバックエンドに prompt が保存され、以後ローカルファイルは参照されない
- **symlink (2)**: ローカルで `~/.claude/scheduled-tasks/` を見たときに内容を確認するための便宜 (実行には影響しない)

### 制約と運用ルール

SKILL.md を **single source of truth にできない** という不都合は受容している。SKILL.md とバックエンド prompt が乖離する drift リスクが常にある。これを抑えるため:

1. SKILL.md を編集したら、**直後に** `update_scheduled_task` を呼ぶ (CLAUDE.md「自動更新ルール」に明記)
2. CLAUDE.md / SESSION.md にも sync 必須を明記してリマインダーを残す
3. 新しいマシンで pull した後は、そのマシンで使う scheduled task は `update_scheduled_task` で prompt を sync する (バックエンドがマシン独立なため)

### 2026-04-08 commit_archives_to_git で SKILL.md を **触らなかった**理由

最初は「ステップ3 末尾に commit + push 手順を書く」案 (上記 (A)) を検討したが、深層検討の結果、**Python 側で完結させる** 方針に変更した。理由:

- Python レイヤーで完結 → SKILL.md unchanged → `update_scheduled_task` 不要 → バックエンド sync drift リスクゼロ
- Claude (scheduled task の実行者) は post_all.py の **stdout** で commit/push 結果を直接見るので不透明性も無い
- SKILL.md は「procedure description」で、Python 内部の実装詳細 (auto-commit) は記述する必要がない

これは「SKILL.md と Python の責務分離」を強化する判断でもある。SKILL.md は「Claude にどう動いてほしいか」を書く層で、Python は「Claude が呼ぶ tool」のレイヤー。tool が auto で何かをやる場合、SKILL.md には書かなくてよい (= Claude は tool の output を見れば分かる)。

## Discord mention ID を collaborator layer に委譲 (2026-04-14)

### 背景

`profiles/<name>/config.yaml` に `mention_target: "<@NUMERIC_ID>"` として Discord 数値ユーザー ID を平文で保持していた。このリポは public (`odakin/arxiv-digest`) で、profile 側の interest_profile.txt にも実名・所属を書くパターンが先行しており、**実名 + 所属 + Discord 数値 ID** が git history ごと GitHub に並列して公開されていた。

Discord 数値 ID 単独の危険度は低いが、実名・所属と並列されると dox (doxxing) 素材価値が跳ね上がるため、今後の leak を止める方針とした。新しい subscriber を追加するタイミングで設計を見直し、併せて interest_profile.txt の identity 部分も redact する (個別 subscriber の実名・所属・named collaborators は private registry に委譲、public には研究興味のみ残す) 方針に切り替えた。

### 採用した設計: layer 3 委譲 + env var bridge

odakin の 4 層アーキテクチャ (claude-config の `docs/personal-layer.md`):

| 層 | リポ | この問題における役割 |
|---|---|---|
| 1 public tool | `arxiv-digest` (このリポ) | profile config は env 変数**名**のみ保持 |
| 1 public conventions | `claude-config` | `collaborators.md` schema に `discord_id` field を追加 |
| 3 collaborator | `research-collab/collaborators.yaml` (git-crypt) | **Discord ID の canonical source** |
| runtime (local) | `arxiv-digest/.env` (gitignored) | 実行時に読まれる env 変数の実体 |

フロー:
```
research-collab/collaborators.yaml       (layer 3, git-crypt)
          │  odakin が手動コピー (将来 sync script)
          ▼
arxiv-digest/.env                        (gitignored)
          │  src/config.py の load_dotenv()
          ▼
os.environ[DISCORD_MENTION_<PROFILE>]
          │  src/channels/discord.py が resolve
          ▼
Discord webhook 本文の mention
```

### 検討した代替案

| 案 | 却下理由 |
|---|---|
| α: 新規 `arxiv-digest-private` private repo を作る | subscriber 全員が research collaborator だったため、既存 `collaborators.yaml` で十分。新リポのオーバーヘッドを避けた |
| β: `odakin-prefs` (layer 2 personal) に入れる | layer 2 は本来「odakin 自身の設定」で「他者情報」を置く層ではない。境界曖昧化を避けた |
| γ: `.env` のみ、構造化ストアなし | Cross-machine backup・metadata (名前・所属の紐付け) を失う |
| 1': `mention_target` を直書きのまま git history purge | すでに public、forks/GitHub cache/archive.org 等に残存確実。force-push の破壊的コストに見合う効果がない |

### 実装

- **Schema**: `claude-config/conventions/collaborators.md` に `discord_id: null` field 追加
- **Data**: `research-collab/collaborators.yaml` に takeda / ogawa / onda エントリを新規追加、各々 `discord_id` をセット
- **Code**: `src/channels/discord.py` が `mention_target_env` キー (env 変数名) を優先。env 未設定時は warning + mention なし送信で fail soft。後方互換として legacy `mention_target` (直書き) も残す
- **Config**: `profiles/{onda,takeda,ogawa}/config.yaml` を `mention_target_env: DISCORD_MENTION_<NAME>` に置き換え
- **Runtime**: `arxiv-digest/.env` (gitignored) に `DISCORD_MENTION_*` 実値を記載

### 運用上の帰結

- **既存 public git history は残る**: takeda/ogawa の Discord ID は過去コミットに平文で残っており、これは変えない。「今後新規 leak しない」が現実的な目標
- **Template 利用者への波及**: default profile は mention_target を持たないので影響なし。他者が fork した際に onda/takeda/ogawa profile はそのまま残るが、env 変数が未設定なので mention は無言でスキップされる (fail soft 設計)
- **Cross-machine**: 新 Mac で setup した際は `research-collab` を unlock → `collaborators.yaml` から `discord_id` を手動で `.env` にコピー。将来 sync script 化は検討可能だが現状は手動で十分

## 当日追加された subscriber の catch-up (2026-04-14)

### 問題

scheduled task は平日朝 10:31 に発火し、その時点の active profile 一覧で fetch → score → post する。一日の途中で新しい subscriber profile を足した場合、その日の配信は自動では行われない (= 新 subscriber は翌営業日から自動配信)。

2026-04-14 の onda 追加時、初日配信を手動で行う必要があった。

### 採用した catch-up フロー (archive-as-transport)

運用 Mac (scheduled task を走らせる Mac) が必ずしも作業 Mac と同じではない場合 (odakin の場合は home ↔ iMac-3)、かつ `state/` は gitignored なので scored 結果を直接 commit で運べない。しかし `archive/` は git-tracked (public) なので、そこを cross-machine transport に使える。

手順:

```bash
# --- 作業 Mac (scoring を行う Mac、Mode B であれば Claude session 内で score) ---
cd ~/Claude/arxiv-digest
python3 -m src.fetch --profile <new_name>          # today_papers_<new_name>.json を生成
# ... Claude が scoring して state/scored_papers_<new_name>.json を書く ...
python3 -c "
from pathlib import Path
from src.archive import archive_scored_papers
archive_scored_papers('<new_name>', scored_path=Path('state/scored_papers_<new_name>.json'))
"
git add archive/$(date +%Y)/$(date +%m)/$(date +%Y-%m-%d)_<new_name>.json
git commit -m "archive: $(date +%Y-%m-%d) <new_name> daily digest (mid-day catch-up)"
git push

# --- 運用 Mac (webhook を持ち post する Mac) ---
cd ~/Claude/arxiv-digest
git pull
# archive ファイルを state/ にコピーして post パイプラインに食わせる
cp archive/$(date +%Y)/$(date +%m)/$(date +%Y-%m-%d)_<new_name>.json \
   state/scored_papers_<new_name>.json
python3 -m src.post --profile <new_name>
```

### なぜ archive-as-transport が clean か

- `archive/` は「scored_papers の日次アーカイブ」という自然な責務を持つ。mid-day catch-up で使うのは **同じファイルを同じ時点で保存する** だけなので、運用と整合
- `archive/` は公開 git-tracked だが、scoring 結果の粒度は **通常の scheduled task が毎日保存しているものと同一**なので、追加 leak は発生しない
- `state/` を git-tracked にする案は棄却: gitignored の現設計は「日々の大量 state ファイルで repo を肥大化させない」ための既存判断。例外を作らず archive を使う方が設計一貫性が高い
- Dropbox 等の private 経路は、archive で済むなら不要。"運用 data" と "生成物 commit" を別経路にする複雑さを避ける

### Mid-day catch-up の将来改善オプション

将来 subscriber 追加頻度が上がった場合 (年数回 → 月 1 回以上等)、以下の自動化を検討:

- **(a)** `src/` に CLI `python3 -m src.catchup --profile <name>` を追加: fetch + score (mode A API) + archive commit + push を一気に実行。post は運用 Mac 側に残す
- **(b)** Scheduled task SKILL.md step 2 前に「今日 fetch されていない active profile を自動補完」処理を追加。ただし SKILL.md 変更は backend prompt 再 sync が必要でコストあり

un-defer トリガーは `odakin-prefs/next-steps.md` 「arxiv-digest scheduled task に当日追加 subscriber の catch-up 対応」参照。
