# arxiv-digest

AI-powered daily arXiv digest for researchers. Get personalized paper recommendations delivered to Mastodon, Discord, Slack, or other channels every morning.

## How It Works

1. Fetches new papers from arXiv RSS feeds in your chosen categories
2. Scores each paper against your research interest profile using Claude
3. Delivers top-scoring papers with recommendations to your preferred channels

## Two Execution Modes

| Mode | Scoring | Cost | Requirements |
|------|---------|------|-------------|
| **A: GitHub Actions** | Anthropic API | ~$0.01/day (Sonnet) | GitHub + API key |
| **B: Local Claude Code** | Claude Code scheduled task | **Free** (Pro Max) | Always-on Mac/PC |

Both modes share the same fetch and publish pipeline. Only the scoring step differs.

## Quick Start (Mode A: GitHub Actions)

1. Click **"Use this template"** > **"Create a new repository"**
   - Choose Private if you want to keep your scoring profile hidden
2. Edit `config.yaml`:
   ```yaml
   language: en                    # en or ja
   scoring_threshold: 80           # 0-100
   arxiv_categories:
     - hep-ph                      # your categories
     - astro-ph.CO
   channels:
     mastodon:
       enabled: true
       instance: "https://mastodon.social"
       mention_target: "@you@mastodon.social"
   style:
     tone: casual                  # casual / formal / neutral
     emoji_level: moderate          # none / light / moderate / heavy
   ```
3. Create your profile in `profiles/default/`:
   - **HEP researchers**: Run `python3 -m tools.setup_inspire --search "Your Name"` to find your INSPIRE BAI and auto-generate `profiles/default/inspire_profile.txt` (or pass your BAI directly: `python3 -m tools.setup_inspire YOUR.BAI.ID`)
   - Edit `profiles/default/interest_profile.txt` to add your personal priorities
   - **Others**: Just edit `profiles/default/interest_profile.txt` from the template
4. Set GitHub Secrets (Settings > Secrets and variables > Actions):
   - `ANTHROPIC_API_KEY` (required)
   - `MASTODON_ACCESS_TOKEN`, `DISCORD_WEBHOOK_URL`, etc. (per your channels)
5. Enable GitHub Actions, then manually trigger from the Actions tab to test

Papers will be delivered every weekday morning (adjust `cron` in `.github/workflows/digest.yml`).

See [docs/setup-guide.md](docs/setup-guide.md) for detailed step-by-step instructions, channel setup, and troubleshooting.

## Quick Start (Mode B: Local Claude Code)

1. Clone this repo
2. Edit `config.yaml` and create your profile(s)
3. `pip install -r requirements.txt`
4. Set environment variables (`MASTODON_ACCESS_TOKEN`, etc.)
5. Symlink `skill/SKILL.md` to your Claude Code scheduled tasks:
   ```bash
   ln -sf ~/Claude/arxiv-digest/skill/SKILL.md ~/.claude/scheduled-tasks/arxiv-digest/SKILL.md
   ```
6. Claude Code handles scoring directly — no API key needed with Pro Max

## Configuration

### `config.yaml`

| Key | Description | Default |
|-----|-------------|---------|
| `language` | Language for recommendations (`en` / `ja`) | `en` |
| `scoring_threshold` | Minimum score to deliver (0-100) | `80` |
| `scoring_model` | Claude model for Mode A | `claude-sonnet-4-6` |
| `arxiv_categories` | arXiv categories to monitor | — |
| `style.tone` | Writing tone: `casual` / `formal` / `neutral` | `neutral` |
| `style.emoji_level` | Emoji density: `none` / `light` / `moderate` / `heavy` | `moderate` |
| `scoring_instructions` | Free-form extra rules for scoring | — |

Per-profile overrides go in `profiles/<name>/config.yaml`. Additional per-profile fields:

| Key | Description |
|-----|-------------|
| `inspire_bai` | INSPIRE BAI (e.g. `K.Y.Oda.1`) — enables auto-update of `inspire_profile.txt` when new papers are detected |

### Research Profile (two-file system)

All profile files live in `profiles/<name>/`. The default profile is `profiles/default/`.

| File | Purpose | Updated by |
|------|---------|-----------|
| `profiles/<name>/interest_profile.txt` | Hand-curated priorities & topics | You (manually) |
| `profiles/<name>/inspire_profile.txt` | Auto-generated from INSPIRE | `setup_inspire.py` |
| `profiles/<name>/config.yaml` | Per-profile config overrides | You (manually) |

The scorer reads both profile files. At least one must exist. Monthly INSPIRE regeneration only touches `inspire_profile.txt`, so your hand-curated priorities are never overwritten.

For multi-user setups, use `--profile <name>` flag with all commands. Without the flag, `default` is used.

### Delivery Channels

| Channel | Auth | Character Limit | Status |
|---------|------|----------------|--------|
| **Mastodon** | Access token | Auto-detected from instance | Available |
| **stdout** | None | None | Available (testing) |
| Bluesky | App password | 300 | Planned |
| **Discord** | Webhook URL | 2000 | Available |
| Slack | Webhook URL | — | Planned |

Tokens and secrets are always set via environment variables, never in `config.yaml`.

## Project Structure

```
arxiv-digest/
├── config.yaml                 # Default settings (base for all profiles)
├── profiles/                   # All profiles live here
│   ├── default/                # Template users edit this
│   │   └── interest_profile.txt
│   └── <name>/                 # Named profiles (optional)
│       ├── config.yaml         # Per-profile config overrides
│       ├── interest_profile.txt
│       └── inspire_profile.txt
├── src/
│   ├── main.py                 # Mode A entry point (fetch → score → publish)
│   ├── fetch.py                # Mode B step 1: fetch → JSON
│   ├── post.py                 # Mode B step 3: JSON → publish
│   ├── fetch_arxiv.py          # arXiv RSS fetcher
│   ├── scorer.py               # Anthropic API scorer (Mode A)
│   ├── profile_update.py       # Auto-update INSPIRE profiles on new papers
│   ├── publish.py              # Channel dispatcher
│   ├── config.py               # Config loader
│   └── channels/
│       ├── discord.py
│       ├── mastodon.py
│       └── stdout.py
├── tools/
│   ├── setup_inspire.py        # Generate profile from INSPIRE
│   └── fetch_inspire.py        # INSPIRE API client
├── skill/
│   └── SKILL.md                # Claude Code scheduled task template
├── templates/
│   └── interest_profile.txt    # Blank profile template
└── .github/workflows/
    └── digest.yml              # GitHub Actions workflow
```

## Requirements

- Python 3.9+
- `pyyaml` (config parsing)
- `anthropic` (Mode A only)

```bash
pip install -r requirements.txt
```

## License

MIT

---

# arxiv-digest (日本語)

研究者向け arXiv 新着論文の AI 日刊ダイジェスト。毎朝、あなたの研究興味に合った論文を Mastodon や Discord などに配信します。

## 仕組み

1. 指定した arXiv カテゴリの RSS から新着論文を取得
2. あなたの研究興味プロファイルに基づき Claude がスコアリング
3. 高スコアの論文を推薦文付きで配信チャンネルに投稿

## 2つの実行モード

| モード | スコアリング | コスト | 必要環境 |
|--------|------------|--------|---------|
| **A: GitHub Actions** | Anthropic API | ~$0.01/日（Sonnet） | GitHub + API キー |
| **B: ローカル Claude Code** | Claude Code scheduled task | **無料**（Pro Max） | 常時起動 Mac/PC |

## セットアップ（モード A: GitHub Actions）

1. **「Use this template」** > **「Create a new repository」** をクリック
   - スコアリング設定を非公開にしたい場合は Private を選択
2. `config.yaml` を編集:
   ```yaml
   language: ja
   scoring_threshold: 80
   arxiv_categories:
     - hep-ph    # あなたの分野
   channels:
     mastodon:
       enabled: true
       instance: "https://mstdn.jp"
       mention_target: "@you@mstdn.jp"
   style:
     tone: casual       # casual / formal / neutral
     emoji_level: heavy  # none / light / moderate / heavy
   ```
3. `profiles/default/` に研究プロファイルを作成:
   - **HEP 系研究者**: `python3 -m tools.setup_inspire --search "名前"` で INSPIRE BAI を検索し `profiles/default/inspire_profile.txt` を自動生成（BAI を知っていれば直接指定も可: `python3 -m tools.setup_inspire YOUR.BAI.ID`）
   - `profiles/default/interest_profile.txt` に個人的な優先事項を記入
   - **その他**: `profiles/default/interest_profile.txt` をテンプレートから編集するだけでOK
4. GitHub Secrets を設定（Settings > Secrets and variables > Actions）:
   - `ANTHROPIC_API_KEY`（必須）
   - `MASTODON_ACCESS_TOKEN` 等（使用するチャンネルに応じて）
5. GitHub Actions を有効化し、Actions タブから手動実行でテスト

平日毎朝自動実行されます（`.github/workflows/digest.yml` の `cron` で時刻調整可能）。

詳細な手順、チャンネル設定、トラブルシューティングは [docs/setup-guide.md](docs/setup-guide.md) を参照。

## セットアップ（モード B: ローカル Claude Code）

1. このリポを clone
2. `config.yaml` と `profiles/default/` の研究プロファイルを設定
3. `pip install -r requirements.txt`
4. 環境変数にトークン類を設定（`~/.zshrc` 等）
5. `skill/SKILL.md` を Claude Code の scheduled task に symlink:
   ```bash
   ln -sf ~/Claude/arxiv-digest/skill/SKILL.md ~/.claude/scheduled-tasks/arxiv-digest/SKILL.md
   ```
6. Claude Code が直接スコアリング — Pro Max なら API キー不要

## 設定項目

### 文体カスタマイズ

`config.yaml` の `style` セクションで、推薦文のトーンと絵文字の量を調整できます:

- **tone**: `casual`（フランク）/ `formal`（学術的）/ `neutral`（中立）
- **emoji_level**: `none`（絵文字なし）/ `light`（控えめ）/ `moderate`（ほどほど）/ `heavy`（たっぷり）

### 配信チャンネル

| チャンネル | 認証 | 状態 |
|-----------|------|------|
| **Mastodon** | アクセストークン | 利用可 |
| **stdout** | なし | 利用可（テスト用） |
| Bluesky | App Password | 計画中 |
| **Discord** | Webhook URL | 利用可 |
| Slack | Webhook URL | 計画中 |

## ライセンス

MIT
