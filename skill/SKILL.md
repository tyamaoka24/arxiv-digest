---
name: arxiv-digest
description: 平日朝に arXiv 新着論文を全プロファイル一括でスコアリングし配信
---

arXiv 日刊ダイジェストを全プロファイル分まとめて実行する。

## ステップ0: SESSION.md チェック

`SESSION.md` の「要対応」セクションに未完了タスク（`- [ ]`）があれば、ダイジェスト実行前に対応する。

## 手順

### ステップ1: 一括 fetch

`cd ~/Claude/arxiv-digest && python3 -m src.fetch_all` を実行。全アクティブプロファイルのカテゴリを union して1回の RSS 取得で済ませる。

土日は自動スキップ。エラー終了した場合は表示されたメッセージに従う。

### ステップ2: プロファイルごとにスコアリング

`state/` に生成された `today_papers_{profile}.json` を **プロファイルごとに順番に** 処理する。

各プロファイルについて:

1. `state/today_papers_{profile}.json` を読み込む
2. `profiles/{profile}/` のプロファイルファイルと `config.yaml` の設定（scoring_instructions, style）を確認する
3. 各論文をスコアリング（100点満点、閾値は config の scoring_threshold）:
   - 研究興味との直接的な重なり → 高スコア
   - 共同研究者の論文 → 高スコア
   - 関連手法・結果 → 中スコア
   - 分野の一般的な発展 → 低スコア
4. 閾値以上の論文について、config の language で推薦文と要約を生成:
   - 推薦文（reason）: この論文がなぜ面白いか（**最大120文字**、style.tone に従う）
   - 要約（summary）: 技術的内容の簡潔な説明（**最大120文字**）
   - 絵文字の量は style.emoji_level に従う（none/light/moderate/heavy）
   - reason + summary は合計240文字以内を厳守
5. スコア結果を `state/scored_papers_{profile}.json` に JSON で書き出す:
   ```json
   {
     "total_fetched": 155,
     "scored_papers": [
       {
         "arxiv_id": "2503.12345",
         "title": "...",
         "authors": ["..."],
         "categories": ["hep-ph"],
         "url": "https://arxiv.org/abs/2503.12345",
         "abstract": "...",
         "score": 85,
         "reason": "推薦文...",
         "summary": "要約..."
       }
     ]
   }
   ```

### ステップ3: 一括 post

`python3 -m src.post_all` を実行。全プロファイルの scored_papers を読んでチャンネルに配信。1プロファイルがエラーでも残りは続行する。配信成功後、`archive/{year}/{month}/` に自動アーカイブされる。

### ステップ4: INSPIRE プロファイル更新

配信した論文の著者に profiles/ 登録者（`inspire_bai` 設定あり）がいた場合、以下を実行（`{profile}` は任意のアクティブプロファイル名。fetch_all で全ファイルに同じ論文が入るため、どれを使っても同じ）:

```
python3 -c "from src.profile_update import check_for_profile_updates; import json, glob; f=glob.glob('state/today_papers_*.json')[0]; papers=json.load(open(f))['papers']; check_for_profile_updates(papers)"
```

## 注意
- 環境変数（MASTODON_ACCESS_TOKEN, DISCORD_WEBHOOK_URL_TAKEDA 等）が必要。`.env` ファイル（リポルート）または shell 環境変数で設定する
- 新しいデバイスでは `.env` ファイルを作成すること
- 日によって0件でも8件でもOK（閾値で自然に数件/日が目安）
- プロファイル追加は `profiles/<name>/` にファイルを置くだけで自動認識される

## エラー時
- いずれかのステップでエラーが発生した場合、ユーザーに報告する
- Python スクリプトのエラーは exit code 非ゼロで検知できる
- エラー内容と、考えられる原因・対処法を簡潔に報告する