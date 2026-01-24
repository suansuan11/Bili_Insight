# danmaku_scraper.py (命令行参数版)

import asyncio
import json
import time
from pathlib import Path
import argparse  # 导入argparse库

from bilibili_api import video, Credential

# 【修改】不再从代码顶部读取配置，而是通过main函数接收参数
async def run_scraper(bvid: str, sessdata: str):
    """
    爬取B站视频弹幕

    Args:
        bvid: 视频BVID
        sessdata: B站登录凭证

    Returns:
        list: 弹幕数据列表 [{"content": "弹幕内容", "dm_time": 时间}, ...]
    """
    start_time = time.time()
    try:
        # ===== 文件与路径设置 =====
        data_folder = Path("data")
        data_folder.mkdir(parents=True, exist_ok=True)
        output_filename = f"{bvid}_danmaku.json"
        full_filepath = data_folder / output_filename
        print(f"初始化完成，弹幕将被保存到: {full_filepath}")

        # ===== 数据获取 =====
        credential = Credential(sessdata=sessdata)
        v = video.Video(bvid=bvid, credential=credential)
        info = await v.get_info()
        print(f"成功连接到视频：《{info['title']}》")
        print("正在获取全部弹幕...")
        danmakus_list = await v.get_danmakus(cid=info['cid'])

        # 转换弹幕数据格式
        danmaku_data_for_json = []
        for dm in danmakus_list:
            if dm.text:
                danmaku_data_for_json.append({
                    "content": dm.text,  # 改用 content 字段
                    "dm_time": dm.dm_time
                })

        # 保存到文件
        with open(full_filepath, 'w', encoding='utf-8') as f:
            json.dump(danmaku_data_for_json, f, ensure_ascii=False, indent=4)

        print(f"\n【任务完成】全部 {len(danmaku_data_for_json)} 条有效弹幕已成功保存到文件: {full_filepath}")

        duration = time.time() - start_time
        print(f"\n总耗时: {duration:.2f} 秒")

        # 返回弹幕数据
        return danmaku_data_for_json

    except Exception as e:
        print(f"\n【程序执行出错】: {e}", flush=True)
        return []  # 出错时返回空列表

if __name__ == '__main__':
    # ===== argparse 设置 =====
    parser = argparse.ArgumentParser(description='Bilibili Danmaku Scraper')
    parser.add_argument('--bvid', type=str, required=True, help='视频的 BVID')
    parser.add_argument('--sessdata', type=str, required=True, help='用于认证的 SESSDATA')
    args = parser.parse_args()
    
    # ===== 运行主程序 =====
    # asyncio.run() 在Python 3.7+ 中是标准用法
    asyncio.run(run_scraper(bvid=args.bvid, sessdata=args.sessdata))

# python danmaku_scraper.py --bvid BV1iwN4zeEUo --sessdata fe6fdbe0%2C1765951800%2C79ea5%2A62CjCjw1x9x8_4UheNvG1I6mysRdAn7M_btFYRCy0gx9qrgMpjgnHOBVFx-uhNHXcaxeESVi1GR2F2TVpRTnlZaWRoMTUyTjlEQ05WYjU4ejAtT2J0RlZlQTZhVk5QNEdLV1hkWC1RLU45SmhyRnZCYWs3aDVLN3pQVTJLNEI3aGhfd2lYZUtzWWt3IIEC   