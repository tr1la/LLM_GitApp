//***Rename to .env.mjs
// This file needs to run before any other module initialization 
import { LocalStorage } from 'node-localstorage';

if (typeof global !== 'undefined' && typeof global.localStorage === 'undefined') {
  global.localStorage = new LocalStorage('./scratch');
}
