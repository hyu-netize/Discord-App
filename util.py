import datetime

def get_time():
    """現在時刻を取得する関数"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
