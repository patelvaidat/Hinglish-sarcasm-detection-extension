"""
Quick test script for YouTube scraper
Run this after setting up API credentials
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

print("="*60)
print("YOUTUBE DATA SCRAPER - QUICK TEST")
print("="*60)
print()

# Check if dependencies are installed
try:
    from googleapiclient.discovery import build
    print("✓ Google API Client installed (YouTube scraper ready)")
except ImportError:
    print("✗ Google API Client not installed")
    print("    Run: pip install google-api-python-client")
    print()

print()
print("="*60)
print("CHOOSE AN OPTION:")
print("="*60)
print("1. Test YouTube Scraper")
print("2. Exit")
print()

choice = input("Enter choice (1-2): ").strip()

if choice == "1":
    print()
    print("="*60)
    print("YOUTUBE SCRAPER TEST")
    print("="*60)
    print()
    
    from youtube_scraper import YouTubeScraper
    
    # Prefer the environment variable, fall back to a prompt for ad hoc testing.
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("Enter your YouTube API key:")
        print("(Get it from: https://console.cloud.google.com/)")
        print()
        api_key = input("API Key: ").strip()
    
    if api_key:
        scraper = YouTubeScraper(api_key=api_key)
        
        if scraper.connect():
            print()
            print("✓ Connected to YouTube!")
            print()
            
            print("1. Search for videos")
            print("2. Scrape specific video")
            
            sub_choice = input("Enter choice (1-2): ").strip()
            
            if sub_choice == "1":
                keyword = input("Search keyword (default: sarcasm comedy): ").strip() or "sarcasm comedy"
                
                print()
                print(f"Searching for '{keyword}'...")
                
                videos = scraper.search_videos_by_keyword(keyword, max_results=5)
                
                if videos:
                    print()
                    print(f"Found {len(videos)} videos:")
                    for i, v in enumerate(videos, 1):
                        print(f"{i}. {v['title']}")
                        print(f"   By: {v['channel']}")
                        print(f"   ID: {v['video_id']}")
                    
                    print()
                    scrape = input("Scrape comments from video #1? (y/n): ").strip().lower()
                    
                    if scrape == 'y':
                        video_id = videos[0]['video_id']
                        print()
                        print(f"Scraping comments from: {videos[0]['title']}")
                        
                        comments = scraper.scrape_video_comments(video_id, max_results=50)
                        
                        if comments:
                            json_file = scraper.save_data(comments)
                            csv_file = scraper.save_for_training(comments)
                            
                            print()
                            print("✓ SUCCESS!")
                            print(f"Scraped {len(comments)} comments")
                            print(f"JSON: {json_file}")
                            print(f"CSV: {csv_file}")
                
            elif sub_choice == "2":
                video_url = input("Enter YouTube video URL: ").strip()
                max_comments = input("Max comments (default: 50): ").strip() or "50"
                
                print()
                print("Scraping comments...")
                
                comments = scraper.scrape_video_comments(video_url, max_results=int(max_comments))
                
                if comments:
                    json_file = scraper.save_data(comments)
                    csv_file = scraper.save_for_training(comments)
                    
                    print()
                    print("✓ SUCCESS!")
                    print(f"Scraped {len(comments)} comments")
                    print(f"JSON: {json_file}")
                    print(f"CSV: {csv_file}")
        else:
            print("✗ Failed to connect. Check your API key.")
    else:
        print("✗ API key required")

elif choice == "2":
    print("Exiting...")
    sys.exit(0)

print()
print("="*60)
print("TEST COMPLETE!")
print("="*60)
print()
print("Check the scraped_data/ directory for your files!")
print()