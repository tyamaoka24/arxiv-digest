---
name: arxiv-digest
description: 平日朝に arXiv 新着論文をスコアリングし配信
---

arXiv 日刊ダイジェストを実行する。

## 手順

1. `cd ~/Claude/arxiv-digest && python3 -m src.fetch --profile odakin` を実行し、arXiv RSS から新着論文を取得（`.env` の読み込みと環境変数チェックはコード側で自動実行される。エラー終了した場合は表示されたメッセージに従う）
2. `state/today_papers_odakin.json` を読み込む
3. プロファイルと設定を読む:
   - `profiles/odakin/interest_profile.txt`（手書きの研究優先事項）
   - `profiles/odakin/inspire_profile.txt`（INSPIRE 自動生成）
   - `profiles/odakin/config.yaml` の `scoring_instructions` および `style`（tone, emoji_level）
4. 各論文をスコアリング（100点満点、閾値は config.yaml の scoring_threshold）:
   - 研究興味との直接的な重なり → 高スコア
   - 共同研究者の論文 → 高スコア
   - 関連手法・結果 → 中スコア
   - 分野の一般的な発展 → 低スコア
5. 閾値以上の論文について、config.yaml の language で推薦文と要約を生成:
   - 推薦文（reason）: この論文がなぜ面白いか（**最大120文字**、config.yaml の style.tone に従う）
   - 要約（summary）: 技術的内容の簡潔な説明（**最大120文字**）
   - 絵文字の量は config.yaml の style.emoji_level に従う（none/light/moderate/heavy）
   - Mastodon 投稿の文字数制限に収めるため、reason + summary は合計240文字以内を厳守
6. スコア結果を `state/scored_papers_odakin.json` に JSON で書き出す:
   ```json
   {
     "total_fetched": 133,
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
7. `python3 -m src.post --profile odakin` を実行し、scored_papers_odakin.json を読んでチャンネルに配信
8. 配信した論文の著者に profiles/ 登録者（`inspire_bai` 設定あり）がいた場合、`python3 -c "from src.profile_update import check_for_profile_updates; import json; papers=json.load(open('state/today_papers_odakin.json'))['papers']; check_for_profile_updates(papers)"` を実行し、INSPIRE プロファイルを自動更新

## 注意
- config.yaml のチャンネル設定に従って配信
- 環境変数（MASTODON_ACCESS_TOKEN 等）が必要。`.env` ファイル（リポルート）または shell 環境変数で設定する。`.env` は `src/post.py` が自動読み込みする
- 新しいデバイスでは必ず `.env` ファイルを作成すること（`.env` は `.gitignore` に入っているため git clone では取得されない）
- 土日は arXiv 更新なし（fetch が自動スキップ）
- 日によって0件でも8件でもOK（閾値で自然に3-5件/日が目安）

## エラー時
- いずれかのステップでエラーが発生した場合、ユーザーに報告する
- Python スクリプトのエラーは exit code 非ゼロで検知できる
- エラー内容と、考えられる原因・対処法を簡潔に報告する
