# Spotify Playlist Analyzer & AI Curator 🎵

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)](https://mysql.com)
[![Spotify API](https://img.shields.io/badge/Spotify-API-brightgreen)](https://developer.spotify.com)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-yellow)](https://ai.google.dev)

An intelligent music recommendation system that combines Spotify's music library with Google's Gemini AI to create personalized playlists based on your mood descriptions.

## 🌟 Features

- **AI-Powered Playlist Creation**: Generate custom playlists using natural language descriptions
- **Spotify Integration**: Analyze your existing playlists and music taste
- **Smart Mood Matching**: AI understands emotional context and musical preferences
- **Beautiful Terminal UI**: Rich, formatted interface with emojis and tables
- **Database Storage**: Store analyzed tracks and generated playlists in MySQL
- **Error Handling**: Robust error recovery and fallback mechanisms

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Spotify Developer Account
- Google AI Studio Account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/spotify-playlist-analyzer.git
cd spotify-playlist-analyzer

    Install dependencies

bash

pip install -r requirements.txt

    Setup MySQL database

bash

mysql -u root -p < db.sql

    Configure environment variables

bash

cp .env.example .env
# Edit .env with your API keys and database credentials

    Run the application

bash

python index.py

🔧 Configuration
API Setup

    Spotify Developer Dashboard

        Visit Spotify Developer

        Create a new app

        Add http://127.0.0.1:8000/callback as redirect URI

        Copy Client ID and Client Secret to .env

    Google AI Studio

        Visit Google AI Studio

        Generate an API key for Gemini AI

        Add to .env file

Environment Variables

Create a .env file:
env

# Database
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=spotify_tracks

# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

🎯 Usage

    Run the application
    bash

python index.py

    Select a playlist from your Spotify account

    Choose how many tracks to analyze (1-100)

    Describe your mood (e.g., "chill study music", "energetic workout")

    Name your playlist or use AI-generated name

    Watch the magic happen! 🎵

Example Session
text

📋 Your Playlists:
┏━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ #   ┃ Playlist Name              ┃ Tracks┃ Owner  ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ 1   │ Liked Songs                │ 245   │ User   │
│ 2   │ Workout Mix                │ 50    │ User   │
└─────┴────────────────────────────┴───────┴────────┘

Enter playlist number: 1
Tracks to analyze: 20
Mood description: focus coding with ambient background music
Playlist name: Code Flow

🎵 Custom Playlist: Code Flow
📝 Deep focus ambient tracks to keep you in the zone while coding

🏗️ Project Structure
text

spotify-playlist-analyzer/
├── 📄 index.py              # Main application & UI
├── 📄 link.py               # Spotify API & database operations
├── 📄 llm_handler.py        # Gemini AI integration
├── 📄 db.sql               # Database schema
├── 📄 requirements.txt     # Python dependencies
├── 📄 .env.example        # Environment template
└── 📄 README.md           # This file

🔌 API Integration
Spotify API Endpoints Used

    current_user_playlists() - Get user's playlists

    playlist_tracks() - Get tracks from specific playlist

    artist() - Get artist details and genres

    current_user() - Get user profile

Gemini AI Models

    gemini-1.5-pro-latest (primary)

    gemini-pro (fallback)

    models/gemini-pro (backup)

🗃️ Database Schema

The system uses 5 main tables:

    tracks: Core track metadata (ID, name, artist, album, popularity)

    artist_genres: Many-to-many genre relationships

    track_history: Request audit trail

    custom_playlists: AI-generated playlist headers

    custom_playlist_tracks: Playlist-track relationships

🛠️ Development
Running Tests
bash

# Test database connection
python -c "from link import SpotifyAPI; s=SpotifyAPI(); print('✅ DB connected')"

# Test Spotify connection
python -c "from link import SpotifyAPI; s=SpotifyAPI(); print(f'✅ {len(s.get_user_playlists())} playlists')"

# Test AI connection
python -c "from llm_handler import LLMHandler; l=LLMHandler(); print('✅ AI connected')"

Code Architecture
🐛 Troubleshooting
Common Issues

Spotify Authentication Failed
bash

rm .spotify_cache  # Clear cached tokens

MySQL Connection Error

    Ensure MySQL service is running

    Verify credentials in .env

AI API Errors

    Check Gemini API key in .env

    Verify internet connection

Module Not Found
bash

pip install -r requirements.txt

Performance Tips

    Limit track analysis to 50-100 for faster processing

    Use stable internet connection for API calls

    Close other bandwidth-intensive applications

🚀 Future Enhancements

    Real Spotify playlist creation

    Audio feature analysis (BPM, energy, danceability)

    Collaborative playlist features

    Web interface

    Mobile app

    Social sharing

🤝 Contributing

    Fork the repository

    Create a feature branch (git checkout -b feature/amazing-feature)

    Commit your changes (git commit -m 'Add amazing feature')

    Push to the branch (git push origin feature/amazing-feature)

    Open a Pull Request

📝 License

This project is for educational purposes. Please comply with:

    Spotify Developer Terms

    Google AI Studio Terms

    MySQL License

🙏 Acknowledgments

    Spotify Web API

    Google Gemini AI

    Spotipy Python Library

    Rich Python Library

<div align="center">

Made with ❤️ and 🎵

Transform your music experience with AI-powered curation!

Report Bug · Request Feature
</div> ```

This README includes:

    Badges for quick project overview

    Clear installation instructions

    Visual examples of how the app works

    Troubleshooting section

    API documentation

    Development guidelines

    Professional formatting
