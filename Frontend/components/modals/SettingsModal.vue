<template>
    <div v-if="show" class="modal modal-open">
      <div class="modal-box max-w-2xl">
        <h3 class="text-lg font-bold mb-4">Settings</h3>
        
        <!-- Spotify Token Configuration -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 class="font-semibold mb-2 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="mr-2 text-green-600" viewBox="0 0 16 16">
              <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm3.669 11.538a.498.498 0 0 1-.686.165c-1.879-1.147-4.243-1.408-7.028-.772.342.59.966.957 1.466.957.591 0 1.081-.194 1.081-.694a.542.542 0 0 0-.854-.54 2.017 2.017 0 0 1-.62-.092c-.76-.172-1.193-.54-1.193-1.077 0-.538.43-.906 1.19-1.078.57-.13 1.326.09 1.326.09.206-.305-.2-.71-.556-.71a1.15 1.15 0 0 0-.58.151c-.456.253-1.338.25-1.338-1.082 0-.77.537-1.427 1.4-1.427.45 0 .926.163 1.346.495.44-.312.856-.595 1.436-.595 1.08 0 2.03.606 2.03 1.586 0 .882-.668 1.666-2.192 2.431-.12.065-.243.13-.358.21a.5.5 0 1 0 .575.866c.128-.087.255-.177.375-.255 1.74-1.132 2.323-2.269 2.323-3.812 0-2.39-1.883-4.471-4.744-4.471-1.997 0-3.846 1.087-4.558 2.614-.2.37-.35.771-.443 1.159-.394.529-.976.875-1.652.875-.735 0-1.332-.597-1.332-1.333 0-.735.597-1.332 1.332-1.332.41 0 .783.184 1.036.477-.09-.63.207-1.231.65-1.629C5.853 1.635 6.878 1 7.978 1c1.55 0 2.873.822 3.559 2.037zm0-7.686a.498.498 0 0 0 .286-.9c-1.514-1.172-3.666-1.605-5.813-.93a.5.5 0 0 0 .286.902c1.857-.504 3.73-.145 5.041.958z"/>
            </svg>
            Spotify Integration
          </h4>
          <p class="text-sm text-gray-600 mb-3">
            Connect your Spotify account to play music. The app will automatically refresh tokens when needed.
          </p>
          
          <div class="form-control mb-3">
            <label class="label">
              <span class="label-text text-sm">Account Status:</span>
            </label>
            <div class="text-sm p-2 rounded" :class="spotifyStore.authError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
              <span v-if="spotifyStore.accessToken && !spotifyStore.authError">✓ Connected to Spotify</span>
              <span v-else-if="spotifyStore.authError">{{ spotifyStore.authError }}</span>
              <span v-else>Not connected</span>
            </div>
          </div>

          <div class="flex gap-2">
            <button 
              v-if="!spotifyStore.accessToken || spotifyStore.authError"
              @click="authenticateWithSpotify" 
              class="btn btn-sm btn-success text-white"
            >
              Connect Spotify Account
            </button>
            <button 
              v-else
              @click="disconnectSpotify"
              class="btn btn-sm btn-outline"
            >
              Disconnect Account
            </button>
          </div>
        </div>

        <!-- Troubleshooting -->
        <div class="mb-6 p-4 bg-blue-50 rounded-lg">
          <h4 class="font-semibold mb-2">Troubleshooting</h4>
          <ul class="text-sm space-y-1 list-disc list-inside text-gray-700">
            <li>Make sure Spotify app is open on a device</li>
            <li>Check that Spotify token is valid and not expired</li>
            <li>Ensure you have an active Spotify Premium account</li>
            <li>Try detecting a song first, then playing</li>
          </ul>
        </div>
        
        <div class="modal-action">
          <button class="btn" @click="$emit('close')">Close</button>
        </div>
      </div>
      <div class="modal-backdrop" @click="$emit('close')"></div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import { useSpotifyStore } from '@/stores/spotify';

  const spotifyStore = useSpotifyStore();

  defineProps({
    show: {
      type: Boolean,
      default: false
    }
  });
  
  defineEmits(['close']);

  const authenticateWithSpotify = async () => {
    try {
      await spotifyStore.authenticate();
    } catch (error) {
      console.error('Spotify authentication failed:', error);
    }
  };

  const disconnectSpotify = () => {
    // Clear tokens from store and localStorage
    spotifyStore.accessToken = null;
    spotifyStore.refreshToken = null;
    spotifyStore.authError = "Not connected to Spotify";
    
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.removeItem('spotify_access_token');
      localStorage.removeItem('spotify_refresh_token');
    }
  };
  </script>