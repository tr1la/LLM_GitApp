<template>
  <div class="flex flex-col items-center space-y-6">
    <!-- Camera Container -->
    <div 
      class="w-[320px] h-[240px] rounded-lg overflow-hidden shadow-lg bg-black"
    >
      <Camera 
        v-if="isClient && !cameraError"
        :resolution="cameraResolution" 
        ref="cameraRef"
        @error="handleCameraError"
      />
      <div v-else-if="cameraError" class="w-full h-full flex items-center justify-center text-white text-center p-4">
        <p>{{ cameraError }}</p>
      </div>
      <div v-else class="w-full h-full flex items-center justify-center text-white">
        <p v-if="!cameraReady">Initializing camera...</p>
      </div>
    </div>

    <!-- Snapshot Button -->
    <div>
      <button 
        class="btn btn-primary px-6 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        @click="takeSnapshot"
        :disabled="cameraError !== null || !cameraReady"
        aria-label="Take a snapshot"
        title="Take a snapshot"
      >
        Take Snapshot
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';

const props = defineProps({
  featureType: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['take-snapshot']);

// Refs
const cameraRef = ref<any>();
const cameraResolution = ref({ width: 320, height: 240 });
const isClient = ref(false);
const cameraError = ref<string | null>(null);
const cameraReady = ref(false);

onMounted(async () => {
  isClient.value = true;
  
  // Wait for camera component to mount
  await nextTick();
  
  // Poll for camera readiness (check every 200ms for up to 5 seconds)
  let attempts = 0;
  const maxAttempts = 25; // 5 seconds with 200ms intervals
  
  const checkCameraReady = () => {
    attempts++;
    if (cameraRef.value) {
      cameraReady.value = true;
      console.log('Camera is ready');
    } else if (attempts < maxAttempts) {
      setTimeout(checkCameraReady, 200);
    } else {
      cameraError.value = 'Camera initialization timed out';
      console.log('Camera initialization timed out');
    }
  };
  
  // Start checking for camera readiness
  checkCameraReady();
});

const handleCameraError = (error: any) => {
  console.error('Camera error event:', error);
  cameraError.value = 'Camera error: ' + (error?.message || 'Unknown error');
};

// Methods
const takeSnapshot = async () => {
  console.log('Taking snapshot...');
  console.log('Camera ref value:', cameraRef.value);
  
  try {
    if (!cameraRef.value) {
      cameraError.value = 'Camera not ready';
      console.log('Camera ref is null or undefined');
      return;
    }
    
    // Wait a bit for the camera to be ready
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Check if snapshot method exists
    if (typeof cameraRef.value.snapshot !== 'function') {
      cameraError.value = 'Camera snapshot method not available';
      console.log('Camera snapshot method not available');
      console.log('Camera ref value structure:', Object.keys(cameraRef.value || {}));
      return;
    }
    
    const blob = await cameraRef.value.snapshot();
    if (blob) {
      emit('take-snapshot', blob);
      cameraError.value = null;
      console.log('Snapshot captured successfully');
    } else {
      cameraError.value = 'Failed to capture snapshot - no data';
      console.log('Snapshot returned no data');
    }
  } catch (error: any) {
    cameraError.value = `Snapshot error: ${error?.message || 'Unknown error'}`;
    console.error('Snapshot error:', error);
  }
};

// Expose methods to parent
defineExpose({
  takeSnapshot,
  camera: cameraRef,
  isCameraReady: () => cameraReady.value && cameraRef.value !== null,
  getCameraStatus: () => ({
    isReady: cameraReady.value && cameraRef.value !== null,
    hasError: cameraError.value !== null,
    errorMessage: cameraError.value,
    isClient: isClient.value
  })
});
</script>

<style scoped>
/* Camera container styles */
.bg-black {
  background-color: #000;
}

.shadow-lg {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Button styles */
.btn-primary {
  background-color: #2563eb; /* Bright blue */
  color: white;
  border: none;
  border-radius: 0.5rem;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.btn-primary:hover {
  background-color: #1d4ed8; /* Darker blue */
  transform: scale(1.05);
}

.focus\:ring-2 {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5); /* Blue focus ring */
}
</style>