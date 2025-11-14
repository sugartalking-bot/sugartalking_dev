# Plex + HEOS Integration Feature - Design Planning Prompt

## Context for Claude Sonnet 4.5

You are an expert Python/Flask developer. I need to plan and design a new feature 
for the SugarTalking project that integrates Plex music library with Denon AVR 
receiver music playback capabilities via HEOS.

---

## Current Project Context

### Project Overview
- **Name**: SugarTalking
- **Type**: Flask-based web application for controlling a Denon AVR-X2300W receiver
- **Current Architecture**:
  - `app/routes/` - API endpoints (admin.py, api.py, web.py)
  - `app/services/` - Business logic (command_executor.py, discovery.py, error_reporter.py, receiver_status.py)
  - `app/models.py` - Database models
  - `static/` - Web UI (index.html, denon-control.js)
  - `lib/` - Command libraries (change_input.py, get_status.py, mute_toggle.py, set_volume.py, volume_up_down.py)

### Current Receiver Control
- **Protocol**: Telnet (Port 23)
- **Capabilities**: Volume, input selection, power control, mute
- **Integration Method**: Direct telnet commands to receiver IP

### Database/Configuration
- Uses SQLAlchemy ORM for models
- Configuration managed through app settings
- Error handling via dedicated error_reporter service

---

## Feature Requirements

### User Goals
1. Browse and search Plex music library from web UI
2. Select tracks, albums, or artists from Plex catalog
3. Send playback commands to receiver via HEOS
4. Control playback (play, pause, next, previous, volume) through web UI
5. Display currently playing track information in real-time
6. Manage Plex and HEOS configuration (server IP, auth tokens)

### Functional Requirements
- Search Plex music library by artist, album, track
- Display search results with metadata (artist, album, duration, artwork)
- Queue management (play now, add to queue)
- Transport controls (play/pause/stop/next/previous)
- Volume control synchronized with receiver
- Now playing display with track metadata
- Connection status indicators
- Configuration UI for Plex server and HEOS device settings

---

## Available Libraries & APIs - Detailed Analysis

### HEOS API (Denon's Music Control Protocol)

#### Library Information
- **Package Name**: `pyheos`
- **Latest Version**: 1.0.6 (as of October 2025)
- **Language**: Python with async/await support
- **Connection Protocol**: Telnet-based CLI (Port 1255)
- **Last Updated**: Last week (actively maintained)
- **GitHub**: https://github.com/andrewsayre/pyheos
- **Documentation**: https://github.com/andrewsayre/pyheos (README)

#### Architecture
- **Connection**: Single TCP connection manages all HEOS devices on network
- **Communication**: Event-based messaging with JSON responses
- **Auto-Discovery**: Automatic device discovery available
- **Reconnection**: Built-in auto-reconnect with configurable delays
- **Device Management**: Support for multiple players, failover options

#### Key Features & Capabilities

**Device Discovery & Connection**:
```python
from pyheos import Heos
from pyheos import HeosOptions

# Auto-discover and connect
heos = await Heos.create_and_connect('192.168.1.100', auto_reconnect=True)

# Get all players
players = await heos.get_players(refresh=True)

# Connect to specific player
player = players[player_id]
```

**HeosOptions Configuration**:
- `host` - IP address or hostname of HEOS device (required)
- `timeout` - Connection timeout in seconds (default: 15.0)
- `heart_beat` - Enable/disable heart beat (default: True)
- `heart_beat_interval` - Interval between beats (default: 10.0)
- `events` - Enable event updates (default: True)
- `all_progress_events` - Receive progress events (default: True)
- `auto_reconnect` - Auto-reconnect on failure (default: False)
- `auto_reconnect_delay` - Delay before reconnect (default: 1.0)
- `auto_reconnect_max_attempts` - Max reconnection attempts (default: 0 = unlimited)
- `auto_failover` - Failover to other hosts (default: False)
- `auto_failover_hosts` - List of backup hosts

**Playback Control Commands**:
- `player/play` - Start playback
- `player/pause` - Pause playback
- `player/stop` - Stop playback
- `player/play_next` - Skip to next track
- `player/play_previous` - Skip to previous track
- `player/set_play_state` - Set play state (play/pause/stop)

**Volume Control**:
- `player/set_volume` - Set volume level (0-100)
- `player/get_volume` - Get current volume
- `player/volume_up` - Increase volume
- `player/volume_down` - Decrease volume
- `player/set_mute` - Mute/unmute

**Media Information**:
- `player/get_now_playing_media` - Get current track information
- `player/get_player_info` - Get player details
- Returns: Track title, artist, album, duration, artwork URL

**Event Subscriptions**:
- `player_now_playing_changed` - Track changed
- `player_volume_changed` - Volume changed
- `player_playback_state_changed` - Play state changed
- Real-time event notifications for UI updates

#### Connection Lifecycle
```python
# Create connection
heos = await Heos.create_and_connect('192.168.1.100')

# Subscribe to events
heos.dispatcher.register_callback(
    callback=on_event,
    signal=pyheos.signals.signal_player_now_playing_changed
)

# Execute commands
players = await heos.get_players()
player = players[1]
await player.play()

# Disconnect
await heos.disconnect()
```

#### Error Handling
- Connection failures with auto-retry
- Timeout management
- Device offline scenarios
- Event dispatch failures

---

### Plex API (Music Library Management)

#### Library Information
- **Package Name**: `python-plexapi`
- **Latest Version**: 4.17.1 (as of August 2025)
- **Language**: Python (synchronous - not async)
- **Repository**: https://github.com/pushingkarmaorg/python-plexapi
- **Documentation**: http://python-plexapi.readthedocs.io/en/latest/
- **Contributors**: 96 active contributors
- **Stars**: 1.2k on GitHub
- **Last Updated**: 2 weeks ago

#### Authentication Methods

**Method 1: Direct Token Authentication** (Recommended for local network)
```python
from plexapi.server import PlexServer

baseurl = 'http://192.168.1.50:32400'
token = 'your_plex_auth_token'
plex = PlexServer(baseurl, token)
```

**Method 2: MyPlex Account** (For remote access)
```python
from plexapi.myplex import MyPlexAccount

account = MyPlexAccount('username', 'password')
plex = account.resource('SERVER_NAME').connect()
```

**Finding Your Token**:
- Log into Plex Web at http://your-plex-server:32400
- Open browser dev console (F12)
- Look for network request, find auth token in headers/cookies
- Or: Check Plex settings → Users & Sharing → Tokens

#### Music Library Access

**Access Music Section**:
```python
# Get music library section
music = plex.library.section('Music')

# List all artists
for artist in music.all():
    print(f"Artist: {artist.title}")
```

**Search Functionality**:
```python
# Search across all music
results = music.search('Beatles')

# Search specific types
artists = music.search('Beatles', libtype='artist')
albums = music.search('Abbey Road', libtype='album')
tracks = music.search('Here Comes the Sun', libtype='track')
```

**Hierarchical Browsing**:
```python
# Get specific artist
artist = music.get('The Beatles')

# Get albums by artist
for album in artist.albums():
    print(f"Album: {album.title}")
    
    # Get tracks in album
    for track in album.tracks():
        print(f"  Track: {track.title}")
        print(f"  Duration: {track.duration}ms")
        print(f"  Rating: {track.rating}")
```

**Advanced Filtering**:
```python
# Filter by multiple criteria
results = music.search(
    title='track_name',
    artist='artist_name',
    album='album_name'
)

# Search with operators
unwatched = music.search(unwatched=True)
rated = music.search(rating='>8.0')
```

#### Playlist Management

```python
# List all playlists
for playlist in plex.playlists():
    print(f"Playlist: {playlist.title}")

# Get items in playlist
for item in playlist.items():
    print(f"Item: {item.title}")

# Create new playlist
new_playlist = plex.createPlaylist('My Playlist', items=[track1, track2])

# Add items to playlist
playlist.addItems(track)
```

#### Metadata Access

**Track Information**:
- `track.title` - Track name
- `track.artist().title` - Artist name
- `track.album().title` - Album name
- `track.duration` - Duration in milliseconds
- `track.rating` - Rating (0-10)
- `track.index` - Track number
- `track.year` - Release year
- `track.media` - Media file information

**Album Information**:
- `album.title` - Album title
- `album.artist().title` - Artist name
- `album.year` - Release year
- `album.rating` - Average rating
- `album.thumbUrl` - Album artwork URL
- `album.tracks()` - List of tracks

**Artist Information**:
- `artist.title` - Artist name
- `artist.albums()` - Albums by artist
- `artist.tracks()` - All tracks by artist
- `artist.rating` - Artist rating

#### Available Clients

```python
# List all available clients (playback devices)
for client in plex.clients():
    print(f"Client: {client.title}")
    print(f"Address: {client.baseurl}")

# Get specific client
client = plex.client('Client Name')
```

#### Playback Control

```python
# Get client for playback
client = plex.client('Receiver or Speaker Name')

# Play media
client.playMedia(track)
client.playMedia(album)
client.playMedia(playlist)

# Transport controls
client.play()              # Resume playback
client.pause()             # Pause
client.stop()              # Stop
client.skipNext()          # Next track
client.skipPrevious()      # Previous track

# Volume control
client.setVolume(50)       # Set volume 0-100
current_volume = client.getVolume()

# Seek
client.seekTo(30000)       # Seek to milliseconds

# Get playback status
state = client.getPlayState()
now_playing = client.now_playing
```

#### Library Actions

```python
# Scan library
music.scan()

# Analyze library
music.analyze()

# Empty trash
music.emptyTrash()

# Refresh section
music.refresh()
```

---

## Data Flow Architecture

### Plex → SugarTalking → HEOS Flow

```
User UI Request
    ↓
Flask API Endpoint
    ↓
Plex Service (search/browse music)
    ↓
Plex API Response (track/album/artist data)
    ↓
Format & Return to UI
    ↓
User Selects Track
    ↓
Playback Request
    ↓
HEOS Controller Service
    ↓
pyheos Library
    ↓
HEOS Device (AVR-X2300W)
    ↓
Receiver Playback
    ↓
WebSocket/Event Update
    ↓
UI Updates (now playing, controls)
```

### Event Flow

```
User Action (pause, volume change, etc)
    ↓
Browser sends request to Flask API
    ↓
HEOS Service executes command
    ↓
Command sent to receiver via pyheos
    ↓
Receiver acknowledges
    ↓
HEOS events triggered
    ↓
Event dispatcher notifies listeners
    ↓
WebSocket broadcasts to UI
    ↓
UI updates in real-time
```

---

## Current Project Structure Reference

```
sugartalking/
├── app/
│   ├── __init__.py
│   ├── models.py                    # Database models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py                 # Admin routes
│   │   ├── api.py                   # API endpoints (primary)
│   │   └── web.py                   # Web routes
│   └── services/
│       ├── __init__.py
│       ├── command_executor.py      # Execute receiver commands
│       ├── discovery.py             # Device discovery
│       ├── error_reporter.py        # Error handling
│       └── receiver_status.py       # Status monitoring
├── lib/
│   ├── __init__.py
│   ├── change_input.py
│   ├── get_status.py
│   ├── mute_toggle.py
│   ├── set_volume.py
│   └── volume_up_down.py
├── static/
│   ├── index.html
│   └── denon-control.js
├── wsgi.py
├── requirements.txt
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## Integration Points

### Existing Services to Consider
- `command_executor.py` - Execute receiver commands (pattern to follow)
- `error_reporter.py` - Error handling pattern
- `receiver_status.py` - Status monitoring pattern
- `discovery.py` - Device discovery pattern

### Existing Routes to Extend
- `app/routes/api.py` - Add new Plex + HEOS endpoints here
- `app/routes/admin.py` - Configuration management

### Existing Libraries Pattern
- `lib/` directory structure (simple, focused command modules)

---

## Key Constraints & Considerations

### Technical Constraints
- Flask (synchronous framework) + pyheos (async library) → Need adapter/wrapper
- Plex API is synchronous, HEOS is async → Different execution models
- Single HEOS connection for all operations → Connection pooling needed
- Plex auth token management → Secure storage required

### Network Constraints
- Both Plex and HEOS need network accessibility
- Plex: Port 32400 (default)
- HEOS: Port 1255 (default)
- May need configuration for different network scenarios

### Performance Considerations
- Large music libraries (10,000+ tracks) → Pagination/caching needed
- Real-time updates → WebSocket vs polling trade-off
- Search performance → Index optimization
- Connection stability → Reconnection retry strategy

### Security Considerations
- Plex auth tokens → Secure storage (environment variables or encrypted DB)
- HEOS IP/port configuration → Secure storage
- API endpoint protection → Authentication/authorization
- User isolation if multi-user support planned

---

## Configuration Requirements

### Settings to Store
```python
# Plex Configuration
PLEX_SERVER_URL = 'http://192.168.1.50:32400'
PLEX_AUTH_TOKEN = 'xxxxx'
PLEX_LIBRARY_NAME = 'Music'

# HEOS Configuration
HEOS_DEVICE_IP = '192.168.1.100'
HEOS_DEVICE_PORT = 1255
HEOS_AUTO_DISCOVERY = True
HEOS_AUTO_RECONNECT = True
HEOS_RECONNECT_DELAY = 1.0
HEOS_PLAYER_ID = 1  # or auto-select

# UI Configuration
MUSIC_SEARCH_PAGE_SIZE = 50
CACHE_TTL = 300  # seconds
REAL_TIME_UPDATES = True  # WebSocket vs polling
```

### Configuration Storage Options
1. Environment variables (recommended for production)
2. Database model (ConfigurationSettings)
3. Configuration file (JSON/YAML)
4. Flask configuration object

---

## Your Task: Create Comprehensive Design Plan

Please analyze this information and provide a detailed design plan including:

### 1. Architecture Design (30% of response)
- Recommended service layer organization
- Separation of concerns between Plex and HEOS
- Adapter patterns for async/sync compatibility
- Data flow between components
- Configuration management approach
- How to integrate with existing codebase patterns

### 2. API Endpoint Design (25% of response)
- List all new RESTful endpoints needed
- For each endpoint:
  - URL path and method
  - Request parameters/body
  - Response format with examples
  - Error handling codes
  - Authentication requirements
- Suggest response structure for UI consumption

### 3. Database/Storage Design (15% of response)
- What data needs persistent storage
- Recommended SQLAlchemy models
- Caching strategy for Plex data
- Configuration storage approach
- Session management for connections

### 4. Web UI Integration Plan (15% of response)
- New UI components needed
- JavaScript module organization
- WebSocket vs polling recommendation
- Real-time update strategy
- UI state management approach

### 5. Implementation Roadmap (10% of response)
- Phase breakdown
- Dependencies between phases
- Estimated complexity per phase
- Testing strategy per phase

### 6. Potential Challenges & Solutions (5% of response)
- Identify 5-7 key technical challenges
- Propose solutions for each
- Highlight areas needing special attention

---

## Success Criteria

The design plan should be:
- ✅ Actionable - Can be directly used for implementation
- ✅ Detailed - Specific code examples and patterns
- ✅ Realistic - Considers async/sync integration challenges
- ✅ Aligned - Follows existing SugarTalking patterns
- ✅ Scalable - Can handle large music libraries
- ✅ Maintainable - Clear separation of concerns
- ✅ Robust - Considers error scenarios

---

## Additional Context for Claude

- **Project Language**: Python 3
- **Web Framework**: Flask
- **Database ORM**: SQLAlchemy
- **Frontend**: Vanilla JavaScript (not React/Vue)
- **Existing Patterns**: Command executor, service layer, error handling
- **Target Device**: Denon AVR-X2300W
- **Use Case**: Home media center with music streaming
- **Future Scope**: May add other music services (Spotify, Apple Music)

Please provide the comprehensive design plan now.
