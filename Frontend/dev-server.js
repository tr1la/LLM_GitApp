#!/usr/bin/env node
import { LocalStorage } from 'node-localstorage';

// Initialize localStorage in the global scope BEFORE anything else loads
if (typeof global.localStorage === 'undefined') {
  try {
    global.localStorage = new LocalStorage('./scratch');
  } catch (e) {
    // Fallback to in-memory storage if LocalStorage fails
    const store = {};
    global.localStorage = {
      getItem: (key) => store[key] || null,
      setItem: (key, value) => { store[key] = value; },
      removeItem: (key) => { delete store[key]; },
      clear: () => { Object.keys(store).forEach(k => delete store[k]); },
      key: (index) => Object.keys(store)[index] || null,
      length: Object.keys(store).length,
    };
  }
}

// Now import and run Nuxt
import { exec } from 'child_process';
import { spawn } from 'child_process';

const nuxtProcess = spawn('nuxt', ['dev'], {
  env: {
    ...process.env,
    NUXT_HOST: '0.0.0.0',
    NUXT_PORT: '3000',
  },
  stdio: 'inherit',
});

nuxtProcess.on('exit', (code) => process.exit(code));
