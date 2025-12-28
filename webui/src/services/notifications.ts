import { notificationsApi } from './api'

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

export async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })
      
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'LOG') {
          console.log(event.data.message, event.data.data);
        }
      });

      await navigator.serviceWorker.ready;
      console.log('Service Worker registered and ready');
      return registration
    } catch (error) {
      console.error('Service Worker registration failed:', error)
    }
  }
}

export async function subscribeUserToPush() {
  const registration = await registerServiceWorker()
  if (!registration) {
    console.error('Service Worker not available')
    return
  }

  try {
    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
      console.warn('Notification permission not granted')
      alert('You need to allow notifications to use this feature.')
      return
    }

    const vapidKeyResponse = await notificationsApi.getVapidPublicKey()
    const vapidPublicKey = vapidKeyResponse.data.public_key

    if (!vapidPublicKey) {
      alert('Push notifications are not configured on the server (VAPID keys missing).')
      console.error('VAPID public key not found')
      return
    }

    console.log('Subscribing to push with VAPID key...')
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
    })

    console.log('Got browser subscription, registering with backend...')
    await notificationsApi.subscribe(subscription.toJSON())
    console.log('User subscribed to push notifications successfully')
  } catch (error) {
    console.error('Failed to subscribe user to push notifications:', error)
    alert('Failed to subscribe to notifications. Check console for details.')
  }
}

export async function isSubscribed() {
  if (!('serviceWorker' in navigator)) return false
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) return false
  const subscription = await registration.pushManager.getSubscription()
  return !!subscription
}

export async function getPushEndpoint() {
  if (!('serviceWorker' in navigator)) return null
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) return null
  const subscription = await registration.pushManager.getSubscription()
  return subscription?.endpoint || null
}

