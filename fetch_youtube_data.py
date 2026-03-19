#!/usr/bin/env python3
"""
Fetch real YouTube data for MrBeast channels
Pulls actual video metadata, stats, and performance data
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class YouTubeDataFetcher:
    """Fetch real data from YouTube API v3"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.channels = {
            "MrBeast": "UCX6OQ3DkcsbYNE6H8uQQuVA",
            "MrBeast2": "UC4-79UOlP48-QNGgCko5p2g",
            "MrBeast Gaming": "UCIPPMRA040LQr5QPyJEbmXA"
        }
    
    def get_channel_stats(self, channel_id: str) -> Dict:
        """Get channel statistics"""
        url = f"{self.base_url}/channels"
        params = {
            "part": "statistics,snippet",
            "id": channel_id,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                item = data['items'][0]
                return {
                    "channel_name": item['snippet']['title'],
                    "subscribers": int(item['statistics']['subscriberCount']),
                    "total_views": int(item['statistics']['viewCount']),
                    "video_count": int(item['statistics']['videoCount']),
                    "description": item['snippet']['description']
                }
        except Exception as e:
            print(f"Error fetching channel stats: {e}")
        
        return {}
    
    def get_videos(self, channel_id: str, max_results: int = 50) -> List[Dict]:
        """Get recent videos from a channel"""
        videos = []
        
        try:
            # First, get uploads playlist ID
            channel_url = f"{self.base_url}/channels"
            channel_params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": self.api_key
            }
            channel_response = requests.get(channel_url, params=channel_params)
            channel_response.raise_for_status()
            
            uploads_playlist = channel_response.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            playlist_url = f"{self.base_url}/playlistItems"
            playlist_params = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist,
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }
            
            playlist_response = requests.get(playlist_url, params=playlist_params)
            playlist_response.raise_for_status()
            playlist_data = playlist_response.json()
            
            video_ids = [item['contentDetails']['videoId'] for item in playlist_data.get('items', [])]
            
            if video_ids:
                # Get video statistics
                videos_url = f"{self.base_url}/videos"
                videos_params = {
                    "part": "snippet,statistics",
                    "id": ",".join(video_ids),
                    "key": self.api_key
                }
                
                videos_response = requests.get(videos_url, params=videos_params)
                videos_response.raise_for_status()
                videos_data = videos_response.json()
                
                for item in videos_data.get('items', []):
                    video = {
                        "video_id": item['id'],
                        "title": item['snippet']['title'],
                        "description": item['snippet']['description'],
                        "published_at": item['snippet']['publishedAt'],
                        "thumbnail": item['snippet']['thumbnails']['high']['url'],
                        "views": int(item['statistics'].get('viewCount', 0)),
                        "likes": int(item['statistics'].get('likeCount', 0)),
                        "comments": int(item['statistics'].get('commentCount', 0)),
                    }
                    videos.append(video)
        
        except Exception as e:
            print(f"Error fetching videos: {e}")
        
        return videos
    
    def analyze_all_channels(self) -> Dict:
        """Analyze all MrBeast channels"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "channels": {}
        }
        
        for channel_name, channel_id in self.channels.items():
            print(f"Fetching data for {channel_name}...")
            
            stats = self.get_channel_stats(channel_id)
            videos = self.get_videos(channel_id, max_results=50)
            
            analysis["channels"][channel_name] = {
                "channel_id": channel_id,
                "stats": stats,
                "recent_videos": videos,
                "analysis": self._analyze_videos(videos)
            }
        
        return analysis
    
    @staticmethod
    def _analyze_videos(videos: List[Dict]) -> Dict:
        """Analyze video patterns"""
        if not videos:
            return {}
        
        views = [v['views'] for v in videos]
        likes = [v['likes'] for v in videos]
        comments = [v['comments'] for v in videos]
        
        return {
            "avg_views": sum(views) / len(views) if views else 0,
            "avg_likes": sum(likes) / len(likes) if likes else 0,
            "avg_comments": sum(comments) / len(comments) if comments else 0,
            "top_video": max(videos, key=lambda x: x['views']) if videos else None,
            "title_patterns": analyze_titles([v['title'] for v in videos]),
            "upload_frequency": calculate_frequency([v['published_at'] for v in videos])
        }
    
    def save_results(self, data: Dict, filename: str = "youtube_data.json"):
        """Save results to file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Data saved to {filename}")

def analyze_titles(titles: List[str]) -> Dict:
    """Analyze title patterns"""
    patterns = {
        "has_dollar": sum(1 for t in titles if '$' in t),
        "has_urgency": sum(1 for t in titles if any(word in t.upper() for word in ["FINAL", "LAST", "ONLY"])),
        "has_question": sum(1 for t in titles if '?' in t),
        "avg_length": sum(len(t) for t in titles) / len(titles) if titles else 0
    }
    return patterns

def calculate_frequency(dates: List[str]) -> str:
    """Calculate upload frequency"""
    if len(dates) < 2:
        return "Unknown"
    
    dates_sorted = sorted(dates, reverse=True)
    diffs = []
    for i in range(len(dates_sorted) - 1):
        d1 = datetime.fromisoformat(dates_sorted[i].replace('Z', '+00:00'))
        d2 = datetime.fromisoformat(dates_sorted[i+1].replace('Z', '+00:00'))
        diffs.append((d1 - d2).days)
    
    avg_days = sum(diffs) / len(diffs) if diffs else 0
    
    if avg_days < 2:
        return "Daily"
    elif avg_days < 7:
        return "Weekly"
    elif avg_days < 14:
        return "Biweekly"
    else:
        return "Monthly"

def main():
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY environment variable not set")
        print("Set it with: export YOUTUBE_API_KEY='your_api_key'")
        return
    
    fetcher = YouTubeDataFetcher(api_key)
    
    print("Fetching YouTube data for MrBeast channels...")
    print("=" * 50)
    
    analysis = fetcher.analyze_all_channels()
    
    # Save raw data
    fetcher.save_results(analysis, "data/youtube_data.json")
    
    # Print summary
    print("\n" + "=" * 50)
    print("ANALYSIS SUMMARY")
    print("=" * 50)
    
    for channel, data in analysis['channels'].items():
        stats = data['stats']
        analysis_data = data['analysis']
        
        print(f"\n📺 {channel}")
        print(f"   Subscribers: {stats.get('subscribers', 'N/A'):,}")
        print(f"   Total Views: {stats.get('total_views', 'N/A'):,}")
        print(f"   Videos: {stats.get('video_count', 'N/A')}")
        print(f"   Upload Frequency: {analysis_data.get('upload_frequency', 'N/A')}")
        print(f"   Avg Views/Video: {analysis_data.get('avg_views', 0):,.0f}")
        print(f"   Avg Likes: {analysis_data.get('avg_likes', 0):,.0f}")
        
        titles = analysis_data.get('title_patterns', {})
        print(f"   Titles with $: {titles.get('has_dollar', 0)}/{len(data['recent_videos'])}")
        print(f"   Titles with urgency: {titles.get('has_urgency', 0)}/{len(data['recent_videos'])}")

if __name__ == "__main__":
    main()
