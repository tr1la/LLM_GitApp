<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h1 class="text-2xl font-bold text-center mb-6">Spotify Authentication</h1>
      
      <div v-if="loading" class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p class="mt-4">Completing Spotify authentication...</p>
      </div>
      
      <div v-else-if="success" class="text-center">
        <div class="text-green-500 text-5xl mb-4">✓</div>
        <p class="text-lg mb-4">Successfully authenticated with Spotify!</p>
        <p class="text-gray-600 mb-6">You can now close this window and return to the app.</p>
        <button @click="goToApp" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
          Return to App
        </button>
      </div>
      
      <div v-else class="text-center">
        <div class="text-red-500 text-5xl mb-4">✗</div>
        <p class="text-lg mb-4">Authentication failed</p>
        <p class="text-gray-600 mb-6">{{ errorMessage }}</p>
        <button @click="retryAuth" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
          Try Again
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSpotifyStore } from '~/stores/spotify';

const route = useRoute();
const router = useRouter();
const spotifyStore = useSpotifyStore();

const loading = ref(true);
const success = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  // Check if we have an error in query parameters
  const error = route.query.error as string;
  
  // If we have an error, display it
  if (error) {
    loading.value = false;
    errorMessage.value = decodeURIComponent(error);
    return;
  }
  
  // Check if we have an authorization code in query parameters
  const code = route.query.code as string;
  
  if (!code) {
    loading.value = false;
    errorMessage.value = 'No authorization code received from Spotify';
    return;
  }
  
  try {
    // Handle the callback with the authorization code
    const result = await spotifyStore.handleCallback(code);
    
    if (result.success) {
      success.value = true;
    } else {
      errorMessage.value = result.error || 'Failed to authenticate with Spotify';
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'An unexpected error occurred';
  } finally {
    loading.value = false;
  }
});

const goToApp = () => {
  // Redirect to the main app
  router.push('/');
};

const retryAuth = () => {
  // Redirect to Spotify authentication
  spotifyStore.authenticate();
};
</script>