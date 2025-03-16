import requests
import time
from config import YouTube
from util import get_time


# APIのベースURL
BASE_URL = 'https://www.googleapis.com/youtube/v3'

def get_channels(channel_id):
    """Step 1: チャンネル情報からアップロードプレイリストIDを取得"""
    channel_url = f"{BASE_URL}/channels?key={YouTube.API_KEY}&id={channel_id}&part=contentDetails"
    channel_response = requests.get(channel_url)
    
    if channel_response.status_code == 200:
        channel_data = channel_response.json()
        if 'items' in channel_data and len(channel_data['items']) > 0:
            # アップロードプレイリストIDを取得
            upload_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            thumbnails = channel_data['items'][0]['snippet']['thumbnails']
            # 解像度に応じたサムネイルURLを取得
            thumbnail_url = thumbnails["default"]["url"]  # ['medium']['url']や['high']['url']も選択可能
            return upload_playlist_id, thumbnail_url
        else:
            print(get_time(), "チャンネルデータが取得できませんでした。")
            return None
    else:
        print(get_time(), f"チャンネル情報の取得に失敗しました: {channel_response.status_code}")
        return None

def get_playlist_items(upload_playlist_id):
    """Step 2: アップロードプレイリストから最新動画のIDを取得"""
    playlist_url = f"{BASE_URL}/playlistItems?key={YouTube.API_KEY}&playlistId={upload_playlist_id}&part=snippet&maxResults=1"
    playlist_response = requests.get(playlist_url)
    
    if playlist_response.status_code == 200:
        playlist_data = playlist_response.json()
        if 'items' in playlist_data and len(playlist_data['items']) > 0:
            video_id = playlist_data['items'][0]['snippet']['resourceId']['videoId']
            title = playlist_data['items'][0]['snippet']['title']
            return video_id, title
        else:
            print(get_time(), "プレイリストデータが取得できませんでした。")
            return None, None
    else:
        print(get_time(), f"プレイリスト情報の取得に失敗しました: {playlist_response.status_code}")
        return None, None

def get_videos(video_id):
    """Step 3: 動画の詳細情報を取得"""
    video_url = f"{BASE_URL}/videos?key={YouTube.API_KEY}&id={video_id}&part=snippet,liveStreamingDetails"
    video_response = requests.get(video_url)
    
    if video_response.status_code == 200:
        video_data = video_response.json()
        if 'items' in video_data and len(video_data['items']) > 0:
            is_live = video_data['items'][0]['snippet']['liveBroadcastContent'] == 'live'
            return is_live
    else:
        print(get_time(), f"動画情報の取得に失敗しました: {video_response.status_code}")
    
    return None


def send_discord_notification(channel_name, video_id, title, is_live):
    """DiscordのWebhookに通知を送信する関数"""
    content = {
        "content": f"📢 {f'{channel_name}さんがライブ配信を開始しました！\n' if is_live else f'{channel_name}さんが動画を投稿しました！'}\n"
                   f"視聴リンク: https://www.youtube.com/watch?v={video_id}"
    }
    response = requests.post(YouTube.DISCORD_WEBHOOK_URL, json=content)
    if response.status_code == 204:
        print(get_time(), f"{channel_name} の通知を送信しました")
    else:
        print(get_time(), f"{channel_name} の通知の送信に失敗しました:", response.status_code)


""" プレイリストIDはチャンネルIDの左から二番目を「U」に変えた文字列とわかったので、処理を省略 """
# # 各チャンネルのプレイリストIDを格納する辞書
# upload_playlist_ids = {channel_id: "" for channel_id in YouTube.CHANNEL_IDS.values()}
# thumbnail_urls = {channel_id: "" for channel_id in YouTube.CHANNEL_IDS.values()}
# for channel_name, channel_id in YouTube.CHANNEL_IDS.items():
#     try:
#         # APIで各チャンネルのプレイリストIDを取得
#         upload_playlist_id, thumbnail_url = get_channels(channel_id)
#         if upload_playlist_id and thumbnail_url:
#             # 最後に確認した動画IDを更新
#             upload_playlist_ids[channel_id] = upload_playlist_id
#             thumbnail_urls[channel_id] = thumbnail_url
#         else:
#             exit
#     except Exception as e:
#         print(get_time(), f"{channel_name}の初期データ取得中にエラーが発生しました:", e)
#         exit
#     time.sleep(1)
# print(get_time(), "初回実行: 最新のプレイリストID情報を記録しました")

# 各チャンネルのプレイリストIDを格納する辞書
upload_playlist_ids = {channel_id: (channel_id[:1] + 'U' + channel_id[2:]) for channel_id in YouTube.CHANNEL_IDS.values()}
# 各チャンネルの最新動画IDを格納する辞書
last_video_ids = {channel_id: "" for channel_id in YouTube.CHANNEL_IDS.values()}

is_first_run = True

# メインループ
while True:
    for channel_name, channel_id in YouTube.CHANNEL_IDS.items():
        try:
            # 各チャンネルの最新の動画情報を取得
            video_id, title = get_playlist_items(upload_playlist_ids[channel_id])

            # 新しい動画またはライブ配信が始まった場合に通知を送信（最初の実行時は除く）
            if video_id and (video_id != last_video_ids[channel_id]):
                if not is_first_run:
                    is_live = get_videos(video_id)
                    send_discord_notification(channel_name, video_id, title, is_live)
                
                # 最後に確認した動画IDを更新
                last_video_ids[channel_id] = video_id

            # 各チャンネルを確認した後に待機
            time.sleep(1)

        except Exception as e:
            print(get_time(), f"{channel_name}のステータス取得中にエラーが発生しました:", e)
            time.sleep(60)

    # 最初の実行フラグを更新
    if is_first_run:
        is_first_run = False
        print(get_time(), "初回実行: 最新の動画情報を記録しました")
    
    # 一定時間待機してから再度チェック (60秒間隔)
    time.sleep(70)

