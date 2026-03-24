# arxiv-digest

arXiv 新着論文の AI スコアリング＋自動配信システム。GitHub Template Repository。

## リポジトリ情報

- パス: `~/Claude/arxiv-digest/`
- ブランチ: `main`
- リモート: `odakin/arxiv-digest` (public)
- 開発者（odakin）自身もこのリポで日常運用

## 実行モード

| モード | スコアリング | コスト |
|--------|------------|--------|
| **A: GitHub Actions** | `src/scorer.py` → Anthropic API | ~$0.01/日 |
| **B: ローカル Claude Code** | scheduled task が直接スコアリング | 無料（Pro Max） |

**odakin 自身はモード B で運用。モード A はテンプレート利用者向け。**

配信中プロファイル:
| プロファイル | チャンネル | メンション先 |
|------------|-----------|------------|
| odakin | Mastodon (Vivaldi Social `@odakinarxiv`) | `@odakin@social.vivaldi.net` |
| takeda | Discord (東女物理研 `#arxiv-digest`) | `<@888803091296706650>` (satsuko3310) |

共通パイプライン: `src.fetch → [スコアリング] → src.post → チャンネル配信`

- モード A: `python3 -m src.main --profile <name>`（全ステップ Python 内で完結）
- モード B: `src.fetch` → Claude がスコアリング → `src.post`（`skill/SKILL.md` 参照）

## プロファイル

全プロファイルは `profiles/<name>/` に格納。`--profile` のデフォルトは `default`。

各プロファイルに置けるファイル:
- `interest_profile.txt` — 手書きの研究優先事項（人間が編集）
- `inspire_profile.txt` — INSPIRE 自動生成（`tools/setup_inspire.py`）
- `config.yaml` — ルート `config.yaml` へのオーバーライド（ディープマージ）

スコアラーは両プロファイルを結合して使う。どちらか片方だけでも動作する。
月次 INSPIRE 更新は `inspire_profile.txt` のみ上書き、`interest_profile.txt` は不変。

## 開発規約

- Python 3.9+、外部依存は `pyyaml` + `anthropic` のみ
- コード・コメント: 英語、ユーザーとのやりとり: 日本語
- チャンネル追加は `src/channels/base.py` の Channel クラスを継承
- トークン類は環境変数で管理（config.yaml に書かない）。`.env` ファイル（リポルート）からの自動読み込みに対応（`src/config.py` の `load_dotenv()`）。shell 環境変数が `.env` より優先される
- **Mastodon 文字数制限**: インスタンス API から自動取得（`_fetch_instance_char_limit()`）。Vivaldi Social は 1337 文字。URL は常に保護し、文字数超過時は reason → summary の順に切り詰め
- **reason/summary 文字数**: スコアラー（Mode A: `scorer.py`、Mode B: `skill/SKILL.md`）で各最大 120 文字を指示。合計 240 文字以内
- **Mastodon トークン更新手順**: Vivaldi Social は同一ブラウザで1アカウントのみログイン可。odakinarxiv のトークンを操作する場合は、まず odakin をログアウト → odakinarxiv でログイン → `設定 > 開発 > アプリ` でトークン確認/再生成 → 完了後 odakin に戻る

## 将来の拡張（検討中）

- 他の LLM 対応: OpenAI, Gemini 等（scorer のプラグイン化）
- X (Twitter) 対応: API 費用が高いため優先度低
- Web UI: GitHub Pages で結果閲覧（JSON → 静的 HTML）
- 複数ユーザー集約: 同じ分野の研究者がダイジェストを共有
- 無料枠: API 不使用のキーワードマッチングモード（精度は落ちるが費用ゼロ）

## How to Resume（autocompact 復帰手順）

1. `SESSION.md` を読む → 現在の作業状態と次のステップを把握
2. SESSION.md の「次のステップ」に従って作業を継続
3. 不明点があればユーザーに確認

## 自動更新ルール（必須）

- タスク完了時 → SESSION.md を更新
- 重要な判断・ファイル作成/大幅変更時 → SESSION.md に記録
- push 前 → SESSION.md / CLAUDE.md が実態と一致しているか確認（詳細は CONVENTIONS.md §3）
- **`skill/SKILL.md` または `skill/SKILL-takeda.md` を変更した場合**: registered task は symlink なので自動反映される。symlink が壊れていないか確認: `ls -la ~/.claude/scheduled-tasks/arxiv-digest/SKILL.md ~/.claude/scheduled-tasks/arxiv-digest-takeda/SKILL.md`
- CLAUDE.md のルールの詳細は `~/Claude/CONVENTIONS.md` 参照
