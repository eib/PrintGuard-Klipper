self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

async function broadcast(message, data = {}) {
  const allClients = await clients.matchAll({ type: 'window' });
  for (const client of allClients) {
    client.postMessage({
      type: 'LOG',
      message: `[SW Log] ${message}`,
      data: data
    });
  }
}

self.addEventListener('push', function(event) {
  let data = {};
  try {
    if (event.data) {
      data = event.data.json();
    }
  } catch (e) {
    data = { 
      title: 'PrintGuard Notification', 
      body: event.data ? event.data.text() : 'A printer defect was detected.' 
    };
  }

  const title = data.title || 'PrintGuard Notification';
  
  const toAbsolute = (url) => {
    if (!url) return undefined;
    if (url.startsWith('http')) return url;
    return self.location.origin + (url.startsWith('/') ? '' : '/') + url;
  };

  const options = {
    body: data.body || 'Defect detected.',
    icon: toAbsolute(data.icon) || toAbsolute('/vite.svg'),
    image: toAbsolute(data.image),
    badge: toAbsolute(data.badge) || toAbsolute('/vite.svg'),
    data: data.data || {},
    tag: 'defect-' + (data.data?.printer_id || 'general'),
    renotify: true,
  };

  event.waitUntil(
    Promise.all([
      broadcast('Push Received', { title, options }),
      self.registration.showNotification(title, options)
        .then(() => broadcast('Notification shown successfully'))
        .catch(err => broadcast('Error showing notification', { error: err.message }))
    ])
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/';
  
  const fullUrl = new URL(url, self.location.origin).href;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url === fullUrl && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(fullUrl);
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/';
  const fullUrl = new URL(url, self.location.origin).href;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url === fullUrl && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(fullUrl);
    })
  );
});

