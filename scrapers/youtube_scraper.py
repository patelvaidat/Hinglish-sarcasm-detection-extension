"""
YouTube Data Scraper for Sarcasm Detection
Scrapes comments from YouTube videos using YouTube Data API v3
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class YouTubeScraper:
    """
    Scrape YouTube comments for sarcasm detection training/testing
    """
    
    def __init__(self, api_key=None):
        """
        Initialize YouTube scraper
        
        To get API key:
        1. Go to https://console.cloud.google.com/
        2. Create a new project
        3. Enable YouTube Data API v3
        4. Create credentials (API key)
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.youtube = None
        self.output_dir = Path("scraped_data/youtube")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Connect to YouTube API"""
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("? Connected to YouTube API")
            return True
        except Exception as e:
            logger.error(f"? Failed to connect to YouTube: {e}")
            return False
    
    def get_video_id_from_url(self, url):
        """Extract video ID from YouTube URL"""
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        elif 'watch?v=' in url:
            return url.split('watch?v=')[1].split('&')[0]
        else:
            return url  # Assume it's already a video ID
    
    def scrape_video_comments(self, video_url, max_results=100):
        """
        Scrape comments from a YouTube video
        
        Args:
            video_url: YouTube video URL or video ID
            max_results: Maximum number of comments to retrieve
        """
        if not self.youtube:
            logger.error("Not connected to YouTube. Call connect() first.")
            return []
        
        video_id = self.get_video_id_from_url(video_url)
        
        try:
            logger.info(f"Scraping comments from video: {video_id}")
            
            comments = []
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                textFormat='plainText',
                order='relevance'
            )
            
            while request and len(comments) < max_results:
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    
                    comment_data = {
                        'id': item['id'],
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'like_count': comment['likeCount'],
                        'published_at': comment['publishedAt'],
                        'video_id': video_id,
                        'reply_count': item['snippet']['totalReplyCount'],
                        'type': 'comment'
                    }
                    comments.append(comment_data)
                
                # Get next page
                if 'nextPageToken' in response and len(comments) < max_results:
                    request = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=min(max_results - len(comments), 100),
                        pageToken=response['nextPageToken'],
                        textFormat='plainText',
                        order='relevance'
                    )
                else:
                    request = None
            
            logger.info(f"? Scraped {len(comments)} comments from video {video_id}")
            return comments
            
        except Exception as e:
            logger.error(f"? Error scraping video {video_id}: {e}")
            return []
    
    def scrape_comment_replies(self, comment_id, max_results=50):
        """
        Scrape replies to a specific comment
        
        Args:
            comment_id: YouTube comment ID
            max_results: Maximum number of replies to retrieve
        """
        if not self.youtube:
            logger.error("Not connected to YouTube. Call connect() first.")
            return []
        
        try:
            request = self.youtube.comments().list(
                part='snippet',
                parentId=comment_id,
                maxResults=max_results,
                textFormat='plainText'
            )
            
            response = request.execute()
            replies = []
            
            for item in response['items']:
                reply = item['snippet']
                
                reply_data = {
                    'id': item['id'],
                    'text': reply['textDisplay'],
                    'author': reply['authorDisplayName'],
                    'like_count': reply['likeCount'],
                    'published_at': reply['publishedAt'],
                    'parent_id': comment_id,
                    'type': 'reply'
                }
                replies.append(reply_data)
            
            return replies
            
        except Exception as e:
            logger.error(f"? Error scraping replies for {comment_id}: {e}")
            return []
    
    def scrape_video_with_replies(self, video_url, max_comments=100, max_replies_per_comment=10):
        """
        Scrape video comments and their replies
        """
        comments = self.scrape_video_comments(video_url, max_results=max_comments)
        
        all_data = []
        for comment in comments:
            all_data.append(comment)
            
            # Get replies if the comment has any
            if comment['reply_count'] > 0:
                replies = self.scrape_comment_replies(comment['id'], max_results=max_replies_per_comment)
                all_data.extend(replies)
        
        return all_data
    
    def scrape_multiple_videos(self, video_urls, comments_per_video=100):
        """
        Scrape comments from multiple videos
        
        Args:
            video_urls: List of YouTube video URLs
            comments_per_video: Max comments to scrape per video
        """
        all_data = []
        
        for video_url in video_urls:
            logger.info(f"Processing: {video_url}")
            data = self.scrape_video_comments(video_url, max_results=comments_per_video)
            all_data.extend(data)
        
        return all_data
    
    def search_videos_by_keyword(self, keyword, max_results=10):
        """
        Search for videos by keyword
        
        Args:
            keyword: Search query
            max_results: Number of video results to return
        """
        if not self.youtube:
            logger.error("Not connected to YouTube. Call connect() first.")
            return []
        
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=keyword,
                type='video',
                maxResults=max_results,
                order='relevance'
            )
            
            response = request.execute()
            videos = []
            
            for item in response['items']:
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt']
                }
                videos.append(video_data)
            
            logger.info(f"? Found {len(videos)} videos for '{keyword}'")
            return videos
            
        except Exception as e:
            logger.error(f"? Error searching for videos: {e}")
            return []
    
    def save_data(self, data, filename=None):
        """Save scraped data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"youtube_data_{timestamp}.json"
        
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
            output_file = f"youtube_training_{timestamp}.csv"
        
        filepath = self.output_dir / output_file
        
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['text', 'source', 'like_count', 'published_date'])
            
            for item in data:
                text = item.get('text', '').strip()
                if text:
                    writer.writerow([
                        text,
                        f"youtube_{item['type']}",
                        item.get('like_count', 0),
                        item.get('published_at', '')
                    ])
        
        logger.info(f"? Saved training data to {filepath}")
        return filepath


def main():
    """Example usage"""
    print("="*60)
    print("YOUTUBE DATA SCRAPER")
    print("="*60)
    print()
    
    # Initialize scraper from the environment when available.
    scraper = YouTubeScraper()
    
    print("To use this scraper:")
    print("1. Get YouTube API key from: https://console.cloud.google.com/")
    print("2. Enable YouTube Data API v3")
    print("3. Set YOUTUBE_API_KEY in your environment")
    print("4. Run this script")
    print()
    
    # Example video URLs (comedy/sarcasm channels)
    example_videos = [
        "https://www.youtube.com/shorts/jSXUsFoUY-w",  # Example
    ]
    
    print("Suggested video types for sarcasm data:")
    print("  - Comedy sketches")
    print("  - Roast videos")
    print("  - Satire news")
    print("  - Comedy panel shows")
    print("  - Stand-up comedy")
    print()
    
    # Connect to YouTube (will fail without API key)
    if scraper.connect():
        print("? Connected to YouTube!")
        print()
        
        # Example: Search for sarcasm-related videos
        print("Searching for videos about 'sarcasm comedy'...")
        videos = scraper.search_videos_by_keyword('sarcasm comedy', max_results=5)
        
        if videos:
            print(f"Found {len(videos)} videos:")
            for v in videos:
                print(f"  - {v['title']} by {v['channel']}")
            print()
            
            # Scrape comments from first video
            if videos:
                video_id = videos[0]['video_id']
                print(f"Scraping comments from: {videos[0]['title']}")
                comments = scraper.scrape_video_comments(video_id, max_results=50)
                
                # Save data
                json_file = scraper.save_data(comments)
                csv_file = scraper.save_for_training(comments)
                
                print()
                print("? Scraping complete!")
                print(f"Scraped {len(comments)} comments")
                print(f"JSON file: {json_file}")
                print(f"CSV file: {csv_file}")
    else:
        print("? Could not connect to YouTube")
        print()
        print("SETUP INSTRUCTIONS:")
        print("="*60)
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable YouTube Data API v3:")
        print("   - APIs & Services > Library")
        print("   - Search for 'YouTube Data API v3'")
        print("   - Click Enable")
        print("4. Create API key:")
        print("   - APIs & Services > Credentials")
        print("   - Create Credentials > API Key")
        print("5. Copy the API key")
        print("6. Export it as YOUTUBE_API_KEY before running")
        print()
        print("Then install required library:")
        print("  pip install google-api-python-client")


if __name__ == "__main__":
    main()
