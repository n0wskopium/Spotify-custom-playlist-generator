import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
from datetime import datetime, date
import json
import os
from dotenv import load_dotenv

load_dotenv()

class SpotifyAPI:
    def __init__(self):
        # Scopes for reading library and modifying playlists
        scope = " ".join([
            "playlist-read-private",
            "playlist-read-collaborative",
            "user-library-read",
            "user-read-private",
            "user-read-email",
            "playlist-modify-public",
            "playlist-modify-private"
        ])
        
        auth_manager = SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri="http://127.0.0.1:8000/callback",
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        self.cursor = self.db.cursor()

    def get_user_playlists(self):
        """Get all playlists of the current user"""
        try:
            playlists = []
            results = self.sp.current_user_playlists(limit=50)
            while results:
                for item in results['items']:
                    if item:
                        playlists.append({
                            'id': item['id'],
                            'name': item['name'],
                            'tracks_total': item['tracks']['total'],
                            'owner': item['owner']['display_name']
                        })
                results = self.sp.next(results) if results['next'] else None
            return playlists
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return []

    def get_playlist_tracks(self, playlist_id, limit=20):
        """Get metadata for tracks with optimized batch processing"""
        try:
            # 1. Fetch tracks from Spotify
            results = self.sp.playlist_tracks(playlist_id, limit=limit)
            if not results or 'items' not in results:
                print("No tracks found in playlist")
                return []

            raw_items = [item['track'] for item in results['items'] if item and item.get('track')]
            artist_ids = set()
            
            # Collect all Artist IDs first
            for track in raw_items:
                if track.get('artists'):
                    artist_ids.add(track['artists'][0]['id'])

            # 2. Batch Fetch Artist Genres (1 call per 50 artists vs 1 call per track)
            artist_genres_map = {}
            if artist_ids:
                artist_ids_list = list(artist_ids)
                for i in range(0, len(artist_ids_list), 50):
                    batch = artist_ids_list[i:i+50]
                    try:
                        artists_info = self.sp.artists(batch)
                        for artist in artists_info['artists']:
                            artist_genres_map[artist['id']] = artist.get('genres', [])
                    except Exception as e:
                        print(f"Warning: Error fetching artist batch: {e}")

            # 3. Construct Track Data Objects
            tracks_data = []
            for track in raw_items:
                primary_artist = track['artists'][0] if track.get('artists') else None
                genres = artist_genres_map.get(primary_artist['id'], []) if primary_artist else []
                
                tracks_data.append({
                    "id": track.get('id', ''),
                    "track_name": track.get('name', 'Unknown'),
                    "artist": primary_artist['name'] if primary_artist else 'Unknown',
                    "album": track['album']['name'] if track.get('album') else 'Unknown',
                    "release_date": track['album']['release_date'] if track.get('album') else None,
                    "artist_genres": genres,
                    "popularity": track.get('popularity', 0)
                })

            # 4. Batch Store in Database
            if tracks_data:
                self.store_tracks_batch(tracks_data)
            
            return tracks_data

        except Exception as e:
            print(f"Error fetching playlist data: {e}")
            return []

    def store_tracks_batch(self, tracks_data):
        """Optimized batch storage of tracks, genres, and history"""
        try:
            track_values = []
            genre_values = []
            history_values = []
            
            for t in tracks_data:
                # Format date
                r_date = t['release_date']
                if r_date:
                    if len(r_date) == 4: r_date += "-01-01"
                    elif len(r_date) == 7: r_date += "-01"
                
                track_values.append((
                    t['id'], t['track_name'], t['artist'], t['album'], r_date, t['popularity']
                ))
                
                for g in t['artist_genres']:
                    genre_values.append((t['id'], g))
                
                history_values.append((t['id'],))

            # Bulk Upsert Tracks
            self.cursor.executemany("""
                INSERT INTO tracks (id, track_name, artist, album, release_date, popularity)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    track_name = VALUES(track_name), artist = VALUES(artist),
                    album = VALUES(album), popularity = VALUES(popularity)
            """, track_values)

            # Refresh Genres (Delete old for these tracks, Insert new)
            track_ids = [t[0] for t in track_values]
            if track_ids:
                format_strings = ','.join(['%s'] * len(track_ids))
                self.cursor.execute(f"DELETE FROM artist_genres WHERE track_id IN ({format_strings})", track_ids)
                
                if genre_values:
                    self.cursor.executemany("INSERT INTO artist_genres (track_id, genre) VALUES (%s, %s)", genre_values)
                
                # Log History
                if history_values:
                    self.cursor.executemany("INSERT INTO track_history (track_id) VALUES (%s)", history_values)

            self.db.commit()
            
        except Exception as e:
            print(f"Error storing batch tracks: {e}")
            self.db.rollback()

    def store_custom_playlist(self, playlist_data, mood_description):
        """Store custom playlist using batch processing"""
        try:
            # Insert Playlist Header
            self.cursor.execute("""
                INSERT INTO custom_playlists (playlist_name, description, mood_description)
                VALUES (%s, %s, %s)
            """, (playlist_data['playlist_name'], playlist_data['description'], mood_description))
            
            playlist_id = self.cursor.lastrowid
            
            # Batch Insert Tracks (Triggers in DB will update stats automatically)
            track_values = []
            for track in playlist_data['tracks']:
                track_values.append((
                    playlist_id, track.get('track_id'), track['track_name'],
                    track['artist'], track['album'], track['position']
                ))
            
            if track_values:
                self.cursor.executemany("""
                    INSERT INTO custom_playlist_tracks 
                    (playlist_id, track_id, track_name, artist, album, position)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, track_values)
            
            self.db.commit()
            print(f"✅ Custom playlist '{playlist_data['playlist_name']}' stored with ID: {playlist_id}")
            
        except Exception as e:
            print(f"Error storing custom playlist: {e}")
            self.db.rollback()

    def get_enhanced_playlist_analysis(self, playlist_id):
        """Get analytics using the Optimized View via Stored Procedure"""
        try:
            self.cursor.callproc('GetEnhancedPlaylistAnalysis', [playlist_id])
            for result in self.cursor.stored_results():
                row = result.fetchone()
                if row:
                    return dict(zip(result.column_names, row))
            return None
        except Exception as e:
            print(f"Error in enhanced analysis: {e}")
            return None

    def get_user_playlist_stats(self, limit=5):
        """Get list of playlists with stats via Stored Procedure"""
        try:
            self.cursor.callproc('GetUserPlaylistStats', [limit])
            for result in self.cursor.stored_results():
                columns = result.column_names
                return [dict(zip(columns, row)) for row in result.fetchall()]
            return []
        except Exception as e:
            print(f"Error getting playlist stats: {e}")
            return []

    def get_custom_playlists(self):
        """Standard retrieval of playlists"""
        try:
            self.cursor.execute("""
                SELECT id, playlist_name, description, mood_description, created_at 
                FROM custom_playlists ORDER BY created_at DESC
            """)
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching custom playlists: {e}")
            return []

    def get_custom_playlist_tracks(self, playlist_id):
        """Standard retrieval of playlist tracks"""
        try:
            self.cursor.execute("""
                SELECT track_name, artist, album, position 
                FROM custom_playlist_tracks 
                WHERE playlist_id = %s ORDER BY position
            """, (playlist_id,))
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching custom playlist tracks: {e}")
            return []

    def create_spotify_playlist(self, playlist_name, description, track_ids):
        """Create playlist on Spotify"""
        try:
            user_id = self.sp.current_user()['id']
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                description=description,
                public=True
            )
            
            valid_ids = [tid for tid in track_ids if tid]
            if valid_ids:
                self.sp.playlist_add_items(playlist['id'], valid_ids)
            
            return playlist
        except Exception as e:
            print(f"Error creating Spotify playlist: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.db.is_connected():
            self.cursor.close()
            self.db.close()