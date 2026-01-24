import asyncio
from bilibili_api import hot

async def main():
    print("Testing get_hot_videos...")
    try:
        # Try to get 1 page with 20 items
        result = await hot.get_hot_videos(pn=1, ps=20)
        videos = result.get('list', [])
        print(f"Result keys: {result.keys()}")
        print(f"Number of videos in list: {len(videos)}")
        if len(videos) > 0:
            print(f"First video title: {videos[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
