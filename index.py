from link import SpotifyAPI
from llm_handler import LLMHandler
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import os

def display_playlists(playlists):
    """Display playlists in a formatted table"""
    console = Console()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Playlist Name", width=30)
    table.add_column("Tracks", justify="right", width=8)
    table.add_column("Owner", width=20)
    
    for idx, playlist in enumerate(playlists, 1):
        table.add_row(
            str(idx),
            playlist['name'],
            str(playlist['tracks_total']),
            playlist['owner']
        )
    
    console.print("\n📋 Your Playlists:")
    console.print(table)

def display_custom_playlist(playlist_data):
    """Display the custom generated playlist in a formatted table"""
    console = Console()
    
    # Display playlist header
    console.print(f"\n🎵 [bold cyan]Custom Playlist: {playlist_data['playlist_name']}[/bold cyan]")
    console.print(f"📝 [italic]{playlist_data['description']}[/italic]")
    
    # Create tracks table
    table = Table(show_header=True, header_style="bold green")
    table.add_column("#", style="dim", width=4)
    table.add_column("Track Name", width=35)
    table.add_column("Artist", width=25)
    table.add_column("Album", width=30)
    
    for track in playlist_data['tracks']:
        table.add_row(
            str(track['position']),
            track['track_name'],
            track['artist'],
            track['album']
        )
    
    console.print("\n🎶 Playlist Tracks:")
    console.print(table)

def test_gemini_connection():
    """Test if Gemini API is working"""
    console = Console()
    try:
        console.print("\n🔗 Testing AI connection...", style="bold blue")
        llm_handler = LLMHandler()
        test_result = llm_handler.test_connection()
        
        if "✅" in test_result:
            console.print(f"📡 {test_result}", style="bold green")
            return True, llm_handler
        else:
            console.print(f"⚠️ {test_result}", style="bold yellow")
            return False, None
    except Exception as e:
        console.print(f"❌ AI Connection Failed: {e}", style="bold red")
        return False, None

def get_user_input(prompt, default=None, input_type=str):
    """Get user input with validation and default values"""
    console = Console()
    while True:
        try:
            if default:
                user_input = input(f"{prompt} (default: {default}): ").strip()
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if not user_input and default is not None:
                return default
            
            if not user_input:
                console.print("❌ Please enter a value!", style="bold red")
                continue
                
            return input_type(user_input)
        except ValueError:
            console.print("❌ Invalid input! Please try again.", style="bold red")
        except KeyboardInterrupt:
            console.print("\n\n👋 Exiting...", style="bold yellow")
            exit()

def show_enhanced_playlist_analytics():
    """Display enhanced analytics in terminal"""
    console = Console()
    try:
        spotify = SpotifyAPI()
        custom_playlists = spotify.get_custom_playlists()
        
        if not custom_playlists:
            console.print("\n📭 No custom playlists found for analytics.", style="bold yellow")
            return
        
        console.print("\n📊 [bold cyan]Playlist Analytics Dashboard[/bold cyan]")
        
        # Get enhanced stats
        playlist_stats = spotify.get_user_playlist_stats(limit=10)
        
        if playlist_stats:
            # Display summary metrics
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Playlist Name", width=25)
            table.add_column("Tracks", width=8)
            table.add_column("Avg Popularity", width=15)
            table.add_column("Genres", width=30)
            table.add_column("Created", width=12)
            
            for stats in playlist_stats:
                table.add_row(
                    stats['playlist_name'],
                    str(stats['total_tracks']),
                    f"{stats['avg_popularity']:.1f}",
                    (stats['all_genres'][:27] + '...') if len(stats['all_genres']) > 30 else stats['all_genres'],
                    stats['created_at'].strftime('%Y-%m-%d')
                )
            
            console.print(table)
            
            # Option for detailed analysis
            console.print("\n🔍 Enter a playlist ID for detailed analysis, or press Enter to continue: ")
            try:
                playlist_id = input("Playlist ID: ").strip()
                if playlist_id:
                    playlist_id = int(playlist_id)
                    detailed = spotify.get_enhanced_playlist_analysis(playlist_id)
                    if detailed:
                        console.print(f"\n🎵 [bold]Detailed Analysis for {detailed['playlist_name']}[/bold]")
                        console.print(f"📝 Description: {detailed['description']}")
                        console.print(f"🎭 Mood: {detailed['mood_description']}")
                        console.print(f"🔢 Tracks: {detailed['total_tracks']}")
                        console.print(f"⭐ Popularity: {detailed['min_popularity']}-{detailed['max_popularity']} (avg: {detailed['avg_popularity']:.1f})")
                        console.print(f"🎶 Genres: {detailed['all_genres']}")
                        console.print(f"📅 Created: {detailed['created_at'].strftime('%Y-%m-%d %H:%M')}")
            except ValueError:
                console.print("❌ Invalid playlist ID!", style="bold red")
                
    except Exception as e:
        console.print(f"❌ Error loading analytics: {e}", style="bold red")
    finally:
        try:
            spotify.close()
        except:
            pass

def main():
    # Initialize Spotify API handler
    console = Console()
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold cyan]🎵 Spotify Playlist Analyzer & AI Curator[/bold cyan]\n"
        "Create custom playlists using AI based on your mood and preferences!",
        border_style="green"
    ))
    
    try:
        spotify = SpotifyAPI()
        
        # Fetch and display user's playlists
        console.print("\n🎵 Fetching your playlists...", style="bold blue")
        playlists = spotify.get_user_playlists()
        
        if not playlists:
            console.print("❌ No playlists found!", style="bold red")
            console.print("💡 Make sure you have playlists in your Spotify account.", style="yellow")
            return
        
        # Display playlists
        display_playlists(playlists)
        
        # Get user selection
        console.print("\n🔢 [bold]Playlist Selection[/bold]")
        choice = get_user_input(
            f"Enter the number of the playlist to analyze (1-{len(playlists)})",
            input_type=int
        )
        
        if not 1 <= choice <= len(playlists):
            console.print("❌ Invalid playlist number!", style="bold red")
            return
        
        selected_playlist = playlists[choice - 1]
        console.print(f"\n✨ Selected: [bold]{selected_playlist['name']}[/bold]")
        
        # Get number of tracks to analyze
        console.print("\n📊 [bold]Track Analysis[/bold]")
        max_tracks = min(selected_playlist['tracks_total'], 100)  # Limit to 100 for performance
        limit = get_user_input(
            f"How many tracks to analyze (1-{max_tracks})",
            default=min(20, max_tracks),
            input_type=int
        )
        
        if not 1 <= limit <= max_tracks:
            console.print("❌ Invalid number of tracks!", style="bold red")
            return
        
        # Fetch and store tracks from playlist
        console.print(f"\n📥 Fetching {limit} tracks from the playlist...", style="bold blue")
        tracks_data = spotify.get_playlist_tracks(selected_playlist['id'], limit=limit)
        
        if not tracks_data:
            console.print("❌ Failed to fetch tracks from the playlist!", style="bold red")
            return
            
        console.print(f"✅ Successfully fetched and stored {len(tracks_data)} tracks!", style="bold green")
        
        # Show sample of fetched tracks
        console.print("\n📝 Sample of fetched tracks:", style="bold blue")
        sample_table = Table(show_header=True, header_style="bold yellow")
        sample_table.add_column("Track", width=30)
        sample_table.add_column("Artist", width=20)
        sample_table.add_column("Genres", width=25)
        
        for track in tracks_data[:3]:  # Show first 3 tracks as sample
            genres = ', '.join(track.get('artist_genres', [])[:2])  # Show first 2 genres
            sample_table.add_row(
                track['track_name'][:27] + '...' if len(track['track_name']) > 30 else track['track_name'],
                track['artist'][:17] + '...' if len(track['artist']) > 20 else track['artist'],
                genres[:22] + '...' if len(genres) > 25 else genres or "No genres"
            )
        console.print(sample_table)
        
        # Get mood description for custom playlist
        console.print("\n🎭 [bold]Custom Playlist Creation[/bold]")
        console.print("💡 Describe the mood, theme, or vibe you want for your new playlist")
        console.print("   Examples: 'chill study music', 'energetic workout', 'romantic evening', 'focus coding'")
        
        mood_description = get_user_input(
            "Describe the mood/theme for your custom playlist",
            default="chill vibes"
        )
        
        playlist_name = get_user_input(
            "Enter a name for your custom playlist",
            default=f"{mood_description.title()} Mix"
        )
        
        # Test Gemini connection
        ai_working, llm_handler = test_gemini_connection()
        
        if not ai_working:
            console.print("\n⚠️ [bold yellow]AI features unavailable. Using fallback mode...[/bold yellow]")
            console.print("💡 The playlist will be created with basic matching.", style="yellow")
            
            # Create fallback playlist
            from llm_handler import LLMHandler  # Import here to avoid circular issues
            llm_handler = LLMHandler()
            console.print("\n🎨 Generating your custom playlist (fallback mode)...", style="bold blue")
            
        else:
            console.print("\n🎨 Generating your custom playlist with AI...", style="bold blue")
        
        # Generate custom playlist
        try:
            custom_playlist = llm_handler.analyze_tracks_and_create_playlist(
                tracks_data=tracks_data,
                mood_description=mood_description,
                playlist_name=playlist_name,
                max_tracks=min(10, len(tracks_data))
            )
            
            # Store custom playlist in database
            console.print("\n💾 Saving custom playlist to database...", style="bold blue")
            spotify.store_custom_playlist(custom_playlist, mood_description)
            
            # Display the custom playlist
            display_custom_playlist(custom_playlist)
            
            # Success message
            console.print(f"\n🎉 [bold green]Custom playlist '{custom_playlist['playlist_name']}' created successfully![/bold green]")
            
            # Additional options
            console.print("\n🔧 [bold]Next Steps:[/bold]")
            console.print("   • Run the program again to create more playlists")
            console.print("   • Check your database for stored playlists")
            console.print("   • Share your feedback!")
            
        except Exception as e:
            console.print(f"\n❌ Error generating playlist: {e}", style="bold red")
            console.print("💡 Try again with a different mood description or more tracks.", style="yellow")
            
    except KeyboardInterrupt:
        console.print("\n\n👋 Exiting... Thank you for using Spotify Playlist Analyzer!", style="bold yellow")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="bold red")
        console.print("💡 Check your internet connection and API keys.", style="yellow")
    
    finally:
        try:
            spotify.close()
        except:
            pass

def show_custom_playlists():
    """Display previously created custom playlists"""
    console = Console()
    try:
        spotify = SpotifyAPI()
        custom_playlists = spotify.get_custom_playlists()
        
        if not custom_playlists:
            console.print("\n📭 No custom playlists found in database.", style="bold yellow")
            return
        
        console.print("\n📂 [bold]Previously Created Custom Playlists:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Playlist Name", width=25)
        table.add_column("Description", width=40)
        table.add_column("Created", width=15)
        
        for playlist in custom_playlists:
            created = playlist['created_at'].strftime('%Y-%m-%d') if playlist['created_at'] else 'Unknown'
            table.add_row(
                str(playlist['id']),
                playlist['playlist_name'],
                playlist['description'][:37] + '...' if len(playlist['description']) > 40 else playlist['description'],
                created
            )
        
        console.print(table)
        
        # Option to view tracks of a specific playlist
        if custom_playlists:
            console.print("\n🔍 Enter a playlist ID to view its tracks, or press Enter to continue: ")
            try:
                playlist_id = input("Playlist ID: ").strip()
                if playlist_id:
                    playlist_id = int(playlist_id)
                    tracks = spotify.get_custom_playlist_tracks(playlist_id)
                    if tracks:
                        console.print(f"\n🎵 Tracks in playlist #{playlist_id}:")
                        track_table = Table(show_header=True, header_style="bold green")
                        track_table.add_column("#", style="dim", width=4)
                        track_table.add_column("Track Name", width=30)
                        track_table.add_column("Artist", width=20)
                        track_table.add_column("Album", width=25)
                        
                        for track in tracks:
                            track_table.add_row(
                                str(track['position']),
                                track['track_name'],
                                track['artist'],
                                track['album']
                            )
                        console.print(track_table)
            except ValueError:
                console.print("❌ Invalid playlist ID!", style="bold red")
            except Exception as e:
                console.print(f"❌ Error viewing playlist: {e}", style="bold red")
                
    except Exception as e:
        console.print(f"❌ Error loading custom playlists: {e}", style="bold red")
    finally:
        try:
            spotify.close()
        except:
            pass

if __name__ == "__main__":
    console = Console()
    
    while True:
        console.print(Panel.fit(
            "[bold cyan]🎵 Spotify Playlist Analyzer & AI Curator[/bold cyan]\n"
            "Create amazing playlists with AI magic!",
            border_style="green"
        ))
        
        console.print("\n📋 [bold]Main Menu:[/bold]")
        console.print("   1. 🎨 Create New Custom Playlist")
        console.print("   2. 📂 View Previously Created Playlists") 
        console.print("   3. 📊 Playlist Analytics Dashboard")
        console.print("   4. 🚪 Exit")
        
        choice = get_user_input("Select an option (1-4)", default="1", input_type=str)
        
        if choice == "1":
            main()
        elif choice == "2":
            show_custom_playlists()
        elif choice == "3":
            show_enhanced_playlist_analytics()
        elif choice == "4":
            console.print("\n👋 Thank you for using Spotify Playlist Analyzer! Goodbye! 🎵", style="bold green")
            break
        else:
            console.print("❌ Invalid option! Please select 1, 2, 3, or 4.", style="bold red")
        
        # Ask if user wants to continue
        if choice in ["1", "2", "3"]:
            console.print("\n" + "="*50)
            continue_choice = input("\nWould you like to continue? (y/n, default: y): ").strip().lower()
            if continue_choice in ['n', 'no']:
                console.print("\n👋 Thank you for using Spotify Playlist Analyzer! Goodbye! 🎵", style="bold green")
                break
            console.print("\n" + "="*50)