# Spotify Authorization Code Flow Implementation

This document explains how the new Spotify Authorization Code Flow has been implemented in the application.

## Overview

The application now uses the proper Spotify Authorization Code Flow for authentication, which provides a better user experience by:

1. Automatically handling token refresh
2. Providing a seamless authentication experience
3. Storing tokens securely in localStorage
4. Handling token expiration gracefully

## Architecture

The authentication flow involves three components:
1. **Frontend** (port 3000) - Vue/Nuxt application
2. **Backend** (port 8000) - FastAPI server
3. **Spotify** - Spotify's OAuth service

Flow:
1. User clicks "Connect Spotify Account" in the frontend
2. Frontend calls backend `/spotify/login` endpoint
3. Backend generates Spotify authorization URL and returns it
4. Frontend redirects user to Spotify authorization page
5. User authorizes the application
6. Spotify redirects back to the frontend callback page (`http://localhost:3000/spotify-callback`)
7. Frontend callback page calls backend `/spotify/callback` endpoint with the authorization code
8. Backend exchanges code for access and refresh tokens
9. Backend returns tokens to frontend callback page
10. Frontend stores tokens in localStorage and Pinia store
11. Application is now ready to use Spotify features

## Backend Implementation

The backend (ML Service) now includes three new endpoints:

### 1. `/spotify/login` (GET)
- Generates the Spotify authorization URL
- Uses the redirect URI `http://localhost:3000/spotify-callback`
- Returns the authorization URL to the frontend

### 2. `/spotify/callback` (GET)
- Handles the callback from the frontend with the authorization code
- Exchanges the authorization code for access and refresh tokens
- Returns tokens to the frontend callback page

### 3. `/spotify/refresh` (POST)
- Refreshes expired access tokens using the refresh token
- Returns a new access token

## Frontend Implementation

### Spotify Store (`stores/spotify.ts`)
The Pinia store has been enhanced with:

1. **authenticate()** - Initiates the Spotify authentication flow
2. **handleCallback()** - Processes the callback from Spotify
3. **refreshAccessToken()** - Refreshes expired tokens automatically
4. **Automatic token persistence** - Tokens are stored in localStorage
5. **Automatic token loading** - Tokens are loaded from localStorage on app start
6. **Enhanced error handling** - Better error messages and recovery

### Spotify Callback Page (`pages/spotify-callback.vue`)
Handles the redirect from Spotify and processes the authentication tokens:

1. Receives the authorization code from Spotify
2. Calls the backend `/spotify/callback` endpoint
3. Receives tokens from the backend
4. Stores tokens in localStorage and Pinia store
5. Displays success/error messages

### Spotify Feature Component (`components/features/SpotifyFeature.vue`)
- Added authentication UI when not connected
- Shows account status and errors
- Provides authentication button

### Settings Modal (`components/modals/SettingsModal.vue`)
- Simplified to only show connection/disconnection options
- Removed manual token entry
- Shows account connection status

## How It Works

1. User clicks "Connect Spotify Account" in either the Spotify feature or Settings modal
2. Frontend calls backend `/spotify/login` endpoint
3. Backend generates Spotify authorization URL and returns it
4. Frontend redirects user to Spotify authorization page
5. User authorizes the application
6. Spotify redirects back to the frontend callback page (`http://localhost:3000/spotify-callback`)
7. Frontend callback page calls backend `/spotify/callback` endpoint with the authorization code
8. Backend exchanges code for access and refresh tokens
9. Backend returns tokens to frontend callback page
10. Frontend stores tokens in localStorage and Pinia store
11. Application is now ready to use Spotify features

## Token Management

Tokens are automatically managed:

- **Storage**: Tokens are stored in localStorage for persistence
- **Loading**: Tokens are automatically loaded on app initialization
- **Refreshing**: Expired access tokens are automatically refreshed
- **Error Handling**: Token errors are displayed to the user with recovery options

## Fallback Options

The CLI script (`spotify_token_cli.js`) is still available as a fallback:

```bash
npm run spotify:token
```

This script:
1. Starts a local server on port 8888
2. Opens the Spotify authorization page
3. Receives the callback directly
4. Saves tokens to the [.env](file:///Users/tr1la/Documents/LLMProj/LLM_application/frontend/.env) file

## Required Environment Variables

The following environment variables must be set in the ML service [.env](file:///Users/tr1la/Documents/LLMProj/LLM_application/ml_service/.env) file:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/spotify-callback
```

And in the frontend [.env](file:///Users/tr1la/Documents/LLMProj/LLM_application/frontend/.env) file:

```env
VITE_BACKEND_URL=http://127.0.0.1:8000
```

## Security Considerations

1. Client secret is kept secure on the backend
2. Tokens are stored in localStorage (standard practice for SPAs)
3. Authorization code flow is used (more secure than implicit flow)
4. Proper error handling prevents token leakage

## Troubleshooting

If you encounter issues:

1. Ensure all environment variables are set correctly
2. Check that the Spotify app is configured with the correct redirect URI (`http://localhost:3000/spotify-callback`)
3. Verify that both frontend and backend servers are running
4. Clear localStorage if tokens become corrupted
5. Use the CLI script as a fallback authentication method