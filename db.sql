DROP DATABASE IF EXISTS spotify_tracks;
CREATE DATABASE spotify_tracks;
USE spotify_tracks;

-- 1. Base Tables
CREATE TABLE tracks (
    id VARCHAR(255) PRIMARY KEY,
    track_name VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255) NOT NULL,
    release_date VARCHAR(10),
    popularity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE artist_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    genre VARCHAR(100),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE TABLE track_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- 2. Custom Playlists (With Cached Stats Columns)
CREATE TABLE custom_playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_name VARCHAR(255) NOT NULL,
    description TEXT,
    mood_description TEXT,
    total_tracks INT DEFAULT 0,      -- Cached count
    total_popularity INT DEFAULT 0,  -- Cached sum
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- 3. Indexes
CREATE INDEX idx_track_name ON tracks(track_name);
CREATE INDEX idx_genre ON artist_genres(genre);
CREATE INDEX idx_cp_created ON custom_playlists(created_at);

-- 4. Triggers (The Magic Engine)
DELIMITER //

-- Updates stats automatically when tracks are added
CREATE TRIGGER update_playlist_stats_insert 
AFTER INSERT ON custom_playlist_tracks 
FOR EACH ROW 
BEGIN
    DECLARE track_pop INT;
    SELECT IFNULL(popularity, 0) INTO track_pop FROM tracks WHERE id = NEW.track_id;
    
    UPDATE custom_playlists 
    SET total_tracks = total_tracks + 1,
        total_popularity = total_popularity + track_pop
    WHERE id = NEW.playlist_id;
END //

-- Updates stats automatically when tracks are deleted
CREATE TRIGGER update_playlist_stats_delete
AFTER DELETE ON custom_playlist_tracks
FOR EACH ROW
BEGIN
    DECLARE track_pop INT;
    SELECT IFNULL(popularity, 0) INTO track_pop FROM tracks WHERE id = OLD.track_id;
    
    UPDATE custom_playlists 
    SET total_tracks = GREATEST(0, total_tracks - 1),
        total_popularity = GREATEST(0, total_popularity - track_pop)
    WHERE id = OLD.playlist_id;
END //
DELIMITER ;

-- 5. View & Procedures
CREATE VIEW fast_analytics_view AS
SELECT 
    p.id, p.playlist_name, p.description, p.mood_description, p.total_tracks,
    CASE WHEN p.total_tracks > 0 THEN ROUND(p.total_popularity / p.total_tracks, 1) ELSE 0 END as avg_popularity,
    (SELECT GROUP_CONCAT(DISTINCT ag.genre ORDER BY ag.genre SEPARATOR ', ')
     FROM custom_playlist_tracks cpt
     JOIN artist_genres ag ON cpt.track_id = ag.track_id
     WHERE cpt.playlist_id = p.id) as all_genres,
    p.created_at
FROM custom_playlists p;

DELIMITER //
CREATE PROCEDURE GetEnhancedPlaylistAnalysis(IN p_playlist_id INT)
BEGIN
    SELECT * FROM fast_analytics_view WHERE id = p_playlist_id;
END //

CREATE PROCEDURE GetUserPlaylistStats(IN p_limit INT)
BEGIN
    SELECT playlist_name, total_tracks, avg_popularity, all_genres, created_at
    FROM fast_analytics_view ORDER BY created_at DESC LIMIT p_limit;
END //
DELIMITER ;