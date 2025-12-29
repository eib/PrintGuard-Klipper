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
      throw new Error('Service Worker registration failed')
    }
  }
  throw new Error('Service Worker not supported in this browser')
}

export async function getSubscription() {
  if (!('serviceWorker' in navigator)) return null
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) return null
  return await registration.pushManager.getSubscription()
}

export async function validateSubscription(subscription: PushSubscription | null): Promise<boolean> {
  if (!subscription) return false

  try {
    const vapidKeyResponse = await notificationsApi.getVapidPublicKey()
    const vapidPublicKey = vapidKeyResponse.data.public_key

    if (!vapidPublicKey) return false

    const serverKey = urlBase64ToUint8Array(vapidPublicKey)
    const subKey = new Uint8Array(subscription.options.applicationServerKey as ArrayBuffer)

    if (serverKey.length !== subKey.length) return false
    for (let i = 0; i < serverKey.length; i++) {
      if (serverKey[i] !== subKey[i]) return false
    }

    return true
  } catch (error) {
    console.error('Failed to validate subscription:', error)
    return false
  }
}

export async function unsubscribe() {
  const subscription = await getSubscription()
  if (subscription) {
    try {
      await notificationsApi.unsubscribe(subscription.toJSON())
    } catch (e) {
      console.warn('Failed to notify backend of unsubscription', e)
    }
    await subscription.unsubscribe()
  }
}

export async function subscribeUserToPush() {
  const registration = await registerServiceWorker()
  if (!registration) {
    throw new Error('Service Worker not available')
  }

  const permission = await Notification.requestPermission()
  if (permission !== 'granted') {
    throw new Error('PERMISSION_DENIED')
  }

  const vapidKeyResponse = await notificationsApi.getVapidPublicKey()
  const vapidPublicKey = vapidKeyResponse.data.public_key

  if (!vapidPublicKey) {
    throw new Error('VAPID_MISSING')
  }

  console.log('Subscribing to push with VAPID key...')
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
  })

  console.log('Got browser subscription, registering with backend...')
  await notificationsApi.subscribe(subscription.toJSON())
  console.log('User subscribed to push notifications successfully')
  return subscription
}

export async function isSubscribed() {
  const subscription = await getSubscription()
  return !!subscription
}

export async function getPushEndpoint() {
  const subscription = await getSubscription()
  return subscription?.endpoint || null
}
