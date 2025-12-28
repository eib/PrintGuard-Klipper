# Webcam Provider

Use the `webcam` provider for either:

- A **browser webcam** (streamed from a WebUI browser session), or
- A direct **RTSP/IP camera** URL.

This provider is **camera-only** (it does not provide printer status or control).

## Setup

### Browser webcam

1. In the WebUI, select **Browser Webcam** as the source type.
2. Pick a camera device from your browser’s device list.

Notes:
- Browser webcams can’t be validated server-side until there is an active browser session.
- The browser must keep streaming for the server to consume it.

### RTSP/IP camera

1. Choose **RTSP/IP Camera** as the source type.
2. Enter an RTSP URL like:

   `rtsp://username:password@ip:port/path`

Notes:
- Validation attempts to open the RTSP stream on the server.
- The PrintGuard server must be able to reach the camera URL.

