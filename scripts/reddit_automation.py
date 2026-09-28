# reddit_automation.py
import os
import praw

_REQUIRED = ('REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD')
if any(not os.environ.get(name) for name in _REQUIRED):
    raise SystemExit('Reddit credentials are required')

def post_to_reddit(subreddit_name: str, title: str, content: str) -> str:
    """
    Belirtilen bir subreddit üzerinde otomatik olarak metin (text) gönderisi paylaşır.
    Args:
        subreddit_name (str): Paylaşım yapılacak topluluğun adı (örn: 'Turkey', 'test').
        title (str): Gönderinin başlığı.
        content (str): Gönderinin metin içeriği.
    """
    # Reddit API Kimlik Bilgileri
    reddit = praw.Reddit(
        client_id=os.environ['REDDIT_CLIENT_ID'],
        client_secret=os.environ['REDDIT_CLIENT_SECRET'],
        user_agent="HermesAutomationBot v1.0 (by u/REDDIT_KULLANICI_ADINIZ)",
        username=os.environ['REDDIT_USERNAME'],
        password=os.environ['REDDIT_PASSWORD']
    )
    
    try:
        # İlgili subreddit'i seç ve gönderiyi paylaş
        target_subreddit = reddit.subreddit(subreddit_name)
        submission = target_subreddit.submit(title, selftext=content)
        
        return f"Başarılı! Gönderi paylaşıldı. URL: https://www.reddit.com{submission.permalink}"
        
    except Exception as e:
        return f"Gönderi paylaşılırken bir hata oluştu: {str(e)}"
