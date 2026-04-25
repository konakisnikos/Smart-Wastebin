# Smart-Wastebin Custom Ontology

**Namespace:** `https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#`  
**Prefix:** `smartbin`

This document defines all custom terms used in the `smartbin:` namespace. These terms cover pipeline-specific fields and sensor properties that have no direct equivalent in standard vocabularies (SOSA, SSN, schema.org, BOT).

---

## Sensor Properties

### [smartbin:gpioPin](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#gpioPin)
- **Type:** `xsd:integer`
- **Description:** The BCM-numbered GPIO pin on the Raspberry Pi to which the sensor's output line is connected.

### [smartbin:sensingPrinciple](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#sensingPrinciple)
- **Type:** `xsd:string`
- **Description:** The physical principle by which the sensor detects its observable property (e.g. "Passive Infrared").

### [smartbin:detectionRangeMetres](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#detectionRangeMetres)
- **Type:** `xsd:float`
- **Description:** Maximum detection range of the sensor in metres.

---

## Wastebin Properties

### [smartbin:maximumCapacity](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#maximumCapacity)
- **Type:** `xsd:float`
- **Description:** The total capacity of the wastebin in cubic centimetres.

---

## Pipeline Event Fields

### [smartbin:ingestTime](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#ingestTime)
- **Type:** `xsd:dateTime`
- **Description:** UTC timestamp at which the consumer wrote the event to the output file. Distinct from `sosa:resultTime` (when the sensor observed the event).

### [smartbin:deviceId](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#deviceId)
- **Type:** `xsd:string`
- **Description:** Unique string identifier for the physical sensor device that produced the event.

### [smartbin:eventType](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#eventType)
- **Type:** `xsd:string`
- **Description:** Category of the pipeline event (e.g. `"motion"`).

### [smartbin:sequenceNumber](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#sequenceNumber)
- **Type:** `xsd:integer`
- **Description:** An integer that increases by 1 for every event in a pipeline run. Resets to 1 at the start of each run.

### [smartbin:runId](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#runId)
- **Type:** `xsd:string`
- **Description:** UUID that uniquely identifies a single execution of the producer. All events sharing the same `runId` were produced in the same run.

### [smartbin:pipelineLatencyMs](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#pipelineLatencyMs)
- **Type:** `xsd:float`
- **Description:** Time in milliseconds between the producer publishing the event (`sosa:resultTime`) and the consumer writing it to disk (`smartbin:ingestTime`).

### [smartbin:motionState](https://github.com/konakisnikos/Smart-Wastebin/blob/main/docs/ontology.md#motionState)
- **Type:** `xsd:string`
- **Description:** State of the observed motion at the time of the event. Allowed values: `"detected"`.

