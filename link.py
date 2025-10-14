import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
from datetime import datetime
from datetime import date
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()
class SpotifyAPI:
    def __init__(self):
        # Initialize Spotify client with necessary scopes
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
            open_browser=True,
            cache_path=".spotify_cache"  # Save tokens to cache file
        )
        
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Initialize MySQL connection
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
            results = self.sp.current_user_playlists()
            
            while results:
                for item in results['items']:
                    playlist = {
                        'id': item['id'],
                        'name': item['name'],
                        'tracks_total': item['tracks']['total'],
                        'owner': item['owner']['display_name']
                    }
                    playlists.append(playlist)
                results = self.sp.next(results) if results['next'] else None
                
            return playlists
            
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return None

    def get_playlist_tracks(self, playlist_id, limit=5):
        """Get metadata for top tracks in a playlist"""
        try:
            tracks_data = []
            results = self.sp.playlist_tracks(playlist_id, limit=limit)
            
            if not results or 'items' not in results:
                print("No tracks found in playlist")
                return []

            for item in results['items']:
                if not item or 'track' not in item or not item['track']:
                    continue

                track = item['track']
                
                # Get artist genres
                genres = []
                try:
                    if track['artists'] and len(track['artists']) > 0:
                        artist = self.sp.artist(track['artists'][0]['id'])
                        if artist and 'genres' in artist:
                            genres = artist['genres']
                except Exception as e:
                    print(f"Warning: Could not fetch genres for {track.get('name', 'Unknown track')}")
                
                # Create track data
                track_data = {
                    "id": track.get('id', ''),
                    "track_name": track.get('name', 'Unknown'),
                    "artist": track['artists'][0]['name'] if track.get('artists') else 'Unknown Artist',
                    "album": track['album']['name'] if track.get('album') else 'Unknown Album',
                    "release_date": track['album']['release_date'] if track.get('album') else None,
                    "artist_genres": genres,
                    "popularity": track.get('popularity', 0)
                }
                
                # Store in database
                try:
                    self.store_track_data(track['id'], track_data)
                    tracks_data.append(track_data)
                except Exception as e:
                    print(f"Warning: Could not store track {track.get('name', 'Unknown')}: {e}")
                    continue

            return tracks_data

        except Exception as e:
            print(f"Error fetching playlist data: {e}")
            return []    

    def store_track_data(self, track_id, track_data):
        try:
            # Get audio features with retry mechanism
            retries = 3
            audio_features = None
            
            # Format release date (handle partial dates)
            release_date = track_data['release_date']
            if release_date:
                if len(release_date) == 4:  # Just year
                    release_date = f"{release_date}-01-01"
                elif len(release_date) == 7:  # Year and month
                    release_date = f"{release_date}-01"
                
            # Insert basic track info
            self.cursor.execute("""
                INSERT INTO tracks (id, track_name, artist, album, release_date, popularity)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    track_name = VALUES(track_name),
                    artist = VALUES(artist),
                    album = VALUES(album),
                    release_date = VALUES(release_date),
                    popularity = VALUES(popularity)
            """, (
                track_id,
                track_data['track_name'],
                track_data['artist'],
                track_data['album'],
                release_date,
                track_data['popularity']
            ))

            # Insert genres
            self.cursor.execute("DELETE FROM artist_genres WHERE track_id = %s", (track_id,))
            for genre in track_data['artist_genres']:
                self.cursor.execute("""
                    INSERT INTO artist_genres (track_id, genre)
                    VALUES (%s, %s)
                """, (track_id, genre))

            # Commit the changes
            self.db.commit()

            # Record the request in track_history (so we can retrieve recent requests)
            try:
                self.cursor.execute("INSERT INTO track_history (track_id) VALUES (%s)", (track_id,))
                self.db.commit()
            except Exception:
                # If history insert fails, don't block the main flow
                self.db.rollback()

        except Exception as e:
            print(f"Error storing track data: {e}")
            self.db.rollback()

    def get_stored_tracks_json(self, limit=5):
        """Retrieve stored tracks from database in JSON format"""
        try:
            tracks = []
            
            # Get tracks with their genres
            self.cursor.execute("""
                SELECT t.id, t.track_name, t.artist, t.album, t.release_date, t.popularity,
                       GROUP_CONCAT(ag.genre) as genres
                FROM tracks t
                LEFT JOIN artist_genres ag ON t.id = ag.track_id
                GROUP BY t.id
                LIMIT %s
            """, (limit,))
            
            results = self.cursor.fetchall()
            
            if not results:
                print("No tracks found in database")
                return json.dumps([])
            
            for row in results:
                # Format release date if exists
                release_date = row[4]
                if release_date and isinstance(release_date, (date, datetime)):
                    release_date = release_date.strftime('%Y-%m-%d')
                
                track_data = {
                    "id": row[0],
                    "track_name": row[1] or 'Unknown',
                    "artist": row[2] or 'Unknown Artist',
                    "album": row[3] or 'Unknown Album',
                    "release_date": release_date,
                    "artist_genres": row[6].split(',') if row[6] else [],
                    "popularity": row[5] or 0
                }
                tracks.append(track_data)
            
            return json.dumps(tracks, indent=2)

        except mysql.connector.Error as err:
            print(f"Database error while retrieving tracks: {err}")
            return json.dumps([])
        except Exception as e:
            print(f"Unexpected error while retrieving tracks: {e}")
            return json.dumps([])

    def get_recent_tracks_json(self, limit=5):
        """Retrieve most recently requested tracks from database in JSON format"""
        try:
            tracks = []
            # Get recent tracks with their genres and last requested time
            self.cursor.execute("""
                SELECT t.id, t.track_name, t.artist, t.album, t.release_date, t.popularity,
                       GROUP_CONCAT(ag.genre) as genres,
                       MAX(th.requested_at) as last_requested
                FROM track_history th
                JOIN tracks t ON th.track_id = t.id
                LEFT JOIN artist_genres ag ON t.id = ag.track_id
                GROUP BY t.id
                ORDER BY last_requested DESC
                LIMIT %s
            """, (limit,))

            results = self.cursor.fetchall()

            if not results:
                print("No recent tracks found in database")
                return json.dumps([])

            for row in results:
                release_date = row[4]
                if release_date and isinstance(release_date, (date, datetime)):
                    release_date = release_date.strftime('%Y-%m-%d')

                track_data = {
                    "id": row[0],
                    "track_name": row[1] or 'Unknown',
                    "artist": row[2] or 'Unknown Artist',
                    "album": row[3] or 'Unknown Album',
                    "release_date": release_date,
                    "artist_genres": row[6].split(',') if row[6] else [],
                    "popularity": row[5] or 0,
                    "last_requested": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None
                }
                tracks.append(track_data)

            return json.dumps(tracks, indent=2)

        except mysql.connector.Error as err:
            print(f"Database error while retrieving recent tracks: {err}")
            return json.dumps([])
        except Exception as e:
            print(f"Unexpected error while retrieving recent tracks: {e}")
            return json.dumps([])

    def store_custom_playlist(self, playlist_data, mood_description):
        """Store custom generated playlist in database"""
        try:
            # Insert main playlist record
            self.cursor.execute("""
                INSERT INTO custom_playlists (playlist_name, description, mood_description)
                VALUES (%s, %s, %s)
            """, (
                playlist_data['playlist_name'],
                playlist_data['description'],
                mood_description
            ))
            
            playlist_id = self.cursor.lastrowid
            
            # Insert playlist tracks
            for track in playlist_data['tracks']:
                self.cursor.execute("""
                    INSERT INTO custom_playlist_tracks 
                    (playlist_id, track_id, track_name, artist, album, position)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    playlist_id,
                    track.get('track_id'),
                    track['track_name'],
                    track['artist'],
                    track['album'],
                    track['position']
                ))
            
            self.db.commit()
            print(f"✅ Custom playlist '{playlist_data['playlist_name']}' stored in database with ID: {playlist_id}")
            
        except Exception as e:
            print(f"Error storing custom playlist: {e}")
            self.db.rollback()
            raise

    def get_custom_playlists(self):
        """Retrieve all custom generated playlists"""
        try:
            self.cursor.execute("""
                SELECT id, playlist_name, description, mood_description, created_at
                FROM custom_playlists 
                ORDER BY created_at DESC
            """)
            
            playlists = []
            for row in self.cursor.fetchall():
                playlist = {
                    'id': row[0],
                    'playlist_name': row[1],
                    'description': row[2],
                    'mood_description': row[3],
                    'created_at': row[4]
                }
                playlists.append(playlist)
            
            return playlists
            
        except Exception as e:
            print(f"Error fetching custom playlists: {e}")
            return []

    def get_custom_playlist_tracks(self, playlist_id):
        """Get tracks for a specific custom playlist"""
        try:
            self.cursor.execute("""
                SELECT track_name, artist, album, position
                FROM custom_playlist_tracks
                WHERE playlist_id = %s
                ORDER BY position
            """, (playlist_id,))
            
            tracks = []
            for row in self.cursor.fetchall():
                track = {
                    'track_name': row[0],
                    'artist': row[1],
                    'album': row[2],
                    'position': row[3]
                }
                tracks.append(track)
            
            return tracks
            
        except Exception as e:
            print(f"Error fetching custom playlist tracks: {e}")
            return []

    def get_all_tracks_for_analysis(self, limit=50):
        """Get all available tracks from database for LLM analysis"""
        try:
            tracks = []
            
            # Get tracks with their genres
            self.cursor.execute("""
                SELECT t.id, t.track_name, t.artist, t.album, t.release_date, t.popularity,
                       GROUP_CONCAT(ag.genre) as genres
                FROM tracks t
                LEFT JOIN artist_genres ag ON t.id = ag.track_id
                GROUP BY t.id
                ORDER BY t.popularity DESC
                LIMIT %s
            """, (limit,))
            
            results = self.cursor.fetchall()
            
            if not results:
                print("No tracks found in database for analysis")
                return []
            
            for row in results:
                # Format release date if exists
                release_date = row[4]
                if release_date and isinstance(release_date, (date, datetime)):
                    release_date = release_date.strftime('%Y-%m-%d')
                
                track_data = {
                    "id": row[0],
                    "track_name": row[1] or 'Unknown',
                    "artist": row[2] or 'Unknown Artist',
                    "album": row[3] or 'Unknown Album',
                    "release_date": release_date,
                    "artist_genres": row[6].split(',') if row[6] else [],
                    "popularity": row[5] or 0
                }
                tracks.append(track_data)
            
            return tracks

        except mysql.connector.Error as err:
            print(f"Database error while retrieving tracks for analysis: {err}")
            return []
        except Exception as e:
            print(f"Unexpected error while retrieving tracks for analysis: {e}")
            return []

    def create_spotify_playlist(self, playlist_name, description, track_ids):
        """Create an actual Spotify playlist with the selected tracks"""
        try:
            # Get current user ID
            user = self.sp.current_user()
            user_id = user['id']
            
            # Create empty playlist
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                description=description,
                public=True
            )
            
            # Add tracks to playlist
            if track_ids:
                # Filter out None values
                valid_track_ids = [tid for tid in track_ids if tid]
                if valid_track_ids:
                    self.sp.playlist_add_items(playlist['id'], valid_track_ids)
            
            print(f"✅ Spotify playlist '{playlist_name}' created successfully!")
            print(f"🔗 Playlist URL: {playlist['external_urls']['spotify']}")
            
            return playlist
            
        except Exception as e:
            print(f"Error creating Spotify playlist: {e}")
            return None

    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.db.close()