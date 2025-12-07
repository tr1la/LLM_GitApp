// Mock localStorage for server-side rendering
if (typeof global !== 'undefined' && typeof (global as any).localStorage === 'undefined') {
  const store: Record<string, string> = {};
  
  (global as any).localStorage = {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      for (const key in store) {
        delete store[key];
      }
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] ?? null;
    },
    get length() {
      return Object.keys(store).length;
    },
  };
}

export default defineEventHandler(() => {
  // Ensure localStorage is available on the server
});
