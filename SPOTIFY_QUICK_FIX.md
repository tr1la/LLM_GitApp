# Quick Spotify Playback Fix

## The Problem
When you click the play button, nothing happens and there's no sound.

## Root Cause
**Your Spotify access token is expired or invalid.** Spotify tokens only last ~1 hour.

## The Solution (3 Steps)

### 1️⃣ Generate Fresh Token
```bash
cd frontend
npm run spotify:token
```

Follow the browser prompts to authorize with Spotify.

### 2️⃣ Copy Token
The terminal will show:
```
Access token: BQxxxxxxxxxxxxxxxxxxxxxxxxx
```
Copy this entire token.

### 3️⃣ Update Token in App
1. Click **⚙️ Settings** in the app
2. Find "Spotify Access Token" section
3. Paste the token in the text box
4. Click **Save Token**

## Test It
1. Go to **Music** feature
2. Click **Detect Music** (sing/play audio for 10 seconds)
3. Once a song is detected, click the **▶️ Play** button
4. Check Spotify on your phone/desktop - music should play there

## Requirements
✅ **Spotify Premium** (Free won't work)  
✅ **Spotify app open** on phone, desktop, or web  
✅ **Same Spotify account** for token and device  
✅ **Internet connection**  

## If It Still Doesn't Work
1. Make sure Spotify app is actively open
2. Try playing a song in Spotify app directly first
3. Get a brand new token (old ones expire)
4. Check browser console (F12) for error messages

## Support
See `SPOTIFY_SETUP.md` for detailed troubleshooting.
