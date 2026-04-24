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
 consumer thread        ← output: writes events to JSONL file
      │
      ▼
 output/events.jsonl
```

---

## Project Structure

```
Smart-Wastebin/
├── wastebinlib/
│   ├── __init__.py
│   ├── sampler.py          # reads raw HIGH/LOW from the PIR sensor
│   └── interpreter.py      # debounces samples into clean motion events
├── pir_event_logger.py     # Milestone 2: single-loop event logger
├── run_pipeline.py         # Milestone 3: modular producer/queue/consumer pipeline
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

## Setup

**Prerequisites:** Python 3.9 or newer, Git, Raspberry Pi with the sensor wired up.

```bash
# 1. Clone the repository
git clone https://github.com/konakisnikos/Smart-Wastebin.git
cd Smart-Wastebin

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

```bash
python run_pipeline.py \
  --pin 17 \
  --sample-interval 0.1 \
  --duration 86400 \
  --cooldown 2.0 \
  --min-high 0.2 \
  --queue-size 20 \
  --consumer-delay 0.0 \
  --out output/events.jsonl \
  --device-id pir-01 \
  --verbose
```

| Option | Description |
|---|---|
| `--pin` | BCM GPIO pin connected to the PIR sensor |
| `--sample-interval` | Seconds between sensor reads |
| `--duration` | Total run duration in seconds |
| `--cooldown` | Minimum seconds between emitted events |
| `--min-high` | Minimum HIGH duration before emitting an event |
| `--queue-size` | Maximum events held in the internal queue |
| `--consumer-delay` | Artificial delay between consumer iterations |
| `--out` | Output JSONL file (append mode) |
| `--device-id` | Unique identifier for this sensor |
| `--verbose` | Print pipeline status to the console |

### Example output (`events.jsonl`)

```json
{"event_time": "2026-04-24T10:15:30.512Z", "device_id": "pir-01", "event_type": "motion", "motion_state": "detected", "seq": 1, "run_id": "a1b2c3d4-...", "ingest_time": "2026-04-24T10:15:30.519Z", "pipeline_latency_ms": 7.0}
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| gpiozero | 2.0.1 | GPIO access |
| click | 8.1.8 | CLI argument parsing |
