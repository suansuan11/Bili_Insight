from app.database.repository import DatabaseRepository
from datetime import datetime

repo = DatabaseRepository()

test_video = {
    'bvid': 'BV1xxTest',
    'aid': 123456789,
    'title': 'Test Video',
    'author': 'Test Author',
    'author_mid': 11111,
    'publish_date': '2025-01-01 12:00:00',
    'duration': 100,
    'view_count': 1000,
    'like_count': 100,
    'coin_count': 10,
    'favorite_count': 50,
    'share_count': 20,
    'danmaku_count': 5,
    'description': 'Test Desc',
    'cover_url': 'http://example.com/cover.jpg'
}

try:
    print("Testing insert...")
    repo.insert_or_update_popular_video(test_video)
    print("Insert success!")
except Exception as e:
    print(f"Insert failed: {e}")
