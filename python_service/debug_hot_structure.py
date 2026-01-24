
import asyncio
from bilibili_api import hot

async def check_hot_structure():
    print("Fetching hot videos...")
    try:
        # Get raw response to check fields
        videos = await hot.get_hot_videos()
        if videos and 'list' in videos:
            first_item = videos['list'][0]
            print("\n--- First Hot Video Raw Stat ---")
            print(first_item.get('stat'))
            print("--------------------------------")
            
            if 'reply' in first_item['stat']:
                print(f"Found 'reply' field: {first_item['stat']['reply']}")
            else:
                print("'reply' field NOT found in stat!")
                print(f"Available keys in stat: {first_item['stat'].keys()}")
        else:
            print("No video list found in response")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_hot_structure())
