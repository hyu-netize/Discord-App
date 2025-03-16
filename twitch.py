import requests
import time
from config import Twitch
from util import get_time


# APIのベースURL
BASE_URL = 'https://api.twitch.tv'

# OAuthトークンを取得するためのURL
OAUTH_URL = 'https://id.twitch.tv/oauth2/token'

# アクセストークンを取得
def get_twitch_oauth_token():
    """TwitchのOAuthトークンを取得する関数"""    
    params = {
        'client_id': Twitch.CLIENT_ID,
        'client_secret': Twitch.CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(OAUTH_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        expires_at = time.time() + data['expires_in']  # 新しいトークンの有効期限
        return access_token, expires_at
    else:
        print(get_time(), f"Twitch APIへのリクエストに失敗しました:", response.status_code)
        return None

# 配信の状態を確認するためのURL
STREAM_URL = f'{BASE_URL}/helix/streams'

def get_stream_status(user_name, access_token):
    """Twitch APIを利用して配信者の配信状態を取得"""
    headers = {
        'Client-ID': Twitch.CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'user_login': user_name
    }
    response = requests.get(STREAM_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            # 配信が開始されている場合、ゲームIDと配信タイトルを取得
            stream_data = data['data'][0]
            title = stream_data['title']
            game_id = stream_data.get('game_id')
            timestamp = int(time.time())  # 現在のUNIXタイムスタンプを取得
            thumbnail_url = stream_data['thumbnail_url'].replace("{width}", "825").replace("{height}", "464")  # サムネイルURL
            thumbnail_url += f"?v={timestamp}"

            # ゲームのジャンルとサムネイルを取得
            game_name, game_thumbnail = get_game_info(game_id, access_token)

            return True, title, thumbnail_url, game_name, game_thumbnail
        else:
            return False, None, None, None, None  # 配信が開始されていない場合
    else:
        print(get_time(), f"Twitch APIへのリクエストに失敗しました:", response.status_code)
        return None, None, None, None, None

# ゲーム情報を取得するためのURL
GAMES_URL = f'{BASE_URL}/helix/games'

def get_game_info(game_id, access_token):
    """ゲームIDからゲーム名とサムネイル情報を取得"""
    headers = {
        'Client-ID': Twitch.CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'id': game_id
    }
    response = requests.get(GAMES_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        game_name = data['data'][0]['name']
        timestamp = int(time.time())  # 現在のUNIXタイムスタンプを取得
        game_thumbnail = data['data'][0]['box_art_url'].replace("{width}", "288").replace("{height}", "384")  # ゲームのサムネイル
        game_thumbnail += f"?v={timestamp}"
        return game_name, game_thumbnail
    return None, None

# ユーザー情報を取得するためのURL
USERS_URL = f'{BASE_URL}/helix/users'

def get_user_info(channel_id, access_token):
    """ ユーザーIDからユーザーサムネイルを取得 """
    headers = {
        'Client-ID': Twitch.CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'login': channel_id
    }
    response = requests.get(USERS_URL, headers=headers, params=params)
    if response.status_code == 200:
        user_data = response.json()
        user_info = user_data['data'][0]
        profile_image_url = user_info['profile_image_url']
        user_thumbnail[channel_id] = profile_image_url
        return
    else:
        print(get_time(), f"Twitch APIへのリクエストに失敗しました:", response.status_code)
        return

def send_discord_notification(channel_id, channel_name, title, thumbnail_url, game_name, game_thumbnail):
    """Discord Webhookに通知を送信"""
    content = {
        "content": f"📢 {channel_name}さんが配信を開始しました！\n視聴リンク: https://www.twitch.tv/{channel_id}",
        "embeds": [
            {
                "author": {
                    "name": channel_name,
                    "icon_url": user_thumbnail[channel_id],
                    "url": f"https://www.twitch.tv/{channel_id}"
                },
                "title": f"{title}",
                "url": f"https://www.twitch.tv/{channel_id}",
                "image": {
                    "url": thumbnail_url
                },
                "footer": {
                    "text": f"ゲーム: {game_name}"
                },
                "thumbnail": {
                    "url": game_thumbnail  # ゲームのサムネイル画像
                }
            }
        ]
    }
    response = requests.post(Twitch.DISCORD_WEBHOOK_URL, json=content)
    if response.status_code == 204:
        print(get_time(), f"{channel_name}の通知を送信しました")
    else:
        print(get_time(), f"{channel_name}の通知の送信に失敗しました:", response.status_code)

user_thumbnail = {}

# メインループ
def main():
    global user_thumbnail

    access_token, expires_at = get_twitch_oauth_token()
    if not access_token:
        print(get_time(), "OAuthトークンの取得に失敗しました")
        return

    # 各チャンネルの配信状況を追跡するための辞書
    live_status = {channel_name: False for channel_name in Twitch.CHANNEL_IDS}

    # 各チャンネルのユーザーサムネイルを格納する辞書
    user_thumbnail = {channel_id: "" for channel_id in Twitch.CHANNEL_IDS.values()}

    for channel_id in Twitch.CHANNEL_IDS.values():
        get_user_info(channel_id, access_token)
        if not user_thumbnail[channel_id]:
            print(get_time(), "ユーザーサムネイルの取得に失敗しました")
            return
        time.sleep(1)

    while True:
        # トークンが期限切れになったら再取得
        if time.time() >= expires_at:
            access_token, expires_at = get_twitch_oauth_token()
            if not access_token:
                print(get_time(), "OAuthトークンの再取得に失敗しました")
                return

        for channel_name, channel_id in Twitch.CHANNEL_IDS.items():
            try:
                # 各チャンネルの配信状況を取得
                is_live, title, thumbnail_url, game_name, game_thumbnail = get_stream_status(channel_id, access_token)

                # 配信が開始されたら通知を送信
                if is_live and not live_status[channel_name]:
                    send_discord_notification(channel_id, channel_name, title, thumbnail_url, game_name, game_thumbnail)
                    live_status[channel_name] = True  # 配信中に更新
                elif not is_live:
                    live_status[channel_name] = False  # 配信が終了した場合

                # 各チャンネルを確認した後に待機
                time.sleep(1)

            except Exception as e:
                print(get_time(), f"{channel_name}のステータス取得中にエラーが発生しました:", e)
                time.sleep(60)

        # 一定時間待機してから再度チェック (60秒間隔)
        time.sleep(60)

if __name__ == "__main__":
    main()
