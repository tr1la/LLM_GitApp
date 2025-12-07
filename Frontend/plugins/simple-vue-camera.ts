import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  if (process.client) {
    // Lazy load Camera component to avoid SSR issues
    const Camera = defineAsyncComponent(() =>
      import('simple-vue-camera').catch(err => {
        console.warn('Failed to load Camera component:', err)
        return { default: null }
      })
    )
    
    if (Camera) {
      nuxtApp.vueApp.component('Camera', Camera)
    }
  }
})

import { defineAsyncComponent } from 'vue'
