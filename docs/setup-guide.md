# Setup Guide

A step-by-step guide to get arxiv-digest running. Choose Mode A (GitHub Actions) or Mode B (local Claude Code), then configure your delivery channels.

## Mode A: GitHub Actions Setup

### Step 1: Create Your Repository

1. Go to [odakin/arxiv-digest](https://github.com/odakin/arxiv-digest) on GitHub
2. Click **"Use this template"** > **"Create a new repository"**
3. Choose **Private** if you want to keep your scoring profile hidden (recommended)
4. Name it whatever you like (e.g. `my-arxiv-digest`)

### Step 2: Edit `config.yaml`

Open `config.yaml` in GitHub's web editor (click the file, then the pencil icon) and adjust:

```yaml
language: en                    # en = English, ja = Japanese (for recommendations)
scoring_threshold: 80           # Papers scoring >= this get delivered (0-100)
scoring_model: claude-sonnet-4-6  # Claude model for scoring (affects cost/quality)

arxiv_categories:               # arXiv categories to monitor
  - hep-ph                      # Add/remove as needed
  - astro-ph.CO                 # See https://arxiv.org/category_taxonomy

channels:
  mastodon:
    enabled: true               # Set to true for channels you want
    instance: "https://mastodon.social"
    mention_target: "@you@mastodon.social"

style:
  tone: casual                  # casual = conversational, formal = academic, neutral = balanced
  emoji_level: moderate          # none / light / moderate / heavy
```

Key fields:
- **`language`**: Language for generated recommendations and summaries
- **`scoring_threshold`**: Higher = fewer but more relevant papers. 80 is a good starting point
- **`scoring_model`**: `claude-sonnet-4-6` balances cost and quality (~$0.01/day)
- **`arxiv_categories`**: Which arXiv feeds to monitor. List all categories relevant to your field
- **`channels`**: Enable the delivery channels you want (see channel setup sections below)
- **`style`**: Controls the tone and emoji density of recommendation text

### Step 3: Create Your Research Profile

The system uses two profile files (at least one is required):

- **`interest_profile.txt`** — Hand-curated priorities (what you care about most)
- **`inspire_profile.txt`** — Auto-generated statistics from INSPIRE (optional)

#### Path A: HEP Researchers (INSPIRE-HEP)

If you have an INSPIRE-HEP author profile (BAI):

1. Clone your new repo locally: `git clone https://github.com/YOU/my-arxiv-digest.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python3 -m tools.setup_inspire --search "Your Name"` to find your BAI from INSPIRE
   - Alternatively, pass your BAI directly: `python3 -m tools.setup_inspire YOUR.BAI.ID` (e.g. `K.Y.Oda.1`)
4. This fetches your publication history and generates `profiles/default/inspire_profile.txt`
5. Edit `profiles/default/interest_profile.txt` to add your personal priorities (use `templates/interest_profile.txt` as a guide)
6. Commit and push: `git add profiles/default/ && git commit -m "Add profiles" && git push`

Monthly INSPIRE updates only regenerate `inspire_profile.txt` — your hand-curated `interest_profile.txt` is never overwritten.

#### Path B: All Other Researchers

1. Open `templates/interest_profile.txt` for the format
2. Edit `profiles/default/interest_profile.txt` with your research interests
3. Fill in your name, affiliation, research topics, collaborators, and arXiv categories
4. You can do this directly in GitHub's web editor — no local clone needed
5. You don't need `inspire_profile.txt` at all

### Step 4: Set GitHub Secrets

Go to your repo's **Settings > Secrets and variables > Actions > New repository secret** and add:

| Secret | Required? | Description |
|--------|-----------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | Your Anthropic API key from [console.anthropic.com](https://console.anthropic.com/) |
| `MASTODON_ACCESS_TOKEN` | If Mastodon enabled | See [Mastodon channel setup](#mastodon-channel-setup) below |
| `DISCORD_WEBHOOK_URL` | If Discord enabled | See [Discord channel setup](#discord-channel-setup) below |

> Note: Bluesky and Slack channels are planned but not yet implemented.

### Step 5: Enable GitHub Actions

1. Go to **Settings > Actions > General**
2. Under "Actions permissions", select **"Allow all actions and reusable workflows"**
3. Click **Save**

### Step 6: Manual Test Run

1. Go to the **Actions** tab in your repo
2. Click **"arXiv Daily Digest"** in the left sidebar
3. Click **"Run workflow"** > **"Run workflow"** (the green button)
4. Wait a minute or two, then check your delivery channel

If the run fails, click on it to see logs and debug.

### Step 7: Adjust Schedule (Optional)

The default schedule is **UTC 01:30, weekdays only** (= JST 10:30). To change it, edit `.github/workflows/digest.yml`:

```yaml
on:
  schedule:
    - cron: '30 1 * * 1-5'  # minute hour * * day-of-week (0=Sun, 1-5=Mon-Fri)
```

Examples:
- `'0 14 * * 1-5'` = UTC 14:00 (JST 23:00), weekdays
- `'30 1 * * *'` = UTC 01:30, every day including weekends

Note: arXiv does not update on weekends/US holidays, so weekend runs will find no new papers.

---

## Mode B: Local Claude Code Setup

This mode uses Claude Code's scheduled tasks for scoring. With a Pro Max subscription, scoring is free (no API key needed).

### Step 1: Clone the Repo

```bash
git clone https://github.com/YOU/my-arxiv-digest.git ~/Claude/arxiv-digest
cd ~/Claude/arxiv-digest
```

### Step 2: Edit Configuration

Edit `config.yaml` and create your profile in `profiles/default/` as described in Mode A Steps 2-3 above.

For INSPIRE users, auto-generate the statistics profile:

```bash
pip install -r requirements.txt
python3 -m tools.setup_inspire --search "Your Name"  # search by name, or:
python3 -m tools.setup_inspire YOUR.BAI.ID             # pass BAI directly
```

Then edit `profiles/default/interest_profile.txt` with your personal priorities, or use `templates/interest_profile.txt` as a guide.

### Step 3: Set Environment Variables

Create a `.env` file in the repo root with your channel tokens:

```bash
# ~/Claude/arxiv-digest/.env
MASTODON_ACCESS_TOKEN=your-token-here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

The `.env` file is automatically loaded by `src/post.py` and `src/main.py`. It is listed in `.gitignore`, so it will not be committed to git.

> **Important for multi-device setups:** The `.env` file is NOT synced by git. When setting up on a new device, you must create this file again with the correct tokens. The system will show a clear error if required tokens are missing.

Alternatively, you can add tokens to `~/.zshrc` (or `~/.bashrc`):

```bash
export MASTODON_ACCESS_TOKEN="your-token-here"
```

Then reload: `source ~/.zshrc`

Environment variables set in the shell take precedence over `.env` values.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test the Fetch Step

```bash
python3 -m src.fetch
```

Check the output at `state/today_papers.json`. This file contains the raw paper list from arXiv. If it is empty or missing, check that your `arxiv_categories` in `config.yaml` are valid and that arXiv has new papers today (no updates on weekends/holidays).

### Step 6: Set Up Claude Code Scheduled Task

1. In Claude Code, create a scheduled task for `arxiv-digest` (weekday mornings, e.g. 10:30 JST)
2. Replace the registered SKILL.md with a symlink to the repo's copy:
   ```bash
   ln -sf ~/Claude/arxiv-digest/skill/SKILL.md ~/.claude/scheduled-tasks/arxiv-digest/SKILL.md
   ```
   This ensures the task definition stays in sync when the repo is updated.

### Step 7: Daily Automatic Execution

Once the scheduled task is set up, Claude Code will automatically:
1. Run `python3 -m src.fetch` to get new papers
2. Score each paper against your interest profile (Claude does this directly, no API call)
3. Run `python3 -m src.post` to deliver scored papers to your channels

No `ANTHROPIC_API_KEY` is needed in this mode -- Claude Code handles scoring via its own authentication.

---

## Mastodon Channel Setup

### Create a Bot Account (Recommended)

1. Register a new account on your preferred Mastodon instance (e.g. mastodon.social, mstdn.jp, social.vivaldi.net)
2. In the account's profile settings, consider marking it as a "bot" account

Or use your existing Mastodon account if you prefer.

### Get an Access Token

1. Log in to your Mastodon instance's web UI
2. Go to **Preferences > Development > New Application**
3. Name it something like "arxiv-digest"
4. Required scopes: **`read`** and **`write`** (specifically `write:statuses`)
5. Click **Submit**
6. Click on the newly created application
7. Copy the **"Your access token"** value

### Configure

- **Mode A (GitHub Actions)**: Add the token as a GitHub Secret named `MASTODON_ACCESS_TOKEN`
- **Mode B (Local)**: Set the environment variable: `export MASTODON_ACCESS_TOKEN="your-token-here"`

In `config.yaml`, set:
```yaml
channels:
  mastodon:
    enabled: true
    instance: "https://mastodon.social"   # Your instance URL
    mention_target: "@you@mastodon.social" # Your main account to mention (optional)
```

---

## Discord Channel Setup

### Create a Webhook

1. Open your Discord server
2. Go to the channel where you want papers delivered
3. Click **Edit Channel** (gear icon) > **Integrations** > **Webhooks**
4. Click **New Webhook**
5. Name it (e.g. "arXiv Digest") and optionally set an avatar
6. Click **Copy Webhook URL**

### Configure

- **Mode A (GitHub Actions)**: Add the URL as a GitHub Secret named `DISCORD_WEBHOOK_URL`
- **Mode B (Local)**: Set the environment variable: `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`

In `config.yaml`, set:
```yaml
channels:
  discord:
    enabled: true
    username: "arXiv Digest"   # Bot display name (optional, default: "arXiv Digest")
```

---

## Troubleshooting

### No papers found

- **Weekend or US holiday**: arXiv does not publish new papers on weekends or US federal holidays. This is normal. The fetch step will complete with zero papers.
- **Wrong categories**: Check that your `arxiv_categories` in `config.yaml` are valid arXiv category IDs (e.g. `hep-ph`, not `hep` or `high-energy-physics`). See the [arXiv category taxonomy](https://arxiv.org/category_taxonomy).

### API key invalid (Mode A)

- Verify your `ANTHROPIC_API_KEY` GitHub Secret is set correctly (no extra spaces or newlines)
- Check that your API key is active at [console.anthropic.com](https://console.anthropic.com/)
- Ensure you have billing set up and sufficient credits

### Mastodon token expired or invalid

- Mastodon access tokens do not expire by default, but can be revoked
- If posting fails, regenerate the token: Preferences > Development > your app > regenerate token
- Update the GitHub Secret or environment variable with the new token

### GitHub Actions not running

- Ensure Actions are enabled: Settings > Actions > General > "Allow all actions"
- Scheduled workflows may be disabled if the repo has had no activity for 60 days. Push a commit or manually trigger to re-enable
- Check the Actions tab for error logs

### Scoring threshold too high/low

- If you get no recommendations, try lowering `scoring_threshold` (e.g. from 80 to 60)
- If you get too many, raise it (e.g. from 80 to 85)
- Typical range: 60-85 delivers 2-5 papers per day, depending on your field

---

# セットアップガイド

arxiv-digest を動かすためのステップバイステップガイドです。モード A（GitHub Actions）またはモード B（ローカル Claude Code）を選び、配信チャンネルを設定してください。

## モード A: GitHub Actions セットアップ

### ステップ 1: リポジトリを作成

1. GitHub で [odakin/arxiv-digest](https://github.com/odakin/arxiv-digest) にアクセス
2. **「Use this template」** > **「Create a new repository」** をクリック
3. スコアリング設定を非公開にしたい場合は **Private** を選択（推奨）
4. 名前は自由に（例: `my-arxiv-digest`）

### ステップ 2: `config.yaml` を編集

GitHub の Web エディタで `config.yaml` を開き（ファイルをクリック → 鉛筆アイコン）、以下を調整:

```yaml
language: ja                    # en = 英語, ja = 日本語（推薦文の言語）
scoring_threshold: 80           # この点数以上の論文を配信（0-100）
scoring_model: claude-sonnet-4-6  # スコアリング用モデル（コストと品質のバランス）

arxiv_categories:               # 監視する arXiv カテゴリ
  - hep-ph                      # 必要に応じて追加・削除
  - astro-ph.CO                 # 一覧: https://arxiv.org/category_taxonomy

channels:
  mastodon:
    enabled: true               # 使いたいチャンネルを true に
    instance: "https://mstdn.jp"
    mention_target: "@you@mstdn.jp"

style:
  tone: casual                  # casual = フランク, formal = 学術的, neutral = 中立
  emoji_level: moderate          # none / light / moderate / heavy
```

主な設定項目:
- **`language`**: 推薦文・要約の言語
- **`scoring_threshold`**: 高くすると厳選、低くすると多めに配信。80 が目安
- **`scoring_model`**: `claude-sonnet-4-6` がコストと品質のバランスが良い（~$0.01/日）
- **`arxiv_categories`**: 監視する arXiv カテゴリ。自分の分野を全て列挙
- **`channels`**: 使う配信チャンネルを有効化（詳細は下記）
- **`style`**: 推薦文のトーンと絵文字の量を調整

### ステップ 3: 研究プロファイルを作成

2つのプロファイルファイルがあります（少なくとも1つが必要）:

- **`interest_profile.txt`** — 手書きの優先事項（自分が最も興味あるテーマ）
- **`inspire_profile.txt`** — INSPIRE から自動生成（オプション）

#### パス A: HEP 系研究者（INSPIRE-HEP）

INSPIRE-HEP に著者プロファイル（BAI）がある場合:

1. リポをローカルにクローン: `git clone https://github.com/YOU/my-arxiv-digest.git`
2. 依存パッケージをインストール: `pip install -r requirements.txt`
3. 実行: `python3 -m tools.setup_inspire --search "名前"`（名前から INSPIRE BAI を検索）
   - BAI を知っていれば直接指定も可: `python3 -m tools.setup_inspire K.Y.Oda.1`
4. INSPIRE から出版履歴を取得し、`profiles/default/inspire_profile.txt` を自動生成
5. `profiles/default/interest_profile.txt` に個人的な優先事項を記入（`templates/interest_profile.txt` を参考に）
6. コミット & プッシュ: `git add profiles/default/ && git commit -m "Add profiles" && git push`

月次 INSPIRE 更新は `inspire_profile.txt` のみ上書き。手書きの `interest_profile.txt` は一切触りません。

#### パス B: その他の研究者

1. `templates/interest_profile.txt` のフォーマットを参考にする
2. `profiles/default/interest_profile.txt` を自分のプロファイルで編集
3. 名前、所属、研究トピック、共同研究者、arXiv カテゴリを記入
4. GitHub の Web エディタで直接編集可能（ローカルクローン不要）
5. `inspire_profile.txt` は不要

### ステップ 4: GitHub Secrets を設定

リポの **Settings > Secrets and variables > Actions > New repository secret** で追加:

| Secret 名 | 必須？ | 説明 |
|-----------|--------|------|
| `ANTHROPIC_API_KEY` | **必須** | [console.anthropic.com](https://console.anthropic.com/) の API キー |
| `MASTODON_ACCESS_TOKEN` | Mastodon 使用時 | 下記 [Mastodon チャンネルセットアップ](#mastodon-チャンネルセットアップ) 参照 |
| `DISCORD_WEBHOOK_URL` | Discord 使用時 | 下記 [Discord チャンネルセットアップ](#discord-チャンネルセットアップ) 参照 |

> 注: Bluesky、Slack チャンネルは計画中で未実装です。

### ステップ 5: GitHub Actions を有効化

1. **Settings > Actions > General** に移動
2. 「Actions permissions」で **「Allow all actions and reusable workflows」** を選択
3. **Save** をクリック

### ステップ 6: 手動テスト実行

1. リポの **Actions** タブに移動
2. 左サイドバーで **「arXiv Daily Digest」** をクリック
3. **「Run workflow」** > **「Run workflow」**（緑のボタン）をクリック
4. 1-2 分待ち、配信チャンネルを確認

失敗した場合はクリックしてログを確認。

### ステップ 7: スケジュール調整（任意）

デフォルトは **UTC 01:30、平日のみ**（= JST 10:30）。変更するには `.github/workflows/digest.yml` を編集:

```yaml
on:
  schedule:
    - cron: '30 1 * * 1-5'  # 分 時 * * 曜日 (0=日, 1-5=月-金)
```

例:
- `'0 14 * * 1-5'` = UTC 14:00（JST 23:00）、平日
- `'30 1 * * *'` = UTC 01:30、土日含む毎日

注意: arXiv は週末・米国祝日に更新されないため、週末の実行では新着論文は見つかりません。

---

## モード B: ローカル Claude Code セットアップ

このモードは Claude Code の scheduled task でスコアリングします。Pro Max 契約があれば、スコアリングは無料です（API キー不要）。

### ステップ 1: リポをクローン

```bash
git clone https://github.com/YOU/my-arxiv-digest.git ~/Claude/arxiv-digest
cd ~/Claude/arxiv-digest
```

### ステップ 2: 設定を編集

モード A のステップ 2-3 と同じ手順で `config.yaml` と `profiles/default/` の研究プロファイルを設定。

INSPIRE ユーザーは統計プロファイルを自動生成できます:

```bash
pip install -r requirements.txt
python3 -m tools.setup_inspire --search "名前"  # 名前から BAI を検索、または:
python3 -m tools.setup_inspire YOUR.BAI.ID             # BAI を直接指定
```

`profiles/default/interest_profile.txt` は `templates/interest_profile.txt` を参考に個人的な優先事項を記入。

### ステップ 3: 環境変数を設定

リポのルートに `.env` ファイルを作成し、チャンネルトークンを記入:

```bash
# ~/Claude/arxiv-digest/.env
MASTODON_ACCESS_TOKEN=your-token-here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

`.env` ファイルは `src/post.py` と `src/main.py` が自動的に読み込みます。`.gitignore` に含まれているため、git にはコミットされません。

> **マルチデバイス運用の注意:** `.env` ファイルは git で同期されません。新しいデバイスでセットアップする際は、正しいトークンで `.env` を再作成してください。トークンが未設定の場合、明確なエラーメッセージが表示されます。

代替として、`~/.zshrc`（または `~/.bashrc`）に追加することもできます:

```bash
export MASTODON_ACCESS_TOKEN="your-token-here"
```

反映: `source ~/.zshrc`

shell の環境変数が `.env` の値より優先されます。

### ステップ 4: 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### ステップ 5: fetch のテスト

```bash
python3 -m src.fetch
```

`state/today_papers.json` に出力を確認。arXiv の新着論文リストが入っています。ファイルが空や存在しない場合は、`config.yaml` の `arxiv_categories` が正しいか、今日が平日かを確認してください（週末・祝日は更新なし）。

### ステップ 6: Claude Code Scheduled Task を設定

1. Claude Code で `arxiv-digest` のスケジュールタスクを作成（平日朝、例: JST 10:30）
2. 登録された SKILL.md をリポへの symlink に置き換える:
   ```bash
   ln -sf ~/Claude/arxiv-digest/skill/SKILL.md ~/.claude/scheduled-tasks/arxiv-digest/SKILL.md
   ```
   リポ更新時にタスク定義が自動で同期される。

### ステップ 7: 毎日自動実行

scheduled task が設定されると、Claude Code が毎朝自動的に:
1. `python3 -m src.fetch` で新着論文を取得
2. 興味プロファイルに基づいて各論文をスコアリング（Claude が直接実行、API 呼び出しなし）
3. `python3 -m src.post` でスコア結果をチャンネルに配信

このモードでは `ANTHROPIC_API_KEY` は不要です。Claude Code が自身の認証でスコアリングを行います。

---

## Mastodon チャンネルセットアップ

### ボットアカウントの作成（推奨）

1. お好みの Mastodon インスタンス（mastodon.social, mstdn.jp, social.vivaldi.net 等）で新しいアカウントを登録
2. プロフィール設定で「ボット」アカウントとしてマークすることを推奨

既存の Mastodon アカウントを使うこともできます。

### アクセストークンの取得

1. Mastodon インスタンスの Web UI にログイン
2. **設定 > 開発 > 新規アプリ** に移動
3. 名前を入力（例: "arxiv-digest"）
4. 必要なスコープ: **`read`** と **`write`**（特に `write:statuses`）
5. **送信** をクリック
6. 作成されたアプリをクリック
7. **「アクセストークン」** の値をコピー

### 設定

- **モード A（GitHub Actions）**: `MASTODON_ACCESS_TOKEN` として GitHub Secret に追加
- **モード B（ローカル）**: 環境変数を設定: `export MASTODON_ACCESS_TOKEN="your-token-here"`

`config.yaml` で以下を設定:
```yaml
channels:
  mastodon:
    enabled: true
    instance: "https://mstdn.jp"          # あなたのインスタンス URL
    mention_target: "@you@mstdn.jp"       # メンション先（任意）
```

---

## Discord チャンネルセットアップ

### Webhook の作成

1. Discord サーバーを開く
2. 論文を配信したいチャンネルに移動
3. **チャンネル編集**（歯車アイコン）> **連携サービス** > **ウェブフック** をクリック
4. **新しいウェブフック** をクリック
5. 名前を入力（例: "arXiv Digest"）、アバターは任意
6. **ウェブフック URL をコピー** をクリック

### 設定

- **モード A（GitHub Actions）**: `DISCORD_WEBHOOK_URL` として GitHub Secret に追加
- **モード B（ローカル）**: 環境変数を設定: `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`

`config.yaml` で以下を設定:
```yaml
channels:
  discord:
    enabled: true
    username: "arXiv Digest"   # ボット表示名（任意、デフォルト: "arXiv Digest"）
```

---

## トラブルシューティング

### 論文が見つからない

- **週末または米国祝日**: arXiv は週末・米国連邦祝日に新着論文を公開しません。これは正常です。fetch は0件で完了します。
- **カテゴリが不正**: `config.yaml` の `arxiv_categories` が正しい arXiv カテゴリ ID か確認してください（`hep-ph` であって `hep` や `high-energy-physics` ではない）。[arXiv カテゴリ一覧](https://arxiv.org/category_taxonomy) を参照。

### API キーが無効（モード A）

- `ANTHROPIC_API_KEY` の GitHub Secret が正しく設定されているか確認（余分なスペースや改行がないか）
- [console.anthropic.com](https://console.anthropic.com/) で API キーが有効か確認
- 課金設定と残高を確認

### Mastodon トークンが失効・無効

- Mastodon のアクセストークンはデフォルトでは失効しませんが、取り消される可能性があります
- 投稿に失敗する場合はトークンを再生成: 設定 > 開発 > アプリ > トークン再生成
- GitHub Secret または環境変数を新しいトークンで更新

### GitHub Actions が実行されない

- Actions が有効か確認: Settings > Actions > General > "Allow all actions"
- リポに60日間アクティビティがないと、スケジュールワークフローが無効化されることがあります。コミットをプッシュするか手動トリガーで再有効化
- Actions タブでエラーログを確認

### スコアリング閾値が高すぎる/低すぎる

- 推薦が来ない場合は `scoring_threshold` を下げてみる（例: 80 → 60）
- 多すぎる場合は上げる（例: 80 → 90）
- 目安: 60-85 で1日2-5件程度（分野により変動）
