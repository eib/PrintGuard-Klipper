# Components

Components are the building blocks that make up a printer: cameras, status sources, and control sources. A printer links up to three components into roles (`camera`, `status`, `control`).

## Overview

The component library.

## Usage

1. Go to **Component Library** → **Add Component**.
2. Choose a component type:
   - `camera`
   - `status`
   - `control`
3. Choose how it’s configured:
   - **From a Connection**: pick an existing connection and browse/select an entity (if the provider supports entity browsing).
   - **Standalone**: configure without a connection (e.g. Webcam).
4. Save the component.

## Previewing cameras

- Camera components can be previewed from the library. PrintGuard will start (or multiplex) a stream and show it in the modal.

## Notes

- Components can’t be deleted while in use by printers unless you force deletion (the WebUI will warn you and the API may return a 409 conflict).
- For browser webcams, the camera is streamed from a browser session; other sessions can view the stream by session id.

