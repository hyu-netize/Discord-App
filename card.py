import time
import random
import requests
from requests_html import HTMLSession
from config import Card
from util import get_time


def send_discord_notification(pokemon_name, url, full_img_url):
    """Discord Webhookに配信開始を通知する関数"""
    # ゲームのサムネイル画像
    timestamp = int(time.time()) 
    thumbnail_url = "https://www.pokemon-card.com/assets/images/og.png"
    thumbnail_url += f"?v={timestamp}"
    # タイトル説明
    title = f"カード詳細（{pokemon_name}） | ポケカ公式"
    content = {
        "content": url,
        "embeds": [
            {
                "author": {
                    "name": "ポケカ公式"
                },
                "title": title,
                "url": url,
                "image": {
                    "url": full_img_url
                },
                "thumbnail": {
                    "url": thumbnail_url  # ゲームのサムネイル画像
                }
            }
        ]
    }
    # メッセージを送信
    response = requests.post(Card.DISCORD_WEBHOOK_URL, json=content)
    if response.status_code == 204:
        print(get_time(), f"{pokemon_name} {url}を送信しました")
    else:
        print(get_time(), f"{pokemon_name} {url}の送信に失敗しました:", response.status_code)


def find_dynamic_id(url, card_show_id):
    """ requests-htmlを使用して指定のURLを開き、IDを検索する関数 """
    is_energy = False
    session = HTMLSession()
    try:
        # URLにアクセス
        response = session.get(url)
        # JavaScriptをレンダリング
        response.html.render(timeout=300)
        # 要素が存在するか確認
        element = response.html.find(f'#{card_show_id}', first=True)
        if element:
            # ランダムなカードを選択（例として）
            card = response.html.find(f'a[id="{card_show_id}"]', first=True)
            if card:
                # 画像URLの取得と加工
                img_element = card.find('img', first=True)
                if img_element:
                    img_url = img_element.attrs.get('data-src')
                    pokemon_name = img_element.attrs.get('alt')
                    if "エネルギー" in pokemon_name:
                        is_energy = True
                        print(get_time(), f"Pokemon name contains Energy.: {pokemon_name}")
                    elif img_url and pokemon_name:
                        card_id = img_url.split('/')[-1].split('_')[0]
                        full_img_url = f"https://www.pokemon-card.com{img_url}"
                        detail_url = f"https://www.pokemon-card.com/card-search/details.php/card/{card_id}/regu/all"
                        send_discord_notification(pokemon_name, detail_url, full_img_url)
                    else:
                        print(get_time(), "Image URL or Pokemon name not found.")
                else:
                    print(get_time(), "Image element not found.")
            else:
                print(get_time(), f"Card with id '{card_show_id}' not found.")
        else:
            print(get_time(), f"Element with id '{card_show_id}' not found.")
    except Exception as e:
        print(get_time(), f"An error occurred: {e}")
    finally:
        session.close()
        return is_energy

# ページ範囲を指定
start_page = 0
end_page = Card.END_PAGE

while True:
    random_page = random.randint(start_page, end_page)
    url = f"https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=all&pg=&illust=&sm_and_keyword=true&page={random_page}"

    # 1ページの要素数を指定（固定）
    random_id = random.randint(0, 38)
    card_show_id = f'card-show-id{random_id}'

    is_energy = find_dynamic_id(url, card_show_id)
    if not is_energy:
        exit(0)
    time.sleep(1)
