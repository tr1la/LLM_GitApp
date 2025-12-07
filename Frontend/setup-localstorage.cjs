const { LocalStorage } = require('node-localstorage');

// Initialize localStorage IMMEDIATELY when this module loads
if (typeof global.localStorage === 'undefined') {
  try {
    global.localStorage = new LocalStorage('./scratch');
  } catch (e) {
    // Fallback to in-memory storage
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
