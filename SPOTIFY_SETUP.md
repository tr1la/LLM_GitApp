# Spotify Integration Setup Guide

## Problem: "No sound when clicking play button"

The most common reason for this is an **expired or invalid Spotify access token**. Spotify tokens expire after ~1 hour of inactivity.

## Solution: Get a Fresh Spotify Access Token

### Method 1: In-App Authentication (Recommended)
The easiest way to authenticate is through the app itself:

1. Click the **⚙️ Settings** button in the app
2. Scroll to "Spotify Integration" section
3. Click **"Connect Spotify Account"**
4. Authorize the application in the Spotify popup
5. You're now ready to use Spotify features!

### Method 2: Generate Token via CLI
If the in-app authentication doesn't work, you can use the CLI script:

1. Make sure you have your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

2. From the `frontend` directory, run:

```bash
npm run spotify:token
```

3. This will:
   - Start a local auth server on port 8888
   - Open your browser to Spotify authorization
   - Display the access token in terminal
   - Save it to `.env`

4. Copy the token and update `VITE_SPOTIFY_ACCESS_TOKEN` in `.env`

### Method 3: Manual Token Generation
If the above methods don't work, you can manually generate a token:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

2. Create an app (or use existing one):
   - Click "Create an App"
   - Accept terms and create
   - Copy your **Client ID** and **Client Secret**

3. Set redirect URI in app settings:
   - Add `http://127.0.0.1:3000/spotify-callback` for in-app authentication
   - Add `http://127.0.0.1:8888/callback` for CLI script authentication

4. Construct authorization URL:

```
https://accounts.spotify.com/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://127.0.0.1:3000/spotify-callback&scope=streaming%20user-read-email%20user-read-private%20user-modify-playback-state%20user-read-playback-state%20user-read-currently-playing%20app-remote-control
```

5. Open in browser, authorize, and grab the code from redirect

6. Exchange code for token using curl:

```bash
curl -X POST https://accounts.spotify.com/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=CODE_FROM_STEP_5&redirect_uri=http://127.0.0.1:3000/spotify-callback&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

7. Copy the `access_token` from response and add to `.env`:

```env
VITE_SPOTIFY_ACCESS_TOKEN=BQxxxxxxxxxx...
```

## Requirements for Playback

Before testing playback, ensure:

✅ **Spotify Premium Account** - Playback requires Premium
✅ **Active Spotify Device** - Open Spotify app on phone, desktop, or web player
✅ **Valid Access Token** - Not expired (< 1 hour old)
✅ **Internet Connection** - For both app and Spotify
✅ **Microphone & Speakers** - For voice detection and audio playback

## Testing Playback

1. **Detect a Song:**
   - Click "Music" in the feature menu
   - Click "Detect Music" button
   - Sing or play audio for 10 seconds
   - Wait for song recognition

2. **Play the Song:**
   - Once detected, click the **Play** button
   - Make sure Spotify is open on another device
   - You should hear music playing there

## Troubleshooting

### "No active Spotify devices found"
- Open Spotify app on any device (phone, desktop, web)
- Make sure Spotify is actively logged in
- Check you're using the same Spotify account as the token

### "Token expired"
- Get a fresh token using one of the methods above
- Paste in Settings modal
- Retry playback

### "No sound despite playing"
- Check volume on your Spotify device
- Verify Spotify app has audio output enabled
- Try playing a song directly in Spotify app first

### "403 Forbidden" or "401 Unauthorized"
- Token is invalid or expired
- Refresh token from Spotify Developer Dashboard
- Ensure `VITE_SPOTIFY_ACCESS_TOKEN` starts with "BQ"

## Token Persistence

Tokens are stored in:
- `.env` file (persistent across restarts)
- Browser localStorage (session-based, persists until clearing cache)

## Quick Reference

| Issue | Solution |
|-------|----------|
| No playback sound | Get fresh access token |
| "No devices found" | Open Spotify app on any device |
| Token rejected | Verify token format (should start with "BQ") |
| Playback stops after 1 hour | Refresh token when requested |
| Song not detected | Ensure audio input and 10+ seconds of sound |

## API Endpoints Used

- `GET /v1/me/player/devices` - List available devices
- `PUT /v1/me/player/play` - Start playback
- `PUT /v1/me/player/pause` - Pause playback
- `POST /v1/me/player/next` - Skip to next track
- `POST /v1/me/player/previous` - Skip to previous track
- `GET /v1/me/player/currently-playing` - Get current track

All require valid Bearer token with `user-modify-playback-state` scope.