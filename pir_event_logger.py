"""
Smart Wastebin — PIR Event Logger (Milestone 2)

"""

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import click

from wastebinlib.interpreter import PirInterpreter
from wastebinlib.sampler import PirSampler


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@click.command()
@click.option("--pin",             required=True,  type=int,   help="BCM GPIO pin connected to the PIR sensor")
@click.option("--sample-interval", required=True,  type=float, help="Seconds between sensor reads")
@click.option("--duration",        required=True,  type=float, help="Total run duration in seconds")
@click.option("--cooldown",        default=3.0,    type=float, show_default=True, help="Min seconds between emitted events")
@click.option("--min-high",        default=0.2,    type=float, show_default=True, help="Min HIGH duration before emitting an event")
@click.option("--out",  "out_path", required=True, type=click.Path(), help="Output JSONL file path (append mode)")
@click.option("--device-id",       required=True,  type=str,   help="Unique identifier for this sensor")
@click.option("--verbose",         is_flag=True,   help="Print each event to the console")
def main(pin, sample_interval, duration, cooldown, min_high, out_path, device_id, verbose):
    """PIR event logger — reads sensor, writes deposit events to a JSONL file."""

    if sample_interval <= 0:
        click.echo("Error: --sample-interval must be > 0", err=True)
        sys.exit(2)
    if duration <= 0:
        click.echo("Error: --duration must be > 0", err=True)
        sys.exit(2)
    if cooldown < 0:
        click.echo("Error: --cooldown must be >= 0", err=True)
        sys.exit(2)
    if min_high < 0:
        click.echo("Error: --min-high must be >= 0", err=True)
        sys.exit(2)

    try:
        sampler = PirSampler(pin)
    except Exception as exc:
        click.echo(f"Error: Could not initialise PIR on pin {pin}: {exc}", err=True)
        sys.exit(1)

    interp = PirInterpreter(cooldown_s=cooldown, min_high_s=min_high)
    run_id = str(uuid.uuid4())
    seq = 0
    t0 = time.time()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        click.echo(f"[logger] started  pin={pin} interval={sample_interval}s duration={duration}s")

    try:
        with open(out_path, "a", encoding="utf-8") as f:
            while time.time() - t0 < duration:
                now = time.time()
                raw = sampler.read()

                for ev in interp.update(raw, now):
                    seq += 1
                    event_dt = datetime.fromtimestamp(ev["t"], tz=timezone.utc)
                    event_time = event_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                    ingest_time = utc_now_iso()
                    latency_ms = round((time.time() - ev["t"]) * 1000, 1)

                    record = {
                        "event_time":  event_time,
                        "ingest_time": ingest_time,
                        "device_id":   device_id,
                        "event_type":  "motion_detected",
                        "seq":         seq,
                        "run_id":      run_id,
                        "elapsed_s":   round(ev["t"] - t0, 3),
                        "latency_ms":  latency_ms,
                    }

                    f.write(json.dumps(record) + "\n")
                    f.flush()

                    if verbose:
                        click.echo(f"  >> seq={seq} at t={record['elapsed_s']}s latency={latency_ms}ms")

                time.sleep(sample_interval)

    except KeyboardInterrupt:
        click.echo(f"\n[logger] interrupted. wrote {seq} event(s).")
        sys.exit(0)

    if verbose:
        click.echo(f"[logger] done. wrote {seq} event(s) in {duration}s.")


if __name__ == "__main__":
    main()
