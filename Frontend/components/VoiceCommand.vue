<template>
  <div class="voice-command-container bg-white rounded-xl shadow-md p-4 w-full max-w-md">
    <!-- Visualizer -->
    <VoiceVisualizer :isRecording="isRecording" :decibelLevel="decibelLevel" />

    <!-- User's voice input -->
    <div 
      v-if="lastTranscript" 
      class="mt-3 p-2 bg-gray-50 rounded-lg border border-gray-100"
    >
      <p class="text-sm text-gray-600">
        <span class="font-medium">You said:</span> "{{ lastTranscript }}"
      </p>
    </div>

    <!-- Feedback message -->
    <div 
      v-if="feedback" 
      class="mt-3 p-2 rounded-lg flex items-center space-x-2"
      :class="feedbackType === 'success' ? 'bg-green-50 text-green-700' : feedbackType === 'error' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'"
    >
      <i 
        :class="feedbackType === 'success' ? 'fas fa-check-circle' : feedbackType === 'error' ? 'fas fa-times-circle' : 'fas fa-info-circle'"
        class="text-sm"
      ></i>
      <p class="text-sm">{{ feedback }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { Ref } from 'vue';
import { useNuxtApp } from '#app';
import VoiceVisualizer from './VoiceVisualizer.vue';
import { useSpotifyStore } from '@/stores/spotify';
import { useNewsStore } from '@/stores/news';
import { useChatbotStore } from '@/stores/chatbot'

const chatbotStore = useChatbotStore()

const newsStore = useNewsStore();
const emit = defineEmits(['featureMatched']);
const { $sendAudioForCommand } = useNuxtApp();
const spotifyStore = useSpotifyStore();

const props = defineProps<{
  selectedFeature: string;
  cameraRef: Ref | null;
}>();

// State
const isRecording = ref(false);
const decibelLevel = ref(0);
const feedback = ref<string | null>(null);
const feedbackType = ref<'success' | 'error' | 'info'>('info');
const lastTranscript = ref<string | null>(null);
const isSpeaking = ref(false); // New state to track if system is speaking

let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];
let audioContext: AudioContext | null = null;
let analyser: AnalyserNode | null = null;
let intervalId: ReturnType<typeof setInterval>;
let speechCheckInterval: ReturnType<typeof setInterval>; // Interval to check if system is speaking

// Constants
const DECIBEL_THRESHOLD = 10;
const SPEECH_MIN_DURATION = 500;
const FEEDBACK_DURATION = 5000; // How long feedback messages stay visible (ms)
let speechDetected = false;
let speechStartTime: number | null = null;
let feedbackTimeout: ReturnType<typeof setTimeout> | null = null;  // Corrected type for browser-based code

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const globalCommands = {
  stop: ['stop', 'mute', 'shut up', 'quiet'],
  help: ['help', 'what can i say', 'commands'],
  cancel: ['cancel', 'never mind'],
};

// Define available commands for each feature
const featureCommands = {
  'Text': {
    'read': ['read', 'read text', 'read aloud'],
    'translate': ['translate', 'translate text'],
    'save': ['save', 'save text', 'remember'],
    'capture': ['capture', 'take a picture', 'snapshot'],
  },
  'Music': {
    'detect': ['detect', 'what song', 'identify song', 'recognize'],
    'play': ['play', 'start', 'resume'],
    'pause': ['pause', 'stop', 'mute'],
  },
  'Chatbot': {
    'ask': ['ask', 'question', 'help me'],
    'chat': ['chat', 'talk', 'converse'],
  },
  'News': {
    'summarize': ['summarize', 'summary', 'brief'],
    'read': ['read', 'read aloud', 'narrate'],
  }
};

// Add this above setup block or with other functions
const cancelSpeech = () => {
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
    console.log('🛑 Speech synthesis canceled due to user speaking.');
    isSpeaking.value = false; // Update speaking state
  }
};

// Function to check if system is currently speaking
const checkIfSpeaking = () => {
  if (speechSynthesis.speaking && !isSpeaking.value) {
    // System started speaking, pause recording
    isSpeaking.value = true;
    stopRecording();
    console.log('🎙️ Paused recording because system is speaking');
  } else if (!speechSynthesis.speaking && isSpeaking.value) {
    // System finished speaking, resume recording
    isSpeaking.value = false;
    console.log('🎙️ Resuming recording because system finished speaking');
    startRecording();
  }
};

const getAvailableCommands = () => {
  const global = Object.keys(globalCommands).join(', ');
  if (!props.selectedFeature || !(featureCommands as Record<string, Record<string, string[]>>)[props.selectedFeature]) {
    return `Global: ${global}`;
  }

  const featureSpecific = Object.keys((featureCommands as Record<string, Record<string, string[]>>)[props.selectedFeature]).join(', ');
  return `Feature: ${featureSpecific} | Global: ${global}`;
};

//////////////// ARTICLE_SECTION //////////////////////

const ordinalMap: Record<string, number> = {
  first: 0,
  second: 1,
  third: 2,
  fourth: 3,
  fifth: 4,
  sixth: 5,
  seventh: 6,
  eighth: 7,
  ninth: 8,
  tenth: 9
};

const getArticleIndexFromCommand = (command: string): number | null => {
  const lower = command.toLowerCase();

  // Match "first", "second", etc.
  for (const key in ordinalMap) {
    console.log(key)
    if (lower.includes(key)) return ordinalMap[key];
  }

  // Match digits (e.g. "read article 3")
  const match = lower.match(/(?:article\s*)?(\d+)/);
  if (match && match[1]) {
    const num = parseInt(match[1]);
    if (!isNaN(num) && num >= 1 && num <= newsStore.articles.length) {
      return num - 1;
    }
  }

  return null;
};

const findArticleByQuery = (query: string) => {
  const lowerQuery = query.toLowerCase();
  return newsStore.articles.find(article =>
    article.title.toLowerCase().includes(lowerQuery) ||
    article.summary?.toLowerCase().includes(lowerQuery)
  );
};

const speakArticle = async (article: { title: string; summary: string }) => {
  const utterance = new SpeechSynthesisUtterance(`${article.title}. ${article.summary}`);
  utterance.lang = 'en-US';
  speechSynthesis.speak(utterance);
};

/////////////////////////////////////////////////////

// Start voice recording
const startRecording = async () => {
  // If recording is already active or system is speaking, do nothing
  if (isRecording.value || speechSynthesis.speaking) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];

    // Set up audio analysis - handle possible existing audioContext
    if (audioContext && audioContext.state === 'suspended') {
      await audioContext.resume();
    } else {
      audioContext = new AudioContext();
    }

    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    analyser.fftSize = 256;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    // Track audio levels for visualization and speech detection
    const trackDecibels = () => {
      if (!analyser || !isRecording.value) return;

      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const normalized = dataArray[i] - 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      decibelLevel.value = Math.min(100, rms * 10);

      const now = Date.now();
      if (decibelLevel.value > DECIBEL_THRESHOLD) {
        // cancelSpeech(); // 💥 Interrupt system speech when user starts speaking
        if (!speechStartTime) speechStartTime = now;
        else if (now - speechStartTime > SPEECH_MIN_DURATION) {
          speechDetected = true;
        }
      } else {
        speechStartTime = null;
      }

      if (isRecording.value) requestAnimationFrame(trackDecibels);
    };

    // Set up media recorder
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
      // Don't process if we manually stopped recording for music detection
      if (!isRecording.value) {
        console.log('Recording stopped manually. Skipping processing.');
        resetSpeechFlags();
        return;
      }

      if(speechSynthesis.speaking) {
        console.log('Feedback is being spoken. Skipping request.');
        resetSpeechFlags();
        return;
      }

      if (!speechDetected) {
        console.log('❌ No significant speech detected. Skipping request.');
        resetSpeechFlags();
        return;
      }

      // Process the audio for commands
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      const data = await $sendAudioForCommand(props.selectedFeature, blob);

      const commandText = data.command;

      lastTranscript.value = data.query;

      if (data.query === "") {
        console.log("Nothing to record")
        resetSpeechFlags();
        return;
      }

      // if the current feature matched the command then it is a query of the feature
      if (props.selectedFeature === data.command && data.command === "News") {
        if (data.intent === "read" || commandText.toLowerCase().includes("read")) {
          const articleIndex = getArticleIndexFromCommand(data.query);
          if (articleIndex !== null && newsStore.articles[articleIndex]) {
            const article = newsStore.articles[articleIndex];
            showFeedback(`Reading article ${articleIndex + 1}...`);
            await speakArticle(article);
          } else {
            showFeedback("Sorry, I couldn't find which article you wanted me to read.");
          }
          return;
        }

        // Normal query intent
        if (data.intent === "query" && data.command === "News") {
          showFeedback("Fetching required articles...");
          await newsStore.fetchNews(data.query);
          showFeedback("Articles updated.");
          return;
        }
      }

      if (props.selectedFeature === data.command && data.command === "Chatbot") {
        if (data.intent == "query") {
          console.log("Chatbot query detected:", data.query);
          const reply = await chatbotStore.sendMessage(data.query);
          showFeedback(`${reply}`);
          return;
        }
      }

      if (!commandText) {
        showFeedback("Sorry, I didn't understand that.");
        resetSpeechFlags();
        return;
      }

      const lowerCommand = commandText.toLowerCase();
      console.log('Voice command recognized:', lowerCommand);

      // Check if command is a feature selection
      const featureMatch = Object.keys(featureCommands).find(
        feature => feature.toLowerCase() === lowerCommand
      );

      console.log('Feature match:', featureMatch);
      console.log('Selected feature:', props.selectedFeature);
      console.log("cameraRef:", props.cameraRef);

      if (featureMatch) {
        // User is selecting a feature
        showFeedback(`Switched to ${featureMatch} mode`);
        emit('featureMatched', featureMatch);
      }
      else if (props.selectedFeature) {
        // User is using a feature-specific command
        await handleFeatureCommand(lowerCommand);
      }
      else {
        // No feature selected yet
        showFeedback(`Please select a feature first. Say one of: ${Object.keys(featureCommands).join(', ')}`);
      }

      resetSpeechFlags();
    };

    const resetSpeechFlags = () => {
      speechDetected = false;
      speechStartTime = null;
      audioChunks = [];
    };

    // Start recording and analysis
    isRecording.value = true;
    mediaRecorder.start();
    trackDecibels();

    // Restart recording every 5 seconds
    intervalId = setInterval(() => {
      if (mediaRecorder?.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.start();
      }
    }, 5000);
  } catch (error) {
    console.error('Error starting voice recording:', error);
    showFeedback('Unable to access microphone. Please check permissions.');
  }
};

const handleFeatureCommand = async (command: string) => {
  // Check for global commands first
  for (const action in globalCommands) {
    if ((globalCommands as Record<string, string[]>)[action].some((phrase: string) => command.includes(phrase))) {
      await executeGlobalCommand(action);
      return;
    }
  }

  const currentFeature = props.selectedFeature;
  if (!currentFeature || !(featureCommands as Record<string, Record<string, string[]>>)[currentFeature]) {
    showFeedback(`The command "${command}" doesn't match any available feature.`);
    return;
  }

  const commands = (featureCommands as Record<string, Record<string, string[]>>)[currentFeature];
  let matchedAction = null;

  for (const action in commands) {
    if ((commands as Record<string, string[]>)[action].some((phrase: string) => command.includes(phrase))) {
      matchedAction = action;
      break;
    }
  }

  if (matchedAction) {
    await executeCommand(currentFeature, matchedAction, command);
  } else {
    showFeedback(`The command "${command}" is not valid for ${currentFeature} mode. Try: ${getAvailableCommands()}`);
  }
};

const executeGlobalCommand = async (action: string) => {
  switch (action) {
    case 'stop':
      showFeedback('Stopping all audio...');
      speechSynthesis.cancel();
      if (spotifyStore.isPlaying) {
        spotifyStore.pauseMusic();
      }
      break;

    case 'help':
      showFeedback(`Say one of these global commands: ${Object.keys(globalCommands).join(', ')}`);
      break;

    case 'cancel':
      showFeedback('Okay, canceled.');
      break;

    default:
      showFeedback(`Unknown global command: ${action}`);
  }
};

// Execute the matched command
const executeCommand = async (feature: string, action: string, originalCommand: string) => {
  console.log(`Executing command: ${action} for feature: ${feature}`);

  switch (feature) {
    case 'Music':
      await executeMusicCommand(action);
      break;
    case 'Text':
      await executeCameraCommand(feature);
      break;
    case 'Chatbot':
      await executeChatbotCommand(action);
      break;
    case 'News':
      await executeNewsCommand(action);
      break;
    default:
      showFeedback(`Feature ${feature} not yet implemented`);
  }
};

// Execute music-specific commands
const executeMusicCommand = async (action: string) => {
  switch (action) {
    case 'detect':
      showFeedback('Detecting music');
      
      // Directly trigger the Spotify detection by clicking the button
      try {
        // Find and click the "Detect Music" button directly in the DOM
        // This is the most reliable approach since it doesn't depend on component references
        
        // Look for the button containing "Detect Music" text
        let detectMusicButton = null;
        const buttons = document.querySelectorAll('button');
        for (let button of buttons) {
          if (button.textContent && button.textContent.trim() === 'Detect Music') {
            detectMusicButton = button;
            break;
          }
        }
        
        if (detectMusicButton) {
          (detectMusicButton as HTMLElement).click();
        } else {
          // If we can't find the button, check if we're on the right feature
          if (props.selectedFeature !== 'Music') {
            showFeedback(`Please select the Music feature first before detecting music.`);
          } else {
            showFeedback(`Could not find the Detect Music button. Make sure you're authenticated with Spotify.`);
          }
        }
      } catch (error: any) {
        console.error("Error clicking detect music button:", error);
        showFeedback(`Failed to detect music: ${error.message || 'Unknown error'}`);
      }
      break;

    case 'play':
    case 'pause':
      try {
        // Find and click the play/pause button directly in the DOM
        // This button has a dynamic SVG icon based on the current state
        const playPauseButton = document.querySelector('button.bg-green-500');
        
        if (playPauseButton) {
          (playPauseButton as HTMLElement).click();
          showFeedback(action === 'play' ? 'Playing music' : 'Pausing music');
        } else {
          // If we can't find the button, check if we're on the right feature
          if (props.selectedFeature !== 'Music') {
            showFeedback(`Please select the Music feature first.`);
          } else {
            showFeedback(`Could not find the play/pause button. Make sure a song is loaded.`);
          }
        }
      } catch (error: any) {
        console.error(`Error clicking ${action} button:`, error);
        showFeedback(`Failed to ${action} music: ${error.message || 'Unknown error'}`);
      }
      break;
  }
};

const executeCameraCommand = async (action: string) => {
  console.log("Taking a snapshot with current feature:", action);
  
  try {
    // Find and click the "Take Snapshot" button directly in the DOM
    // This is the most reliable approach since it doesn't depend on component references
    const snapshotButton = document.querySelector('button[aria-label="Take a snapshot"]');
    
    if (snapshotButton) {
      (snapshotButton as HTMLElement).click();
      showFeedback(`Capturing snapshot for ${action}...`);
    } else {
      // If we can't find the button, check if we're on the right feature
      if (props.selectedFeature !== 'Text') {
        showFeedback(`Please select the Text feature first before taking a snapshot.`);
      } else {
        showFeedback(`Could not find the Take Snapshot button. Make sure the camera has finished loading.`);
      }
    }
  } catch (error: any) {
    console.error("Error clicking snapshot button:", error);
    showFeedback(`Failed to capture snapshot: ${error.message || 'Unknown error'}`);
  }
}

const executeChatbotCommand = async (action: string) => {
  showFeedback(`Executing ${action} for chatbot feature`);
  // Implementation would depend on your chatbot feature capabilities
};

const executeNewsCommand = async (action: string) => {
  showFeedback(`Executing ${action} for News feature`);
  // Implementation would depend on your News feature capabilities
};

// Display feedback and speak it
const showFeedback = async (message: string, type: 'success' | 'error' | 'info' = 'info', delayAfter: number = 500) => {
  feedback.value = message;
  feedbackType.value = type;

  console.log('Feedback:', message);

  await speak(message);
  await sleep(delayAfter);

  if (feedbackTimeout) clearTimeout(feedbackTimeout);
  feedbackTimeout = setTimeout(() => {
    feedback.value = null;
  }, FEEDBACK_DURATION);
};

// Text-to-speech
const speak = (text: string): Promise<void> => {
  return new Promise(resolve => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => {
      console.log('🔊 Finished speaking');
      resolve();
    };
    speechSynthesis.speak(utterance);
  });
};

const stopRecording = async () => {
  isRecording.value = false;

  // Stop the recorder if active
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }

  // Stop refreshing audio chunks
  clearInterval(intervalId);

  // Suspend audio context
  if (audioContext) {
    await audioContext.suspend(); // Wait for suspend to complete
  }

  // Release media tracks
  if (mediaRecorder?.stream) {
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }

  // Reset everything
  audioChunks = [];
  mediaRecorder = null;
};

// Lifecycle hooks
onMounted(() => {
  startRecording();
  // Start checking if system is speaking
  speechCheckInterval = setInterval(checkIfSpeaking, 100); // Check every 100ms
  
  // Listen for music detection event from SpotifyFeature
  window.addEventListener('stop-voice-recording-for-music-detection', handleMusicDetectionEvent);
  
  // Listen for Spotify errors
  window.addEventListener('spotify-error', handleSpotifyError);
});

const handleMusicDetectionEvent = () => {
  console.log('Received music detection event, stopping recording');
  // Stop the microphone before music detection
  stopRecording();
  
  // Also clear the interval to prevent automatic restart
  if (intervalId) {
    clearInterval(intervalId);
  }
  
  // Temporarily disable the speech check to prevent automatic restart
  if (speechCheckInterval) {
    clearInterval(speechCheckInterval);
  }
  
  // Restart recording after a delay to allow music detection to complete
  setTimeout(() => {
    console.log('Restarting recording after music detection');
    startRecording();
    // Re-enable the speech check
    speechCheckInterval = setInterval(checkIfSpeaking, 100);
   
  }, 13000); // Wait 13 seconds for music detection to complete
};

const handleSpotifyError = (event: any) => {
  const detail = event.detail as { message: string };
  if (detail && detail.message) {
    showFeedback(detail.message);
  }
};

onUnmounted(() => {
  stopRecording();
  if (feedbackTimeout) {
    clearTimeout(feedbackTimeout);
  }
  // Clear the speech check interval
  if (speechCheckInterval) {
    clearInterval(speechCheckInterval);
  }
  // Remove event listeners
  window.removeEventListener('stop-voice-recording-for-music-detection', handleMusicDetectionEvent);
  window.removeEventListener('spotify-error', handleSpotifyError);
});
</script>

<style scoped>
.voice-command-container {
  border-radius: 12px;
  transition: all 0.3s ease;
}
</style>