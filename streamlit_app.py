# streamlit_app.py
import streamlit as st
import json
import os
from link import SpotifyAPI
from llm_handler import LLMHandler
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Spotify AI Playlist Curator",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Spotify-like theme
def load_css():
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --spotify-black: #191414;
        --spotify-dark: #1f1f1f;
        --spotify-red: #1DB954;
        --spotify-light-red: #1ed760;
        --spotify-white: #ffffff;
    }
    
    .main {
        background-color: var(--spotify-black);
    }
    
    .stApp {
        background-color: var(--spotify-black);
        color: var(--spotify-white);
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1lcbmhc {
        background-color: var(--spotify-black) !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--spotify-white) !important;
        font-family: 'Spotify Circular', Helvetica, Arial, sans-serif;
    }
    
    /* Text */
    .stMarkdown, .stText, .stCaption {
        color: var(--spotify-white) !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--spotify-red) !important;
        color: white !important;
        border: none !important;
        border-radius: 500px !important;
        padding: 12px 32px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background-color: var(--spotify-light-red) !important;
        transform: scale(1.04) !important;
    }
    
    /* Select boxes */
    .stSelectbox>div>div>div {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
        border: 1px solid #404040 !important;
    }
    
    /* Text input */
    .stTextInput>div>div>input {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
        border: 1px solid #404040 !important;
    }
    
    /* Number input */
    .stNumberInput>div>div>input {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
        border: 1px solid #404040 !important;
    }
    
    /* Dataframes and tables */
    .dataframe {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
    }
    
    .dataframe th {
        background-color: #2a2a2a !important;
        color: var(--spotify-white) !important;
    }
    
    .dataframe td {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
        border-bottom: 1px solid #404040 !important;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: rgba(29, 185, 84, 0.1) !important;
        border: 1px solid var(--spotify-red) !important;
        color: var(--spotify-white) !important;
    }
    
    /* Info messages */
    .stInfo {
        background-color: rgba(29, 185, 84, 0.1) !important;
        border: 1px solid var(--spotify-red) !important;
        color: var(--spotify-white) !important;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid #ffa500 !important;
        color: var(--spotify-white) !important;
    }
    
    /* Error messages */
    .stError {
        background-color: rgba(255, 0, 0, 0.1) !important;
        border: 1px solid #ff4444 !important;
        color: var(--spotify-white) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: var(--spotify-red) !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--spotify-black) 0%, #121212 100%) !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background-color: var(--spotify-dark) !important;
        padding: 10px;
        border-radius: 8px;
    }
    
    .stRadio > div > label {
        color: var(--spotify-white) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--spotify-dark) !important;
        color: var(--spotify-white) !important;
        border: 1px solid #404040 !important;
    }
    
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'spotify_api' not in st.session_state:
        st.session_state.spotify_api = None
    if 'playlists' not in st.session_state:
        st.session_state.playlists = None
    if 'selected_playlist' not in st.session_state:
        st.session_state.selected_playlist = None
    if 'tracks_data' not in st.session_state:
        st.session_state.tracks_data = None
    if 'custom_playlists' not in st.session_state:
        st.session_state.custom_playlists = None
    if 'llm_handler' not in st.session_state:
        st.session_state.llm_handler = None

def connect_spotify():
    """Initialize Spotify connection"""
    try:
        if st.session_state.spotify_api is None:
            st.session_state.spotify_api = SpotifyAPI()
            st.success("✅ Successfully connected to Spotify!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to connect to Spotify: {e}")
        return False

def connect_ai():
    """Initialize AI connection"""
    try:
        if st.session_state.llm_handler is None:
            st.session_state.llm_handler = LLMHandler()
            st.success("✅ AI connection established!")
        return True
    except Exception as e:
        st.warning(f"⚠️ AI connection failed: {e}")
        return False

def fetch_playlists():
    """Fetch user's playlists"""
    if st.session_state.spotify_api and st.session_state.playlists is None:
        with st.spinner("🎵 Loading your playlists..."):
            st.session_state.playlists = st.session_state.spotify_api.get_user_playlists()
            if st.session_state.playlists:
                st.success(f"✅ Found {len(st.session_state.playlists)} playlists!")
            else:
                st.error("❌ No playlists found!")

def display_playlist_selector():
    """Display playlist selection interface"""
    st.header("📋 Select Your Playlist")
    
    if st.session_state.playlists:
        playlist_names = [f"{p['name']} ({p['tracks_total']} tracks)" for p in st.session_state.playlists]
        
        selected_index = st.selectbox(
            "Choose a playlist to analyze:",
            range(len(playlist_names)),
            format_func=lambda x: playlist_names[x]
        )
        
        st.session_state.selected_playlist = st.session_state.playlists[selected_index]
        
        # Display playlist info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Playlist Name", st.session_state.selected_playlist['name'])
        with col2:
            st.metric("Total Tracks", st.session_state.selected_playlist['tracks_total'])
        with col3:
            st.metric("Owner", st.session_state.selected_playlist['owner'])

def fetch_tracks():
    """Fetch tracks from selected playlist"""
    st.header("🎵 Analyze Tracks")
    
    if st.session_state.selected_playlist:
        max_tracks = min(st.session_state.selected_playlist['tracks_total'], 100)
        limit = st.slider(
            "Number of tracks to analyze:",
            min_value=5,
            max_value=max_tracks,
            value=min(20, max_tracks),
            help="More tracks will give the AI more data to work with, but may take longer to process."
        )
        
        if st.button("🔍 Analyze Tracks", type="primary"):
            with st.spinner(f"Analyzing {limit} tracks from '{st.session_state.selected_playlist['name']}'..."):
                st.session_state.tracks_data = st.session_state.spotify_api.get_playlist_tracks(
                    st.session_state.selected_playlist['id'], 
                    limit=limit
                )
                
                if st.session_state.tracks_data:
                    st.success(f"✅ Successfully analyzed {len(st.session_state.tracks_data)} tracks!")
                    
                    # Display track preview
                    st.subheader("📊 Track Preview")
                    preview_data = []
                    for track in st.session_state.tracks_data[:5]:  # Show first 5 tracks
                        preview_data.append({
                            'Track': track['track_name'],
                            'Artist': track['artist'],
                            'Album': track['album'],
                            'Genres': ', '.join(track['artist_genres'][:3]) if track['artist_genres'] else 'No genres'
                        })
                    
                    st.dataframe(pd.DataFrame(preview_data), width="stretch")
                else:
                    st.error("❌ Failed to fetch tracks from the playlist!")

def create_custom_playlist():
    """Create custom playlist using AI"""
    st.header("🎨 Create Custom Playlist")
    
    if st.session_state.tracks_data:
        col1, col2 = st.columns(2)
        
        with col1:
            mood_description = st.text_input(
                "🎭 Describe the mood or theme:",
                placeholder="e.g., chill study music, energetic workout, romantic evening...",
                help="Be specific about the vibe you want for your playlist"
            )
        
        with col2:
            playlist_name = st.text_input(
                "📝 Playlist Name:",
                value=f"{mood_description.title()} Mix" if mood_description else "My Custom Playlist",
                help="Give your playlist a creative name"
            )
        
        max_tracks = st.slider(
            "Number of tracks in new playlist:",
            min_value=5,
            max_value=min(15, len(st.session_state.tracks_data)),
            value=min(10, len(st.session_state.tracks_data))
        )
        
        if st.button("✨ Generate Playlist with AI", type="primary"):
            if not mood_description:
                st.warning("⚠️ Please describe the mood for your playlist!")
                return
            
            # Test AI connection
            ai_connected = connect_ai()
            
            with st.spinner("🎵 AI is curating your perfect playlist..."):
                try:
                    custom_playlist = st.session_state.llm_handler.analyze_tracks_and_create_playlist(
                        tracks_data=st.session_state.tracks_data,
                        mood_description=mood_description,
                        playlist_name=playlist_name,
                        max_tracks=max_tracks
                    )
                    
                    # Store in database
                    st.session_state.spotify_api.store_custom_playlist(custom_playlist, mood_description)
                    
                    # Display the generated playlist
                    st.success(f"🎉 Your custom playlist '{custom_playlist['playlist_name']}' has been created!")
                    
                    # Show playlist details
                    st.subheader("🎶 Your Custom Playlist")
                    st.write(f"**Description:** {custom_playlist['description']}")
                    
                    # Display tracks in a table
                    tracks_df = pd.DataFrame(custom_playlist['tracks'])
                    tracks_df = tracks_df[['position', 'track_name', 'artist', 'album']]
                    tracks_df.columns = ['#', 'Track Name', 'Artist', 'Album']
                    
                    st.dataframe(tracks_df, width="stretch")
                    
                except Exception as e:
                    st.error(f"❌ Error generating playlist: {e}")
                    st.info("💡 Try adjusting your mood description or selecting more tracks to analyze.")

def view_custom_playlists():
    """View previously created custom playlists"""
    st.header("📂 Your Custom Playlists")
    
    if st.session_state.spotify_api:
        with st.spinner("Loading your custom playlists..."):
            custom_playlists = st.session_state.spotify_api.get_custom_playlists()
            
            if not custom_playlists:
                st.info("You haven't created any custom playlists yet. Create one in the 'Create Playlist' section!")
                return
            
            for playlist in custom_playlists:
                with st.expander(f"🎵 {playlist['playlist_name']} - {playlist['created_at'].strftime('%Y-%m-%d')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Description:** {playlist['description']}")
                        st.write(f"**Mood:** {playlist['mood_description']}")
                    
                    with col2:
                        st.write(f"**Created:** {playlist['created_at'].strftime('%b %d, %Y')}")
                    
                    # Show tracks
                    tracks = st.session_state.spotify_api.get_custom_playlist_tracks(playlist['id'])
                    if tracks:
                        tracks_df = pd.DataFrame(tracks)
                        st.dataframe(tracks_df[['position', 'track_name', 'artist', 'album']], 
                                   width="stretch", hide_index=True)
                    else:
                        st.write("No tracks found for this playlist.")

def show_playlist_analytics():
    """Display enhanced playlist analytics"""
    st.header("📊 Playlist Analytics")
    
    if not st.session_state.spotify_api:
        st.error("❌ Please connect to Spotify first!")
        st.info("👈 Click 'Connect to Spotify' in the sidebar")
        return
    
    # Refresh custom playlists for analytics
    with st.spinner("Loading your playlists..."):
        st.session_state.custom_playlists = st.session_state.spotify_api.get_custom_playlists()
    
    if not st.session_state.custom_playlists:
        st.info("📭 No custom playlists found. Create some playlists first!")
        st.write("💡 Go to 'Create Playlist' to generate your first AI-powered playlist!")
        return
    
    st.success(f"✅ Found {len(st.session_state.custom_playlists)} custom playlists!")
    
    # Get user playlist stats
    with st.spinner("Analyzing playlist statistics..."):
        playlist_stats = st.session_state.spotify_api.get_user_playlist_stats(limit=10)
    
    if not playlist_stats:
        st.error("❌ Could not load playlist statistics")
        st.info("This might be because:")
        st.write("- Database views/procedures aren't set up correctly")
        st.write("- There are no tracks in your playlists")
        st.write("- There's a connection issue with the database")
        return
    
    # Display stats in metrics
    st.subheader("📈 Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_playlists = len(playlist_stats)
        st.metric("Total Playlists", total_playlists)
    
    with col2:
        # Safely calculate average tracks
        total_tracks_list = [p['total_tracks'] for p in playlist_stats if isinstance(p['total_tracks'], (int, float))]
        avg_tracks = sum(total_tracks_list) / len(total_tracks_list) if total_tracks_list else 0
        st.metric("Avg Tracks/Playlist", f"{avg_tracks:.1f}")
    
    with col3:
        # Safely calculate max popularity
        popularities = []
        for p in playlist_stats:
            if 'avg_popularity' in p:
                try:
                    pop_val = float(p['avg_popularity'])
                    if pop_val > 0:
                        popularities.append(pop_val)
                except (ValueError, TypeError):
                    continue
        max_popularity = max(popularities) if popularities else 0
        st.metric("Max Avg Popularity", f"{max_popularity:.0f}")
    
    with col4:
        total_tracks = sum([p['total_tracks'] for p in playlist_stats if isinstance(p['total_tracks'], (int, float))])
        st.metric("Total Tracks", total_tracks)
    
    # Display playlist stats table
    st.subheader("🎵 Playlist Statistics")
    if playlist_stats:
        # Convert to DataFrame for nice display
        stats_df = pd.DataFrame(playlist_stats)
        
        # Format the DataFrame - FIXED CODE
        if not stats_df.empty:
            # Convert avg_popularity to numeric, handling errors
            stats_df['avg_popularity'] = pd.to_numeric(stats_df['avg_popularity'], errors='coerce')
            stats_df['avg_popularity'] = stats_df['avg_popularity'].fillna(0)
            stats_df['avg_popularity'] = stats_df['avg_popularity'].round(1)
            
            st.dataframe(stats_df, width="stretch")
        else:
            st.info("No statistics data available")
    else:
        st.info("No playlist statistics to display")
    
    # ... rest of the function remains the same ...

def main():
    # Load custom CSS
    load_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_White.png", 
                 width=150)
        st.title("Spotify AI Curator")
        st.markdown("---")
        
        # Connection status
        st.subheader("🔗 Connections")
        
        if st.button("Connect to Spotify", type="primary"):
            connect_spotify()
            fetch_playlists()
        
        if st.button("Connect to AI"):
            connect_ai()
        
        st.markdown("---")
        
        # Navigation
        st.subheader("🎵 Navigation")
        page = st.radio(
            "Choose a section:",
            ["Create Playlist", "View Playlists", "Playlist Analytics", "About"]
        )
    
    # Main content based on navigation
    if page == "Create Playlist":
        st.header("🎨 Create AI-Powered Playlists")
        st.markdown("Transform your music library into personalized playlists using AI magic!")
        
        # Step-by-step process
        if not st.session_state.spotify_api:
            st.info("👈 Click 'Connect to Spotify' in the sidebar to get started!")
        else:
            if st.session_state.playlists:
                display_playlist_selector()
                fetch_tracks()
                
                if st.session_state.tracks_data:
                    create_custom_playlist()
            else:
                st.warning("No playlists found or couldn't load playlists.")
    
    elif page == "View Playlists":
        st.header("📂 Your Created Playlists")
        st.markdown("Browse and manage your AI-generated playlists")
        
        if st.session_state.spotify_api:
            view_custom_playlists()
        else:
            st.info("👈 Connect to Spotify first to view your playlists!")
    
    elif page == "Playlist Analytics":
        st.header("📊 Playlist Analytics")
        st.markdown("Deep insights into your created playlists and performance metrics")
        
        if st.session_state.spotify_api:
            show_playlist_analytics()
        else:
            st.info("👈 Connect to Spotify first to view analytics!")
    
    elif page == "About":
        st.header("About Spotify AI Curator")
        st.markdown("""
        ### 🎵 How It Works
        
        1. **Connect** to your Spotify account
        2. **Select** a playlist to analyze
        3. **Describe** the mood you want
        4. **Generate** a custom playlist using AI
        5. **Save** to your library or create on Spotify
        
        ### 🚀 Features
        
        - 🤖 AI-powered playlist curation
        - 🎨 Mood-based playlist generation
        - 💾 Save playlists to database
        - 📱 Spotify integration
        - 🎯 Personalized recommendations
        - 📊 Advanced analytics
        
        ### 🔧 Technology Stack
        
        - **Spotify API** - Music data and playback
        - **Gemini AI** - Intelligent playlist generation
        - **MySQL** - Data storage
        - **Streamlit** - Beautiful web interface
        
        ### 📝 Requirements
        
        Make sure you have:
        - Spotify developer credentials
        - Gemini API key
        - MySQL database
        """)

if __name__ == "__main__":
    main()