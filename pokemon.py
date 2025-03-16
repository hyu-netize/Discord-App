import random
import requests
from config import Pokemon
from util import get_time


def send_discord_notification(url):
    """Discord Webhookに配信開始を通知する関数"""
    content = {
        "content": f"{url}"
    }

    # メッセージを送信
    response = requests.post(Pokemon.DISCORD_WEBHOOK_URL, json=content)
    if response.status_code == 204:
        print(get_time(), f"{url}を送信しました")
    else:
        print(get_time(), f"{url}の送信に失敗しました:", response.status_code)


# ランダムにIDを選択
pokemon_ids = list(range(1, Pokemon.MAX_POKEMON_ID + 1))
random_pokemon_id = random.choice(pokemon_ids)

# 選択したIDの詳細ページURL
url = f'https://zukan.pokemon.co.jp/detail/{str(random_pokemon_id).zfill(4)}'

send_discord_notification(url)