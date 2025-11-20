import google.generativeai as genai
import json
import os
import re
from typing import List, Dict, Any

class LLMHandler:
    def __init__(self, api_key: str = None):
        """Initialize Gemini API handler"""
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass as argument.")
        
        genai.configure(api_key=api_key)
        
        # Use the updated model name
        try:
            self.model = genai.GenerativeModel('models/gemini-2.5-pro')
        except:
            try:
                self.model = genai.GenerativeModel('models/gemini-2.5-flash')
            except:
                self.model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    def analyze_tracks_and_create_playlist(self, tracks_data: List[Dict], mood_description: str, playlist_name: str, max_tracks: int = 10) -> Dict[str, Any]:
        """Analyze tracks and create a custom playlist based on mood description"""
        
        # Prepare track information for the prompt
        tracks_info = []
        for track in tracks_data:
            track_info = {
                'track_name': track.get('track_name', 'Unknown'),
                'artist': track.get('artist', 'Unknown Artist'),
                'album': track.get('album', 'Unknown Album'),
                'genres': track.get('artist_genres', []),
                'popularity': track.get('popularity', 0),
                'release_date': track.get('release_date', 'Unknown')
            }
            tracks_info.append(track_info)
        
        # Create the prompt for Gemini
        prompt = self._create_playlist_prompt(tracks_info, mood_description, playlist_name, max_tracks)
        
        try:
            # Add safety settings to avoid blocks
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,  # Increased token limit
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            print(f"🔍 Raw LLM response received: {len(response.text)} characters")
            playlist_data = self._parse_llm_response(response.text, tracks_data, max_tracks)
            
            return playlist_data
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Fallback to simple playlist creation
            return self._create_fallback_playlist(tracks_data, mood_description, playlist_name, max_tracks)
    
    def _create_playlist_prompt(self, tracks_info: List[Dict], mood_description: str, playlist_name: str, max_tracks: int) -> str:
        """Create the prompt for playlist generation"""
        
        tracks_json = json.dumps(tracks_info, indent=2)
        
        prompt = f"""
        TASK: Create a music playlist based on user's mood description and available tracks.

        USER REQUEST:
        - Mood/Theme: "{mood_description}"
        - Playlist Name: "{playlist_name}"
        - Maximum Tracks: {max_tracks}

        AVAILABLE TRACKS DATA:
        {tracks_json}

        INSTRUCTIONS:
        1. Select exactly {max_tracks} tracks that best match the mood description
        2. Consider: genres, artist style, popularity, and emotional tone giving more weight to whats asked
        3. Make a comparison between tracks and what the user wants to finalise on a track
        4. Create a logical listening order
        5. Return ONLY valid JSON with this exact structure - NO EXTRA TEXT:

        {{
            "playlist_name": "creative name based on mood",
            "description": "catchy 1-2 sentence Spotify-style description",
            "tracks": [
                {{
                    "track_name": "exact track name from available list",
                    "artist": "exact artist name from available list", 
                    "album": "exact album name from available list",
                    "position": 1
                }},
                ... more tracks ...
            ]
        }}

        CRITICAL RULES:
        - Use ONLY tracks from the available list above
        - Use EXACT track names, artist names, and album names as provided
        - Return COMPLETE JSON only - make sure all brackets are closed
        - Ensure proper JSON syntax with double quotes
        - Order tracks for optimal listening experience
        - MAXIMUM {max_tracks} TRACKS ONLY
        - Make sure the JSON is complete and valid
        """

        return prompt
    
    def _parse_llm_response(self, response_text: str, original_tracks: List[Dict], max_tracks: int) -> Dict[str, Any]:
        """Parse the LLM response and extract playlist data with robust error handling"""
        try:
            print("🔄 Parsing LLM response...")
            
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in cleaned_text:
                cleaned_text = cleaned_text.split('```json')[1].split('```')[0].strip()
            elif '```' in cleaned_text:
                cleaned_text = cleaned_text.split('```')[1].strip()
            
            # Find JSON object
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
            
            json_text = cleaned_text[start_idx:end_idx]
            
            # Fix common JSON issues
            json_text = self._fix_json_issues(json_text, max_tracks)
            
            playlist_data = json.loads(json_text)
            
            # Validate the structure
            required_keys = ['playlist_name', 'description', 'tracks']
            if not all(key in playlist_data for key in required_keys):
                raise ValueError("Missing required keys in LLM response")
            
            if not isinstance(playlist_data['tracks'], list):
                raise ValueError("Tracks should be a list")
            
            # Match tracks with original data to get IDs
            self._match_tracks_with_ids(playlist_data['tracks'], original_tracks)
            
            print(f"✅ Successfully parsed playlist with {len(playlist_data['tracks'])} tracks")
            return playlist_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"📝 Problematic JSON text: {json_text if 'json_text' in locals() else 'N/A'}")
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            print(f"❌ General parsing error: {e}")
            raise ValueError(f"Invalid response format: {str(e)}")
    
    def _fix_json_issues(self, json_text: str, max_tracks: int) -> str:
        """Fix common JSON issues in LLM responses"""
        
        # Fix 1: Add missing closing brackets
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        
        # Add missing closing braces
        if open_braces > close_braces:
            json_text += '}' * (open_braces - close_braces)
        
        # Add missing closing brackets
        if open_brackets > close_brackets:
            json_text += ']' * (open_brackets - close_brackets)
        
        # Fix 2: Remove trailing commas
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        # Fix 3: Ensure tracks array is properly closed
        if '"tracks": [' in json_text and ']' not in json_text.split('"tracks": [')[-1]:
            # Count how many tracks we have
            track_count = json_text.count('"track_name"')
            # If we have some tracks but array isn't closed, close it
            if track_count > 0:
                # Find the last complete track
                last_track_end = max(
                    json_text.rfind('}'),
                    json_text.rfind('",')
                )
                if last_track_end != -1:
                    json_text = json_text[:last_track_end + 1] + ']'
        
        # Fix 4: If JSON is still broken, create a simple valid one
        try:
            json.loads(json_text)
        except:
            print("⚠️ JSON auto-repair failed, creating fallback structure")
            # Extract what we can and create minimal valid JSON
            json_text = self._create_minimal_json(json_text, max_tracks)
        
        return json_text
    
    def _create_minimal_json(self, broken_json: str, max_tracks: int) -> str:
        """Create minimal valid JSON from broken response"""
        try:
            # Extract playlist name
            name_match = re.search(r'"playlist_name":\s*"([^"]*)"', broken_json)
            playlist_name = name_match.group(1) if name_match else "Custom Playlist"
            
            # Extract description
            desc_match = re.search(r'"description":\s*"([^"]*)"', broken_json)
            description = desc_match.group(1) if desc_match else "A curated playlist for you"
            
            # Extract tracks
            tracks = []
            track_pattern = r'"track_name":\s*"([^"]*)",\s*"artist":\s*"([^"]*)",\s*"album":\s*"([^"]*)"'
            for match in re.finditer(track_pattern, broken_json):
                if len(tracks) < max_tracks:
                    tracks.append({
                        "track_name": match.group(1),
                        "artist": match.group(2),
                        "album": match.group(3),
                        "position": len(tracks) + 1
                    })
            
            # Create valid JSON
            minimal_json = {
                "playlist_name": playlist_name,
                "description": description,
                "tracks": tracks
            }
            
            return json.dumps(minimal_json)
        except:
            # Ultimate fallback
            return '{"playlist_name": "My Playlist", "description": "A great music collection", "tracks": []}'
    
    def _match_tracks_with_ids(self, selected_tracks: List[Dict], original_tracks: List[Dict]):
        """Match selected tracks with their original track IDs"""
        for selected_track in selected_tracks:
            selected_track['track_id'] = None  # Initialize
            for original_track in original_tracks:
                if (selected_track['track_name'].lower() == original_track.get('track_name', '').lower() and
                    selected_track['artist'].lower() == original_track.get('artist', '').lower()):
                    selected_track['track_id'] = original_track.get('id')
                    break
    
    def _create_fallback_playlist(self, tracks_data: List[Dict], mood_description: str, playlist_name: str, max_tracks: int) -> Dict[str, Any]:
        """Create a playlist without AI when Gemini fails"""
        print("🔄 Using fallback playlist generator...")
        
        # Simple selection - take first N tracks
        selected_tracks = tracks_data[:max_tracks]
        
        playlist_data = {
            "playlist_name": playlist_name or f"{mood_description.title()} Mix",
            "description": f"A {mood_description} playlist curated for you",
            "tracks": []
        }
        
        for i, track in enumerate(selected_tracks, 1):
            playlist_data["tracks"].append({
                "track_name": track.get('track_name', 'Unknown'),
                "artist": track.get('artist', 'Unknown Artist'),
                "album": track.get('album', 'Unknown Album'),
                "position": i,
                "track_id": track.get('id')
            })
        
        return playlist_data

    def test_connection(self):
        """Test if Gemini API is working"""
        try:
            response = self.model.generate_content("Just say \"connecting..,\" and nothing else.")
            return f"✅ Gemini API connected: {response.text}"
        except Exception as e:
            return f"❌ Gemini API error: {e}"