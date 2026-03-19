# YouTube API Setup Guide

## Getting Real Data from YouTube

This guide explains how to fetch actual MrBeast channel data using the YouTube Data API v3.

### Prerequisites

1. **Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create a new project (or use existing)
   - Enable YouTube Data API v3

2. **API Key**
   - Go to Credentials → Create Credentials → API Key
   - Copy your API key

### Configuration

Set your API key as an environment variable:

```bash
# On Mac/Linux
export YOUTUBE_API_KEY='your_api_key_here'

# On Windows (PowerShell)
$env:YOUTUBE_API_KEY='your_api_key_here'
```

### Running the Data Fetcher

```bash
# Install dependencies
pip install -r requirements.txt

# Run the YouTube data fetcher
python3 fetch_youtube_data.py
```

This will:
- Fetch data from @MrBeast (UCX6OQ3DkcsbYNE6H8uQQuVA)
- Fetch data from @MrBeast2 (UC4-79UOlP48-QNGgCko5p2g)
- Fetch data from MrBeast Gaming (UCIPPMRA040LQr5QPyJEbmXA)
- Analyze title patterns, upload frequency, engagement
- Save raw data to `data/youtube_data.json`

### What Gets Analyzed

**Per Channel:**
- Channel statistics (subscribers, total views, video count)
- Recent 50 videos with:
  - Title, description, thumbnail
  - View count, likes, comments
  - Publication date
- Title patterns ($, urgency words, questions)
- Upload frequency (daily/weekly/biweekly/monthly)
- Average engagement metrics

### Using Real Data in Dashboard

Once you've fetched the data, the dashboard will use real metrics:

```bash
streamlit run dashboard.py
```

The dashboard will now show:
- Actual view distributions
- Real engagement trends
- Title pattern analysis
- Upload timing effectiveness

### API Rate Limits

YouTube API v3 free tier: **10,000 quota units per day**

Each request costs:
- `channels.list` = 1 unit
- `playlistItems.list` = 1 unit per 50 items
- `videos.list` = 1 unit per 50 videos

**Estimated cost per full run:** ~50-100 units

### Troubleshooting

**"API key not valid"**
- Check your API key is correctly set
- Verify YouTube Data API v3 is enabled in Cloud Console

**"quota exceeded"**
- You've hit daily limit (10,000 units)
- Wait until next day or upgrade to paid plan

**"No videos found"**
- Channel might be set to private or removed
- Check channel IDs are correct

### Next Steps

1. Run `python3 fetch_youtube_data.py` to get real data
2. Open `data/youtube_data.json` to see results
3. Use real metrics in analysis and dashboard
4. Update insights based on actual channel patterns

---

**Channels Analyzed:**
- @MrBeast (main channel)
- @MrBeast2 (second channel)
- MrBeast Gaming (gaming vertical)
- Mark Rober (competitor benchmark)
