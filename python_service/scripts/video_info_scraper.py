# video_info_scraper.py

import requests
import json
import argparse
import os
from datetime import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_robust_session():
    """创建一个带有重试机制的 requests Session"""
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    })
    return session

def get_video_info(video_id):
    session = get_robust_session()
    url = 'https://api.bilibili.com/x/web-interface/view'
    if str(video_id).startswith('BV'):
        params = {'bvid': video_id}
    else:
        params = {'aid': video_id}
    
    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 0:
            video_data = data['data']
            stat = video_data['stat']
            info_dict = {
                'bvid': video_data['bvid'], 'aid': video_data['aid'], 'title': video_data['title'],
                'author': video_data['owner']['name'], 'author_mid': video_data['owner']['mid'],
                'publish_date': datetime.fromtimestamp(video_data['pubdate']).strftime('%Y-%m-%d %H:%M:%S'),
                'duration': video_data['duration'], 'view_count': stat['view'], 'like_count': stat['like'],
                'coin_count': stat['coin'], 'favorite_count': stat['favorite'], 'share_count': stat['share'],
                'danmaku_count': stat['danmaku'], 'description': video_data['desc'], 'cover_url': video_data['pic']
            }
            return info_dict
    except Exception as e:
        print(f"获取视频 {video_id} 详情时出错: {e}")
    return None

if __name__ == '__main__':
    # 【优化】增加任务耗时统计
    start_time = time.time()

    import argparse
    parser = argparse.ArgumentParser(description='Bilibili Video Info Scraper (Tool Script)')
    parser.add_argument('--id', type=str, required=True, help='The BVID or AID of the video.')
    parser.add_argument('--output', type=str, help='Output JSON file name.')
    args = parser.parse_args()
    video_id = args.id
    
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    base_filename = args.output if args.output else f"{video_id}_info.json"
    output_file_path = os.path.join(output_dir, base_filename)

    print(f"--- 正在尝试获取视频 {args.id} 的信息 ---")
    video_info = get_video_info(args.id)
    
    if video_info:
        print("\n--- 信息获取成功 ---")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(video_info, f, ensure_ascii=False, indent=4)
        print(f"视频详细信息已保存到: {output_file_path}")
    else:
        print("\n--- 信息获取失败 ---")

    end_time = time.time()
    print(f"\n任务总耗时: {end_time - start_time:.2f} 秒")

#python video_info_scraper.py --id BV1XgNLzbEwe