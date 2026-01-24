# comment_scraper.py

import json
import requests
import hashlib
import time
import argparse
import os
from urllib.parse import quote, urlencode
from functools import reduce
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Robust Session & WBI Logic ---

def get_robust_session(sessdata=None):
    """创建一个带有重试机制的 requests Session，并初始化 B站 Cookies"""
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=1,  # 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # 基础 Headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com"
    })
    
    # 如果提供了 SESSDATA，直接设置 Cookie
    if sessdata:
        session.cookies.set('SESSDATA', sessdata, domain='.bilibili.com')
    
    # 访问主页以获取/刷新基础 Cookie (buvid3 等)，除非已经有完整的 Cookie
    try:
        session.get("https://www.bilibili.com/", timeout=5)
    except Exception as e:
        print(f"初始化 Cookies 失败: {e}")
        
    return session

# ... (mixinKeyEncTab, getMixinKey, encWbi, getWbiKeys, get_aid_from_bvid functions remain unchanged) ...

def get_aid_from_bvid(bvid, session=None):
    if session is None:
        session = get_robust_session()
    try:
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        return data['data']['aid'] if data['code'] == 0 else None
    except Exception as e:
        print(f"获取 AID 失败: {e}")
        return None

def get_comments_page(offset, oid, session, img_key, sub_key):
    url = 'https://api.bilibili.com/x/v2/reply/wbi/main'
    
    # 动态更新 Referer 为具体视频页面，这对于防盗链检查很重要
    session.headers.update({"Referer": f"https://www.bilibili.com/video/av{oid}"})

    # 构造原始参数
    params = {
        'oid': oid,
        'type': 1,
        'mode': 2, # 热门排序(3) 或 时间排序(2)? 通常默认2(时间)或3(热度). 这里保持原代码mode=2
        'pagination_str': json.dumps({"offset": offset}, separators=(',', ':')) if offset != '""' and offset != "" else '{"offset":""}',
        'plat': 1,
        'web_location': 1315875
    }
    
    # 进行 WBI 签名
    signed_params, w_rid = encWbi(params, img_key, sub_key)
    signed_params['w_rid'] = w_rid

    try:
        response = session.get(url, params=signed_params)
        response.raise_for_status()
        json_data = response.json()
        
        if json_data['code'] != 0:
            print(f"API 返回错误代码: {json_data['code']}, 信息: {json_data.get('message')}")
            # print(f"DEBUG: w_rid={w_rid}, params={signed_params}")
            return [], None

        page_comments = []
        replies = json_data.get('data', {}).get('replies', [])
        if replies:
            for index in replies:
                dit = {
                    '昵称': index['member']['uname'],
                    '性别': index['member']['sex'],
                    '评论': index['content']['message'],
                    '点赞': index.get('like', 0),
                    '回复ID': index.get('rpid')
                }
                page_comments.append(dit)

        next_offset_obj = json_data.get('data', {}).get('cursor', {}).get('pagination_reply', {}).get('next_offset')
        # next_offset 可能是字符串也可能是对象，通常这里如果是JSON字符串需要解析，如果是对象直接使用
        # 观察原代码，next_offset_obj 似乎直接是 json 对象。需要转为 json string 传给下一次
        next_offset_str = None
        if next_offset_obj:
             next_offset_str = json.dumps(next_offset_obj).replace(" ", "") # 去除空格以防万一

        return page_comments, next_offset_str
    except Exception as e:
        print(f"请求或处理评论页时出错: {e}")
        return [], None

if __name__ == '__main__':
    # 【优化】增加任务耗时统计
    start_time = time.time()

    parser = argparse.ArgumentParser(description='Bilibili Comment Scraper')
    parser.add_argument('--bvid', type=str, required=True, help='The BVID of the Bilibili video.')
    parser.add_argument('--output', type=str, help='Output JSON file name.')
    parser.add_argument('--sessdata', type=str, help='Bilibili SESSDATA cookie (optional, prevents -403 errors).')
    args = parser.parse_args()
    bvid = args.bvid
    
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    output_file = args.output if args.output else f"{bvid}_comments.json"
    output_file_path = os.path.join(output_dir, output_file)

    print(f"--- 正在为视频 {bvid} 准备评论爬取 ---")
    
    # 初始化 Session (传入 SESSDATA) 和 Keys
    session = get_robust_session(args.sessdata)
    img_key, sub_key = getWbiKeys(session)
    if not img_key or not sub_key:
        print("错误：无法获取 WBI 签名密钥，程序退出。")
        exit(1)

    aid = get_aid_from_bvid(bvid, session)

    if not aid:
        print(f"错误：无法通过 BVID '{bvid}' 获取到有效的 AID。")
    else:
        print(f"成功获取到 AID: {aid}。开始爬取评论...")
        all_comments = []
        # 初始 offset
        # B站新接口第一页传 {"offset":""} 的 json 串
        current_offset_str = "" # 内部逻辑会处理
        
        page_num = 1
        MAX_PAGES = 50 # 安全限制，防止无限爬取
        
        while page_num <= MAX_PAGES:
            print(f"正在爬取第 {page_num} 页...", end="\r")
            new_comments, next_offset = get_comments_page(current_offset_str, aid, session, img_key, sub_key)
            
            if new_comments:
                all_comments.extend(new_comments)
            
            # 如果没有下一页 offset 或者没有抓取到数据(可能是到底了)，则退出
            if not next_offset or (not new_comments and page_num > 1):
                print(f"\n已到达最后一页或无更多数据。")
                break
                
            current_offset_str = next_offset
            page_num += 1
            # 礼貌性延迟，虽然有重试机制
            time.sleep(0.8)

        print(f"\n共获取到 {len(all_comments)} 条评论，准备写入文件...")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=4)
        print(f"视频 {bvid} 的所有评论已成功爬取并保存到 {output_file_path}！")

    end_time = time.time()
    print(f"\n任务总耗时: {end_time - start_time:.2f} 秒")


#python comment_scraper.py --bvid BV1TDNEzfEQM