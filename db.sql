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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for storing artist genres
CREATE TABLE artist_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    genre VARCHAR(100),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- Table for tracking song request history
CREATE TABLE track_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- Table for storing custom generated playlists
CREATE TABLE custom_playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_name VARCHAR(255) NOT NULL,
    description TEXT,
    mood_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for storing tracks in custom playlists
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

-- Audit tables
CREATE TABLE track_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    old_popularity INT,
    new_popularity INT,
    changed_by VARCHAR(100),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE TABLE playlist_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_id INT,
    old_name VARCHAR(255),
    new_name VARCHAR(255),
    changed_by VARCHAR(100),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES custom_playlists(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_track_name ON tracks(track_name);
CREATE INDEX idx_artist ON tracks(artist);
CREATE INDEX idx_album ON tracks(album);
CREATE INDEX idx_genre ON artist_genres(genre);
CREATE INDEX idx_requested_at ON track_history(requested_at);
CREATE INDEX idx_custom_playlist_name ON custom_playlists(playlist_name);
CREATE INDEX idx_track_audit_date ON track_audit(change_date);
CREATE INDEX idx_playlist_audit_date ON playlist_audit(change_date);

-- Create triggers
DELIMITER //

CREATE TRIGGER track_update_audit 
    AFTER UPDATE ON tracks
    FOR EACH ROW
BEGIN
    IF OLD.popularity != NEW.popularity THEN
        INSERT INTO track_audit (track_id, old_popularity, new_popularity, changed_by)
        VALUES (OLD.id, OLD.popularity, NEW.popularity, USER());
    END IF;
END //

CREATE TRIGGER playlist_name_audit
    AFTER UPDATE ON custom_playlists
    FOR EACH ROW
BEGIN
    IF OLD.playlist_name != NEW.playlist_name THEN
        INSERT INTO playlist_audit (playlist_id, old_name, new_name, changed_by)
        VALUES (OLD.id, OLD.playlist_name, NEW.playlist_name, USER());
    END IF;
END //

DELIMITER ;

-- Create enhanced views
CREATE VIEW enhanced_playlist_view AS
SELECT 
    p.id,
    p.playlist_name,
    p.description,
    p.mood_description,
    COUNT(DISTINCT pt.track_id) as total_tracks,
    AVG(t.popularity) as avg_popularity,
    MIN(t.popularity) as min_popularity,
    MAX(t.popularity) as max_popularity,
    GROUP_CONCAT(DISTINCT ag.genre) as all_genres,
    p.created_at,
    p.updated_at
FROM custom_playlists p
LEFT JOIN custom_playlist_tracks pt ON p.id = pt.playlist_id
LEFT JOIN tracks t ON pt.track_id = t.id
LEFT JOIN artist_genres ag ON t.id = ag.track_id
GROUP BY p.id, p.playlist_name, p.description, p.mood_description, p.created_at, p.updated_at;

-- Create stored procedures
DELIMITER //

CREATE PROCEDURE GetEnhancedPlaylistAnalysis(IN p_playlist_id INT)
BEGIN
    SELECT 
        playlist_name,
        description,
        mood_description,
        total_tracks,
        avg_popularity,
        min_popularity,
        max_popularity,
        all_genres,
        created_at
    FROM enhanced_playlist_view 
    WHERE id = p_playlist_id;
END //

CREATE PROCEDURE GetUserPlaylistStats(IN p_limit INT)
BEGIN
    SELECT 
        playlist_name,
        total_tracks,
        avg_popularity,
        all_genres,
        created_at
    FROM enhanced_playlist_view 
    ORDER BY created_at DESC
    LIMIT p_limit;
END //

DELIMITER ;