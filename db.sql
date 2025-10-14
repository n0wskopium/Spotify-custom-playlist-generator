-- Database schema for storing Spotify track metadata
DROP DATABASE IF EXISTS spotify_tracks;
CREATE DATABASE spotify_tracks;
USE spotify_tracks;

-- Table for storing track basic information
CREATE TABLE tracks (
    id VARCHAR(255) PRIMARY KEY,
    track_name VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255) NOT NULL,
    release_date VARCHAR(10),  -- Changed from DATE to VARCHAR to handle partial dates
    popularity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing artist genres
CREATE TABLE artist_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    genre VARCHAR(100),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- Table for tracking song request history
CREATE TABLE IF NOT EXISTS track_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- NEW: Table for storing custom generated playlists
CREATE TABLE custom_playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_name VARCHAR(255) NOT NULL,
    description TEXT,
    mood_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Table for storing tracks in custom playlists
CREATE TABLE custom_playlist_tracks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_id INT,
    track_id VARCHAR(255),
    track_name VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255) NOT NULL,
    position INT,
    FOREIGN KEY (playlist_id) REFERENCES custom_playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE SET NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_track_name ON tracks(track_name);
CREATE INDEX idx_artist ON tracks(artist);
CREATE INDEX idx_album ON tracks(album);
CREATE INDEX idx_genre ON artist_genres(genre);
CREATE INDEX idx_requested_at ON track_history(requested_at);
CREATE INDEX idx_custom_playlist_name ON custom_playlists(playlist_name);