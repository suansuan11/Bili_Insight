import asyncio
from bilibili_api import video, hot

async def check_video_status():
    bvid = "BV1bFk7BvEYH" 
    print(f"Checking video {bvid}...")
    
    # 1. Check individual video details
    try:
        v = video.Video(bvid=bvid)
        info = await v.get_info()
        stat = info['stat']
        print(f"Direct Info Reply Count: {stat.get('reply')}")
    except Exception as e:
        print(f"Direct info fetch failed: {e}")

    # 2. Check if it exists in current hot list
    print("\nChecking presence in current Hot List...")
    try:
        # Fetch 5 pages to be safe
        found = False
        for page in range(1, 6):
            hot_list = await hot.get_hot_videos(pn=page, ps=20)
            if hot_list and 'list' in hot_list:
                for item in hot_list['list']:
                    if item['bvid'] == bvid:
                        print(f"FOUND in Page {page}!")
                        print(f"Hot List Item Reply Count: {item['stat'].get('reply')}")
                        found = True
                        break
            if found: break
        
    except Exception as e:
        print(f"Hot list check failed: {e}")

    # 3. Test Service Extraction logic
    print("\nChecking Service Extraction...")
    from app.services.bilibili_service import BilibiliService
    service = BilibiliService()
    
    try:
        # Test Comments
        comments = await service.get_comments(bvid, max_count=20)
        if comments:
            print(f"First Comment Like: {comments[0].get('like')} (Type: {type(comments[0].get('like'))})")
        else:
            print("No comments fetchable via Service")

        # Test Danmaku
        danmakus = await service.get_danmakus(bvid)
        if danmakus:
            print(f"First Danmaku Time: {danmakus[0].get('dm_time')} (Type: {type(danmakus[0].get('dm_time'))})")
        else:
            print("No danmakus fetchable via Service")
    except Exception as e:
        print(f"Service test failed: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_video_status())
