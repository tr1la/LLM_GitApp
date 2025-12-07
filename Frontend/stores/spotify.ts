import { defineStore } from 'pinia';
import axios from 'axios';

interface SpotifyTrack {
    id: string;
    name: string;
    artists: { name: string }[];
    album: {
        name: string;
        images: { url: string }[];
        release_date?: string;
    };
    duration_ms: number;
    explicit: boolean;
    popularity?: number;
    uri: string;
}

export const useSpotifyStore = defineStore('spotify', {
    state: () => ({
        accessToken: import.meta.env.VITE_SPOTIFY_ACCESS_TOKEN || null,
        refreshToken: import.meta.env.VITE_SPOTIFY_REFRESH_TOKEN || null,
        currentTrack: null as SpotifyTrack | null,
        isPlaying: false,
        playbackPosition: 0,  // Added to track the current position in the track
        authError: null as string | null,
    }),

    actions: {
        // Start Spotify authentication flow
        async authenticate() {
            try {
                // Call our backend to get the Spotify auth URL
                const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/spotify/login`);
                const { auth_url } = response.data;
                
                // Redirect user to Spotify authorization page
                window.location.href = auth_url;
            } catch (error: any) {
                console.error("Error initiating Spotify auth:", error);
                this.authError = "Failed to initiate Spotify authentication";
            }
        },

        // Handle callback from Spotify with authorization code
        async handleCallback(code: string) {
            try {
                // Exchange authorization code for tokens
                const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/spotify/callback`, {
                    params: { code }
                });
                
                // The backend should return tokens in the response body, not as redirect parameters
                const { access_token, refresh_token } = response.data;
                
                // Store tokens
                this.accessToken = access_token;
                this.refreshToken = refresh_token;
                this.authError = null;
                
                // Save to localStorage for persistence
                if (typeof window !== 'undefined' && window.localStorage) {
                    localStorage.setItem('spotify_access_token', access_token);
                    localStorage.setItem('spotify_refresh_token', refresh_token);
                }
                
                return { success: true };
            } catch (error: any) {
                console.error("Error handling Spotify callback:", error);
                this.authError = "Failed to authenticate with Spotify";
                return { success: false, error: error.message };
            }
        },

        // Refresh access token using refresh token
        async refreshAccessToken() {
            if (!this.refreshToken) {
                this.authError = "No refresh token available";
                return { success: false, error: "No refresh token" };
            }

            try {
                const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/spotify/refresh`, {
                    refresh_token: this.refreshToken
                });
                
                const { access_token } = response.data;
                
                // Update access token
                this.accessToken = access_token;
                this.authError = null;
                
                // Save to localStorage
                if (typeof window !== 'undefined' && window.localStorage) {
                    localStorage.setItem('spotify_access_token', access_token);
                }
                
                return { success: true };
            } catch (error: any) {
                console.error("Error refreshing access token:", error);
                this.authError = "Failed to refresh Spotify token";
                return { success: false, error: error.message };
            }
        },

        // Debug: Check device availability
        async checkDevices() {
            if (!this.accessToken) {
                console.warn("No access token");
                return [];
            }

            try {
                const deviceRes = await axios.get('https://api.spotify.com/v1/me/player/devices', {
                    headers: { 'Authorization': `Bearer ${this.accessToken}` }
                });

                console.log("=== SPOTIFY DEVICES DEBUG ===");
                console.log("Total devices:", deviceRes.data.devices.length);
                console.log("Full devices list:", deviceRes.data.devices);
                deviceRes.data.devices.forEach((device: any, idx: number) => {
                    console.log(`Device ${idx}: ${device.name} (ID: ${device.id}) - Active: ${device.is_active}, Type: ${device.type}`);
                });
                console.log("==============================");

                return deviceRes.data.devices;
            } catch (error: any) {
                console.error("Error fetching devices:", error);
                return [];
            }
        },

        // Initialize Spotify by checking if we can access current playback
        async initSpotify() {
            // Try to load tokens from localStorage
            if (typeof window !== 'undefined' && window.localStorage) {
                const storedAccessToken = localStorage.getItem('spotify_access_token');
                const storedRefreshToken = localStorage.getItem('spotify_refresh_token');
                
                if (storedAccessToken) {
                    this.accessToken = storedAccessToken;
                }
                
                if (storedRefreshToken) {
                    this.refreshToken = storedRefreshToken;
                }
            }

            if (!this.accessToken) {
                this.authError = "No Spotify access token found. Please authenticate with Spotify.";
                console.warn(this.authError);
                return;
            }

            try {
                // Try to get current playback state to verify token is valid
                const response = await axios.get('https://api.spotify.com/v1/me/player/currently-playing', {
                    headers: { 'Authorization': `Bearer ${this.accessToken}` }
                });

                if (response.status === 401) {
                    // Token might be expired, try to refresh
                    const refreshResult = await this.refreshAccessToken();
                    if (!refreshResult.success) {
                        this.authError = "Spotify token expired and refresh failed.";
                    } else {
                        this.authError = null;
                        console.log("Spotify token refreshed successfully");
                    }
                } else {
                    this.authError = null;
                    console.log("Spotify initialized successfully");
                }
            } catch (error: any) {
                if (error.response?.status === 401) {
                    // Token might be expired, try to refresh
                    const refreshResult = await this.refreshAccessToken();
                    if (!refreshResult.success) {
                        this.authError = "Spotify authentication failed. Token may be expired.";
                    } else {
                        this.authError = null;
                        console.log("Spotify token refreshed successfully");
                    }
                } else {
                    this.authError = "Could not connect to Spotify API";
                }
                console.warn("Spotify init error:", error.response?.status, this.authError);
            }
        },

        // Update auth token
        setAccessToken(token: string) {
            this.accessToken = token;
            this.authError = null;
            
            // Save to localStorage
            if (typeof window !== 'undefined' && window.localStorage) {
                localStorage.setItem('spotify_access_token', token);
            }
        },
        async detectMusic() {
            this.isPlaying = false;
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                const chunks: Blob[] = [];

                const audioBlob: Blob = await new Promise((resolve, reject) => {
                    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);

                    mediaRecorder.onstop = () => {
                        const blob = new Blob(chunks, { type: 'audio/webm' });
                        resolve(blob);
                    };

                    mediaRecorder.onerror = reject;

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 10000); // 10 seconds
                });

                const file = new File([audioBlob], 'recording.webm');

                const formData = new FormData();
                formData.append("file", file);
                formData.append("return", "spotify");
                formData.append("api_token", import.meta.env.VITE_AUDD_API_KEY);

                const response = await fetch("https://api.audd.io/", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();
                console.log("Audd.io Response:", data);

                if (data?.result?.spotify?.uri) {
                    const track = {
                        id: data.result.spotify.id,
                        name: data.result.title,
                        artists: [{ name: data.result.artist }],
                        album: {
                            name: data.result.album,
                            images: [{ url: data.result.spotify.album?.images?.[0]?.url || '' }],
                            release_date: data.result.release_date || '',
                        },
                        duration_ms: data.result.spotify.duration_ms,
                        explicit: data.result.spotify.explicit || false,
                        popularity: data.result.spotify.popularity || 0,
                        uri: data.result.spotify.uri
                    };

                    this.currentTrack = track;
                    this.isPlaying = false;
                    this.playbackPosition = 0; // Reset position
                } else {
                    alert("Could not recognize any song.");
                }
            } catch (err) {
                console.error("Microphone error:", err);
            }
        },

        async playMusic() {
            if (!this.accessToken || !this.currentTrack) {
                this.authError = "Spotify not configured properly. Missing token or track.";
                console.error(this.authError);
                return;
            }

            try {
                const deviceRes = await axios.get('https://api.spotify.com/v1/me/player/devices', {
                    headers: { 'Authorization': `Bearer ${this.accessToken}` }
                });

                console.log("Available devices:", deviceRes.data.devices);

                // Try to find an active device first, then any device
                let device = deviceRes.data.devices.find((d: any) => d.is_active);
                
                // If no active device, just pick the first available one
                if (!device && deviceRes.data.devices.length > 0) {
                    device = deviceRes.data.devices[0];
                    console.log("No active device found, using first available:", device.name);
                }

                if (!device || deviceRes.data.devices.length === 0) {
                    this.authError = "No Spotify devices found. Make sure Spotify is open on your phone, desktop app, or browser tab and you're logged in.";
                    console.warn(this.authError);
                    console.warn("Devices response:", deviceRes.data);
                    alert(this.authError);
                    return;
                }

                console.log("Playing on device:", device.name, "ID:", device.id);

                const response = await axios.put(`https://api.spotify.com/v1/me/player/play?device_id=${device.id}`,
                    { uris: [this.currentTrack.uri] },
                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                );

                this.isPlaying = true;
                this.authError = null;
                console.log("Playback started on device:", device.name);
            } catch (error: any) {
                if (error.response?.status === 401) {
                    // Token might be expired, try to refresh
                    const refreshResult = await this.refreshAccessToken();
                    if (refreshResult.success) {
                        // Retry the play request with the new token
                        try {
                            const deviceRes = await axios.get('https://api.spotify.com/v1/me/player/devices', {
                                headers: { 'Authorization': `Bearer ${this.accessToken}` }
                            });
                            
                            let device = deviceRes.data.devices.find((d: any) => d.is_active) || deviceRes.data.devices[0];
                            
                            if (device) {
                                await axios.put(`https://api.spotify.com/v1/me/player/play?device_id=${device.id}`,
                                    { uris: [this.currentTrack!.uri] },
                                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                                );
                                
                                this.isPlaying = true;
                                this.authError = null;
                                console.log("Playback started successfully after token refresh");
                                return;
                            }
                        } catch (retryError: any) {
                            this.authError = "Error playing track even after token refresh: " + (retryError.response?.data?.error?.message || retryError.message);
                        }
                    } else {
                        this.authError = "Spotify token expired and refresh failed.";
                    }
                } else if (error.response?.status === 404) {
                    this.authError = "Device not found. Make sure Spotify app is running.";
                } else if (error.response?.status === 202 || error.response?.status === 204) {
                    // 202 or 204 is actually success - playback command accepted
                    this.isPlaying = true;
                    this.authError = null;
                    console.log("Playback started successfully");
                    return;
                } else {
                    this.authError = "Error playing track: " + (error.response?.data?.error?.message || error.message);
                }
                console.error(this.authError, error);
                alert(this.authError);
            }
        },

        async pauseMusic() {
            if (!this.accessToken) return;

            try {
                await axios.put('https://api.spotify.com/v1/me/player/pause', {},
                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                );
                this.isPlaying = false;
            } catch (error) {
                console.error("Error pausing music:", error);
            }
        },

        // New method to resume playback from the current position
        async resumePlayback() {
            if (!this.accessToken || !this.currentTrack || !this.playbackPosition) return;

            try {
                const deviceRes = await axios.get('https://api.spotify.com/v1/me/player/devices', {
                    headers: { 'Authorization': `Bearer ${this.accessToken}` }
                });

                const device = deviceRes.data.devices.find((d: any) => d.is_active) || deviceRes.data.devices[0];
                if (!device) {
                    alert("No active Spotify devices found. Please open Spotify.");
                    return;
                }

                await axios.put(`https://api.spotify.com/v1/me/player/play?device_id=${device.id}`,
                    {
                        uris: [this.currentTrack.uri],
                        position_ms: this.playbackPosition // Start from the current position
                    },
                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                );

                this.isPlaying = true;
            } catch (error) {
                console.error("Error resuming track:", error);
            }
        },

        async previousTrack() {
            if (!this.accessToken) return;

            try {
                await axios.post('https://api.spotify.com/v1/me/player/previous', {},
                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                );
            } catch (error) {
                console.error("Error skipping to previous track:", error);
            }
        },

        async nextTrack() {
            if (!this.accessToken) return;

            try {
                await axios.post('https://api.spotify.com/v1/me/player/next', {},
                    { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
                );
            } catch (error) {
                console.error("Error skipping to next track:", error);
            }
        }
    }
});
