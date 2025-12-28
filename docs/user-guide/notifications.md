# Notifications

PrintGuard supports browser push notifications for defect alerts, configured per device (browser) and per printer.

## Overview

Setting up push notifications.

## Usage

1. In the WebUI, enable notifications on a printer (bell icon on the printer card or checkbox in the printer editor).
2. Your browser will prompt for notification permission.
3. Once granted, the WebUI registers a service worker (`/sw.js`) and subscribes your browser to push using the server’s VAPID public key (`GET /api/notifications/vapid-public-key`).
4. PrintGuard stores this device subscription and you can then toggle notifications per printer.

## Notes / troubleshooting

- Notifications are **device-specific**. Each browser/device has its own push endpoint.
- If the server has no VAPID keys configured, subscription will fail. (You can generate keys with the PrintGuard CLI; see the CLI reference.)
- You can send a test notification from a printer card when notifications are enabled.

