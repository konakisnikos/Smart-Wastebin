# Smart-Wastebin

A Raspberry Pi–based smart waste bin that uses an HC-SR501 PIR sensor to
detect when trash is thrown into the bin. Each deposit triggers a motion
event that is timestamped and logged, enabling usage tracking and
data-driven waste collection management.

---

## Team

| Name | GitHub |
|---|---|
| Nikos Konakis | [@konakisnikos](https://github.com/konakisnikos) |
| Giannis Giannakouras | [@Giannak19](https://github.com/Giannak19) |
| Vasilis Sokos | [@VasiliosSokos](https://github.com/VasiliosSokos) |

---

## Architecture

```
HC-SR501 (GPIO 17)
      │
      ▼
 producer thread        ← sensing: reads sensor, interprets samples
      │
      ▼
   Queue (in-memory)    ← buffering: decouples sensing from output
      │
      ▼
 consumer thread        ← output: writes JSON-LD events to JSONL file
      │
      ▼
 /data/events.jsonl
```

---

## Project Structure

```
Smart-Wastebin/
├── wastebinlib/
│   ├── __init__.py
│   ├── sampler.py              # reads raw HIGH/LOW from the PIR sensor
│   └── interpreter.py          # debounces samples into clean motion events
├── models/                     # Milestone 5: JSON-LD semantic models
│   ├── context.jsonld          #   field → IRI mappings for pipeline events
│   ├── sensor.jsonld           #   HC-SR501 sensor entity
│   ├── wastebin.jsonld         #   smart bin entity
│   └── environment.jsonld      #   deployment zone and spaces
├── docs/
│   └── ontology.md             # custom smartbin: namespace definitions
├── pir_event_logger.py         # Milestone 2: single-loop event logger
├── run_pipeline.py             # Milestone 3–5: modular pipeline, JSON-LD output
├── Dockerfile                  # Milestone 4: container image
├── docker-compose.yml          # Milestone 4: orchestrates the pipeline service
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Hardware

### Components

| Component | Details |
|---|---|
| Board | Raspberry Pi (any model with GPIO headers) |
| Sensor | HC-SR501 PIR motion sensor |

### Wiring

| PIR Pin | Pi Pin | Description |
|---|---|---|
| VCC | Pin 2 (5V) | Power |
| GND | Pin 6 (GND) | Ground |
| OUT | Pin 11 (GPIO 17) | Signal |

> The HC-SR501 needs a 30–60 second warm-up after power-on before it produces stable readings.

---

## Running with Docker (recommended)

```bash
git clone https://github.com/konakisnikos/Smart-Wastebin.git
cd Smart-Wastebin

docker compose up
```

Events are written to a Docker volume (`pipeline-data`) and persist across restarts. To inspect them:

```bash
docker exec smart-wastebin-pir-pipeline-1 tail -f /data/events.jsonl
```

To stop:

```bash
docker compose down
```

---

## Running manually (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python run_pipeline.py \
  --pin 17 \
  --sample-interval 0.1 \
  --duration 86400 \
  --cooldown 2.0 \
  --min-high 0.3 \
  --queue-size 20 \
  --consumer-delay 0.0 \
  --out output/events.jsonl \
  --device-id pir-01 \
  --verbose
```

---

## Event Format

Each line in `events.jsonl` is a self-describing JSON-LD observation:

```json
{
  "@context": "https://raw.githubusercontent.com/konakisnikos/Smart-Wastebin/main/models/context.jsonld",
  "@type": "sosa:Observation",
  "@id": "urn:dev:pir-sensor-smartbin:obs:<run_id>:<seq>",
  "event_time": "2026-04-24T10:15:30.512Z",
  "device_id": "pir-01",
  "event_type": "motion",
  "motion_state": "detected",
  "seq": 1,
  "run_id": "<uuid>",
  "ingest_time": "2026-04-24T10:15:30.519Z",
  "pipeline_latency_ms": 7.0
}
```

The `@context` maps each field to a globally understood IRI — `event_time` expands to `sosa:resultTime`, `seq` to `smartbin:sequenceNumber`, and so on. See [docs/ontology.md](docs/ontology.md) for the full custom namespace.

---

## Entity Models

| File | Describes |
|---|---|
| [models/sensor.jsonld](models/sensor.jsonld) | HC-SR501 PIR sensor (`sosa:Sensor`) |
| [models/wastebin.jsonld](models/wastebin.jsonld) | Smart waste bin (`sosa:FeatureOfInterest`) |
| [models/environment.jsonld](models/environment.jsonld) | Deployment zone and spaces (`bot:Zone`, `bot:Space`) |
| [models/context.jsonld](models/context.jsonld) | Shared `@context` for all pipeline events |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| gpiozero | 2.0.1 | GPIO access |
| rpi-lgpio | 0.6 | lgpio backend required inside the Docker container |
| click | 8.1.8 | CLI argument parsing |
