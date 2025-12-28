# HA Automations

PrintGuard exposes both Home Assistant entities and a Home Assistant event you can use for automations.

## Examples

### Trigger on defect event

The integration fires an event named `printguard_defect_detected` when the prediction class changes to anything other than `normal`.

```yaml
automation:
  - alias: "PrintGuard: Defect detected"
    trigger:
      - platform: event
        event_type: printguard_defect_detected
    action:
      - service: notify.notify
        data:
          title: "PrintGuard Defect"
          message: >
            {{ trigger.event.data.printer_name }} reported {{ trigger.event.data.class }}
            (confidence {{ (trigger.event.data.confidence | float * 100) | round(1) }}%).
```

### Trigger from the binary sensor

```yaml
automation:
  - alias: "PrintGuard: Defect binary sensor"
    trigger:
      - platform: state
        entity_id: binary_sensor.printguard_<printer_id>_defect
        to: "on"
    action:
      - service: notify.notify
        data:
          message: "Defect detected on PrintGuard printer <printer_id>."

