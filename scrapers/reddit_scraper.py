"""
Reddit Data Scraper for Sarcasm Detection
Scrapes comments and posts from Reddit using PRAW (Python Reddit API Wrapper)
"""
import praw
import json
from datetime import datetime
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedditScraper:
    """
    Scrape Reddit posts and comments for sarcasm detection training/testing
    """
    
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        """
        Initialize Reddit scraper
        
        To get credentials:
        1. Go to https://www.reddit.com/prefs/apps
        2. Click "Create App" or "Create Another App"
        3. Select "script" type
        4. Get client_id and client_secret
        """
        self.client_id = client_id or "YOUR_CLIENT_ID"
        self.client_secret = client_secret or "YOUR_CLIENT_SECRET"
        self.user_agent = user_agent or "SarcasmDetector/1.0"
        
        self.reddit = None
        self.output_dir = Path("scraped_data/reddit")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Connect to Reddit API"""
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            logger.info("? Connected to Reddit API")
            return True
        except Exception as e:
            logger.error(f"? Failed to connect to Reddit: {e}")
            return False
    
    def scrape_subreddit_posts(self, subreddit_name, limit=100, time_filter='day'):
        """
        Scrape posts from a subreddit
        
        Args:
            subreddit_name: Name of subreddit (e.g., 'sarcasm', 'funny')
            limit: Number of posts to scrape
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        """
        if not self.reddit:
            logger.error("Not connected to Reddit. Call connect() first.")
            return []
        
        try:
            logger.info(f"Scraping r/{subreddit_name}...")
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for post in subreddit.hot(limit=limit):
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'text': post.selftext,
                    'author': str(post.author),
                    'score': post.score,
                    'url': post.url,
                    'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                    'num_comments': post.num_comments,
                    'subreddit': subreddit_name,
                    'type': 'post'
                }
                posts.append(post_data)
            
            logger.info(f"? Scraped {len(posts)} posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"? Error scraping r/{subreddit_name}: {e}")
            return []
    
    def scrape_post_comments(self, post_id, limit=100):
        """
        Scrape comments from a specific post
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to scrape
        """
        if not self.reddit:
            logger.error("Not connected to Reddit. Call connect() first.")
            return []
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "load more" placeholders
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                if hasattr(comment, 'body'):
                    comment_data = {
                        'id': comment.id,
                        'text': comment.body,
                        'author': str(comment.author),
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'post_id': post_id,
                        'type': 'comment'
                    }
                    comments.append(comment_data)
            
            logger.info(f"? Scraped {len(comments)} comments from post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"? Error scraping comments for {post_id}: {e}")
            return []
    
    def scrape_subreddit_with_comments(self, subreddit_name, num_posts=50, comments_per_post=50):
        """
        Scrape posts and their comments from a subreddit
        """
        posts = self.scrape_subreddit_posts(subreddit_name, limit=num_posts)
        
        all_data = []
        for post in posts:
            all_data.append(post)
            
            # Get comments for this post
            comments = self.scrape_post_comments(post['id'], limit=comments_per_post)
            all_data.extend(comments)
            
            time.sleep(1)  # Rate limiting
        
        return all_data
    
    def save_data(self, data, filename=None):
        """Save scraped data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_data_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"? Saved {len(data)} items to {filepath}")
        return filepath
    
    def save_for_training(self, data, output_file=None):
        """
        Save data in format suitable for training
        CSV format: text, label (manually label later)
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"reddit_training_{timestamp}.csv"
        
        filepath = self.output_dir / output_file
        
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['text', 'source', 'score', 'created_date'])
            
            for item in data:
                text = item.get('title', '') + ' ' + item.get('text', '')
                text = text.strip()
                if text:
                    writer.writerow([
                        text,
                        f"reddit_{item['type']}",
                        item.get('score', 0),
                        item.get('created_utc', '')
                    ])
        
        logger.info(f"? Saved training data to {filepath}")
        return filepath


def main():
    """Example usage"""
    print("="*60)
    print("REDDIT DATA SCRAPER")
    print("="*60)
    print()
    
    # Initialize scraper
    scraper = RedditScraper(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        user_agent="SarcasmDetector/1.0"
    )
    
    print("To use this scraper:")
    print("1. Get Reddit API credentials from: https://www.reddit.com/prefs/apps")
    print("2. Update client_id and client_secret in the code")
    print("3. Run this script")
    print()
    
    # Example subreddits for sarcasm data
    subreddits = [
        'sarcasm',           # Dedicated sarcasm subreddit
        'AskReddit',         # Popular, lots of comments
        'tifu',              # Often contains sarcastic comments
        'AmItheAsshole',     # Many sarcastic responses
    ]
    
    print("Suggested subreddits for sarcasm data:")
    for sub in subreddits:
        print(f"  - r/{sub}")
    print()
    
    # Connect to Reddit (will fail without credentials)
    if scraper.connect():
        print("? Connected to Reddit!")
        print()
        
        # Example: Scrape r/sarcasm
        print("Scraping r/sarcasm...")
        data = scraper.scrape_subreddit_with_comments('sarcasm', num_posts=10, comments_per_post=20)
        
        # Save data
        json_file = scraper.save_data(data)
        csv_file = scraper.save_for_training(data)
        
        print()
        print("? Scraping complete!")
        print(f"Scraped {len(data)} items")
        print(f"JSON file: {json_file}")
        print(f"CSV file: {csv_file}")
    else:
        print("? Could not connect to Reddit")
        print()
        print("SETUP INSTRUCTIONS:")
        print("="*60)
        print("1. Go to: https://www.reddit.com/prefs/apps")
        print("2. Click 'Create App' or 'Create Another App'")
        print("3. Fill in:")
        print("   - name: Sarcasm Detector")
        print("   - type: script")
        print("   - redirect uri: http://localhost:8000")
        print("4. Copy the client_id (under the app name)")
        print("5. Copy the client_secret")
        print("6. Update this script with your credentials")
        print()
        print("Then install PRAW:")
        print("  pip install praw")


if __name__ == "__main__":
    main()
