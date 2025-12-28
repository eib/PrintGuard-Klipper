# Printers

Printers are the top-level objects you monitor and control. Each printer links a required **camera** component plus optional **status** and **control** components.

## Overview

Managing your printers.

## Usage

1. Go to **Dashboard** and click **Add Printer**.
2. Set a name.
3. Select a **Camera Source** (required).
4. Optionally select:
   - **Status Source** (improves printing/idle detection)
   - **Control Source** (enables start/pause/resume/stop and automated defect actions)
5. Configure inference settings:
   - **Sensitivity**
   - **Majority voting**
   - **Target detections per second**
   - **Action on defect** (requires a control source)
6. (Optional) enable **defect notifications** for this printer (browser permission required).
7. Save.

## Editing printers

- Use the **settings** icon on a printer card to edit its components and inference settings.

