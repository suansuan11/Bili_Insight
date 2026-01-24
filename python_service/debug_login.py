import asyncio
import os
from app.services.credential_manager import get_credential_manager

async def test_save_credential():
    print("Testing credential saving...")
    cm = get_credential_manager()
    
    # Simulate a successful login with fake data
    fake_sessdata = "fake_sessdata_for_test"
    fake_bili_jct = "fake_bili_jct"
    fake_buvid3 = "fake_buvid3"
    
    try:
        success = cm.update_credential(fake_sessdata, fake_bili_jct, fake_buvid3, save_to_file=True)
        if success:
            print("Credential update reported success.")
        else:
            print("Credential update reported failure.")
            
        # Verify file content
        import json
        from pathlib import Path
        cred_file = Path("credentials.json")
        if cred_file.exists():
            with open(cred_file, 'r') as f:
                data = json.load(f)
                print(f"File content SESSDATA: {data.get('sessdata')}")
        else:
            print("credentials.json file not found!")
            
    except Exception as e:
        print(f"Error during save test: {e}")

if __name__ == '__main__':
    # Ensure run from python_service directory context for relative paths
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_save_credential())
