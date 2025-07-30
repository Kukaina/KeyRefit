import { createApp } from 'vue'
import App from './App.vue'


const app = createApp(App)

app.mount('#app')


window.addEventListener('beforeunload', (e) => {
    e.preventDefault()
    if (window.pywebview) {
        window.pywebview.api.minimize_window()
    }
    e.returnValue = ''
})
