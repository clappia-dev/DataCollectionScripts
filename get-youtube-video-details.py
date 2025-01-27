"""
The script will get the details of all the videos from a youtube channel and save it to a csv file

To install the required dependencies, run the following command:
pip install -r requirements.txt

To set the environment variables, run the following command:
export YOUTUBE_API_KEY=your_api_key_here
export YOUTUBE_CHANNEL_ID=your_channel_id_here

To run the script, execute the following command:
python get-youtube-video-details.py
"""
import os
from googleapiclient.discovery import build
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_channel_videos(api_key, channel_id):
    # Create YouTube API client
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # First get upload playlist id
    channel_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()
    
    playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    videos = []
    next_page_token = None
    
    while True:
        print(f"Getting videos from playlist {playlist_id} with page token {next_page_token}")
        # Get videos from playlist
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        # Get video IDs
        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
        
        # Get video statistics
        video_response = youtube.videos().list(
            part='statistics,snippet',
            id=','.join(video_ids)
        ).execute()
        
        # Process each video
        for video in video_response['items']:
            video_data = {
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'published_at': datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'video_id': video['id'],
                'video_url': f"https://youtube.com/watch?v={video['id']}"
            }
            print(f"Video data: {video_data}")
            videos.append(video_data)
        
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

def main():
    # Your API key and channel ID
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
    
    if not API_KEY or not CHANNEL_ID:
        raise ValueError("Missing required environment variables. Please set YOUTUBE_API_KEY and YOUTUBE_CHANNEL_ID")
    
    try:
        # Get videos
        videos = get_channel_videos(API_KEY, CHANNEL_ID)
        
        # Convert to DataFrame
        df = pd.DataFrame(videos)
        
        # Sort by published date
        df = df.sort_values('published_at', ascending=False)
        
        # Save to CSV
        df.to_csv('youtube_videos.csv', index=False)
        print(f"Successfully exported {len(videos)} videos to youtube_videos.csv")
        
        # Display first few rows
        print("\nFirst few videos (rest of the data is in the csv file youtube_videos.csv):")
        print(df.head())
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()