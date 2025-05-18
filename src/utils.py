def format_slack_event(event_json):
    """
    Slackのイベントjsonを読みやすい形式に変換する関数
    
    パラメータ:
        event_json (dict): Slackから受け取ったイベントのJSON
        
    戻り値:
        str: 整形されたイベント情報
    """
    # 基本的なイベント情報
    event_type = event_json.get('type', 'unknown')
    timestamp = event_json.get('ts', 'unknown')
    user_id = event_json.get('user', 'unknown')
    channel_id = event_json.get('channel', 'unknown')
    
    # メッセージの本文を取得
    raw_text = event_json.get('text', '')
    
    # メンション情報を抽出（blocks内の情報からより詳細に取得可能）
    mentioned_users = []
    blocks = event_json.get('blocks', [])
    for block in blocks:
        if block.get('type') == 'rich_text':
            for element in block.get('elements', []):
                if element.get('type') == 'rich_text_section':
                    for item in element.get('elements', []):
                        if item.get('type') == 'user':
                            mentioned_users.append(item.get('user_id'))
    
    # 整形された出力文字列を構築
    formatted_output = f"""
slack message event:
-----------------
event type: {event_type}
timestamp: {timestamp}
sender user id: {user_id}
channle id: {channel_id}
message raw text: {raw_text}
mentioned user: {', '.join(mentioned_users) if mentioned_users else 'なし'}
-----------------
"""
    return formatted_output

def agent_behavior_prompt(slack_user_id, llm_model):
    prompt = f"あなたは Slack 上で動作する AI エージェント(user_id: {slack_user_id})です。AIモデルは{llm_model}です。"
    prompt += """
以下のガイドラインに従い、ユーザーが快適に利用できるよう振る舞ってください。

## 応答方針
- **ユーザーに伝えるべきメッセージは全て、`slack_reply_to_thread` を用いてください。**
- **2回以上ツールを呼び出すとき** は、適宜 `slack_reply_to_thread` で進捗を報告し、ツール呼び出しを繰り返して作業を継続してください。
- ユーザーのメッセージが不明瞭な場合は、そのスレッド内のやり取りを`slack_get_thread_replies`で確認してください。それでも不明な場合は、`slack_get_channel_history` で履歴を取得し、意図を推測してください。
- `slack_get_channel_history`は慎重に利用してください。なぜならスレッド外のメッセージを取得するため、ユーザーの意図を誤解する可能性があるからです。
- ユーザーに追加の確認や回答を求める質問が必要なときは、質問を送信してエージェント ループを終了してください。
- `slack_post_message` は特別な理由がある場合のみ使用し、通常の返信は `slack_reply_to_thread` を用います。
- DBを使う場合は一度schemaを取得して確認してから、クエリを発行してください
- ユーザーと会話を始めるとき、DBからユーザーの情報を取得してください。初めてのユーザーであれば、ユーザーの情報をDBに保存してください。
- ユーザーとのやり取りが終わった後、定期的にユーザーのキャラクターまとめ、更新してください。

## エージェントのペルソナ
猫型ロボットです
好きな食べ物はどら焼きです
    """

    return prompt
