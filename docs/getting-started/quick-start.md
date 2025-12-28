# Quick Start Guide

Get PrintGuard detecting print failures in 5 minutes.

## Step 1: Start PrintGuard

The fastest way to get started is using Docker:

```bash
docker run -d \
  --name printguard \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  --privileged \
  ghcr.io/oliverbravery/printguard:latest
```

## Step 2: Login

1. Open `http://localhost:8000` in your browser.
2. Login with the default admin credentials (check the logs if you've never run it before: `docker logs printguard`).

## Step 3: Add a Connection (Optional)

If using OctoPrint or Bambu Labs:

1. Go to **Connections** page.
2. Click **Add Connection**.
3. Select your printer type.
4. Enter connection details (API Key, IP address, etc).

## Step 4: Add a Camera Component

1. Go to **Components** page.
2. Click **Add Component**.
3. Select **Camera** type.
4. Choose **Webcam** provider (for local USB cameras) or **IP Camera**.
5. Select your camera device or enter the URL.

## Step 5: Create a Printer

1. Go to **Dashboard**.
2. Click **Add Printer**.
3. Enter printer name.
4. Select your camera component and any optional connections.
5. Click **Create**.

## Step 6: Start Monitoring

1. Click on your printer card in the Dashboard.
2. The live feed will appear.
3. Inference status shows detection results in real-time.
4. **Green** = Normal, **Red** = Defect detected.

## Next Steps

- [Configure notifications](../user-guide/notifications.md)
- [Set up auto-pause on detection](../user-guide/printers.md)
- [Add printer integration](../integrations/overview.md)
- [Integrate with Home Assistant](../home-assistant/installation.md)
