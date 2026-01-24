# popular_videos_scraper.py

import requests
import json
import argparse
import time
from datetime import datetime
import os
# 【优化】导入并发库
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 假设 video_info_scraper.py 在同一目录下
from video_info_scraper import get_video_info

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

def scrape_popular_page_summary(page_number):
    print(f"\n--- 正在爬取热门榜第 {page_number} 页的视频列表 ---")
    url = "https://api.bilibili.com/x/web-interface/popular"
    params = {'pn': page_number, 'ps': 20}
    
    session = get_robust_session()
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 0:
            return data.get('data', {}).get('list', [])
    except Exception as e:
        print(f"请求热门榜时发生网络错误: {e}")
    return None

if __name__ == "__main__":
    # 【优化】增加任务耗时统计
    start_time = time.time()

    parser = argparse.ArgumentParser(description='Bilibili Popular Videos Detailed Info Scraper')
    parser.add_argument('--pages', type=int, default=1, help='要爬取的热门榜页数。')
    parser.add_argument('--output', type=str, help='输出的JSON文件名。')
    # 【优化】可以指定并发的线程数
    parser.add_argument('--workers', type=int, default=10, help='并发请求的线程数。')
    args = parser.parse_args()

    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime('%Y-%m-%d')
    base_filename = args.output if args.output else f"{today_str}_popular.json"
    output_file_path = os.path.join(output_dir, base_filename)
    
    all_detailed_videos = []
    bvid_list_to_scrape = []

    # 1. 首先，收集所有需要爬取的bvid
    for page in range(1, args.pages + 1):
        page_summary_list = scrape_popular_page_summary(page)
        if not page_summary_list:
            print("没有更多热门视频页，停止收集。")
            break
        for video_summary in page_summary_list:
            if video_summary.get('bvid'):
                bvid_list_to_scrape.append(video_summary.get('bvid'))
        # 翻页之间仍然可以短暂休息
        time.sleep(0.5)
    
    # 2. 【核心优化】使用线程池并发获取所有视频的详细信息
    if bvid_list_to_scrape:
        print(f"\n--- 收集完成，共 {len(bvid_list_to_scrape)} 个视频。开始使用 {args.workers} 个线程并发获取详细信息... ---")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            # 提交所有任务
            future_to_bvid = {executor.submit(get_video_info, bvid): bvid for bvid in bvid_list_to_scrape}
            
            # 当任务完成时，处理结果
            for future in as_completed(future_to_bvid):
                bvid = future_to_bvid[future]
                try:
                    detailed_info = future.result()
                    if detailed_info:
                        all_detailed_videos.append(detailed_info)
                        print(f"  [成功] {detailed_info['title']}")
                    else:
                        print(f"  [失败] 未能获取 {bvid} 的详细信息。")
                except Exception as exc:
                    print(f"  [异常] 获取 {bvid} 详情时产生异常: {exc}")

    # 3. 所有任务完成后，写入文件
    if all_detailed_videos:
        print(f"\n--- 并发爬取完毕，共获取 {len(all_detailed_videos)} 条详细视频信息 ---")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_detailed_videos, f, ensure_ascii=False, indent=4)
        print(f"任务完成！所有热门视频的详细信息已保存到文件: {output_file_path}")
    else:
        print("\n未能获取到任何视频的详细信息。")

    end_time = time.time()
    print(f"\n任务总耗时: {end_time - start_time:.2f} 秒")

#python popular_videos_scraper.py --pages 1 --workers 20