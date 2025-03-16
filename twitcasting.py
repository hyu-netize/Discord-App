import base64
import requests
import time
from config import TwitCasting
from util import get_time


id_secret = f'{TwitCasting.CLIENT_ID}:{TwitCasting.CLIENT_SECRET}'
BASE64_ENCODED_STRING = base64.b64encode(id_secret.encode()).decode()

def get_live_status(channel_id):
    """指定したユーザーの配信状況を取得する関数"""
    url = f"https://apiv2.twitcasting.tv/users/{channel_id}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {BASE64_ENCODED_STRING}',
        'X-Api-Version': '2.0'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        user = data.get('user')
        if user:
            return user['is_live'], user['last_movie_id']
    else:
        print(get_time(), f"TwitCasting APIのリクエストに失敗しました: {response.status_code}")
    return False, None

def send_discord_notification(channel_name, channel_id, movie_id):
    """Discord Webhookに配信開始を通知する関数"""
    content = {
        "content": f"📢 {channel_name}さんが配信を開始しました！\n"
                   f"視聴リンク: https://twitcasting.tv/{channel_id}"
    }
    response = requests.post(TwitCasting.DISCORD_WEBHOOK_URL, json=content)
    if response.status_code == 204:
        print(get_time(), f"{channel_name}さんの配信開始通知を送信しました")
    else:
        print(get_time(), f"{channel_name}さんの通知の送信に失敗しました:", response.status_code)

# 配信状況を追跡する辞書
live_status = {channel_name: False for channel_name in TwitCasting.CHANNEL_IDS}

# メインループ
while True:
    for channel_name, channel_id in TwitCasting.CHANNEL_IDS.items():
        try:
            # 最新の配信状況を取得
            is_live, movie_id = get_live_status(channel_id)

            # 配信が始まったら通知を送信
            if is_live and not live_status[channel_name]:
                send_discord_notification(channel_name, channel_id, movie_id)
                live_status[channel_name] = True  # 配信中に更新
            elif not is_live:
                live_status[channel_name] = False  # 配信が終了した場合

            # 各チャンネルを確認した後に待機
            time.sleep(2)

        except Exception as e:
            print(get_time(), f"{channel_name}のステータス取得中にエラーが発生しました:", e)
            time.sleep(60)

    # 一定時間待機してから再度チェック (60秒間隔)
    time.sleep(60)
