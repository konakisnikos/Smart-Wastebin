"""
Smart Wastebin — Modular Pipeline (Milestone 5)

Same producer/queue/consumer architecture as Milestone 3, with one change:
each event is now a self-describing JSON-LD observation mapped to standard
vocabularies (SOSA, schema.org) via a shared @context.
"""

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Thread
from types import SimpleNamespace

import click

from wastebinlib.interpreter import PirInterpreter
from wastebinlib.sampler import PirSampler

CONTEXT_URL = (
    "https://raw.githubusercontent.com/konakisnikos/Smart-Wastebin/main/models/context.jsonld"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso_utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Producer — senses and enqueues JSON-LD observations
# ---------------------------------------------------------------------------

def producer_loop(
    event_q: Queue,
    sampler: PirSampler,
    interp: PirInterpreter,
    args: SimpleNamespace,
    metrics: dict,
    stop_flag: dict,
) -> None:
    run_id = str(uuid.uuid4())
    seq = 0

    while not stop_flag["stop"]:
        now = time.time()
        raw = sampler.read()

        for _ev in interp.update(raw, now):
            seq += 1
            event_dt = datetime.fromtimestamp(now, tz=timezone.utc)
            event_time = event_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

            record = {
                "@context":    CONTEXT_URL,
                "@type":       "sosa:Observation",
                "@id":         f"urn:dev:pir-sensor-smartbin:obs:{run_id}:{seq}",
                "event_time":  event_time,
                "device_id":   args.device_id,
                "event_type":  "motion",
                "motion_state": "detected",
                "seq":         seq,
                "run_id":      run_id,
            }

            try:
                event_q.put_nowait(record)
                metrics["produced"] += 1
            except Full:
                metrics["dropped"] += 1

        metrics["max_queue"] = max(metrics["max_queue"], event_q.qsize())
        time.sleep(args.sample_interval)


# ---------------------------------------------------------------------------
# Consumer — dequeues and writes
# ---------------------------------------------------------------------------

def consumer_loop(
    event_q: Queue,
    out_path: str,
    args: SimpleNamespace,
    metrics: dict,
    stop_flag: dict,
) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "a", encoding="utf-8") as f:
        while not stop_flag["stop"] or not event_q.empty():
            try:
                record = event_q.get(timeout=3.0)
            except Empty:
                continue

            try:
                ingest_time = utc_now_iso()
                record["ingest_time"] = ingest_time

                event_dt = parse_iso_utc(record["event_time"])
                ingest_dt = parse_iso_utc(ingest_time)
                record["pipeline_latency_ms"] = round(
                    (ingest_dt - event_dt).total_seconds() * 1000.0, 1
                )

                f.write(json.dumps(record) + "\n")
                f.flush()
                metrics["consumed"] += 1
                metrics["max_queue"] = max(metrics["max_queue"], event_q.qsize())

            finally:
                event_q.task_done()

            if args.consumer_delay > 0:
                time.sleep(args.consumer_delay)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option("--pin",             required=True,  type=int,   help="BCM GPIO pin connected to the PIR sensor")
@click.option("--sample-interval", required=True,  type=float, help="Seconds between sensor reads")
@click.option("--duration",        required=True,  type=float, help="Total run duration in seconds")
@click.option("--cooldown",        default=3.0,    type=float, show_default=True, help="Min seconds between emitted events")
@click.option("--min-high",        default=0.2,    type=float, show_default=True, help="Min HIGH duration before emitting an event")
@click.option("--queue-size",      default=100,    type=int,   show_default=True, help="Max events held in the queue")
@click.option("--consumer-delay",  required=True,  type=float, help="Artificial delay between consumer iterations (seconds)")
@click.option("--out",  "out_path", required=True, type=click.Path(), help="Output JSONL file path (append mode)")
@click.option("--device-id",       required=True,  type=str,   help="Sensor identifier, e.g. pir-01")
@click.option("--verbose",         is_flag=True,   help="Print periodic pipeline status to console")
def main(pin, sample_interval, duration, cooldown, min_high, queue_size, consumer_delay, out_path, device_id, verbose):
    """Modular PIR pipeline — produces JSON-LD observations via producer/queue/consumer."""

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
    if queue_size <= 0:
        click.echo("Error: --queue-size must be > 0", err=True)
        sys.exit(2)
    if consumer_delay < 0:
        click.echo("Error: --consumer-delay must be >= 0", err=True)
        sys.exit(2)

    try:
        sampler = PirSampler(pin)
    except Exception as exc:
        click.echo(f"Error: Could not initialise PIR on pin {pin}: {exc}", err=True)
        sys.exit(1)

    interp = PirInterpreter(cooldown_s=cooldown, min_high_s=min_high)
    event_q = Queue(maxsize=queue_size)
    stop_flag = {"stop": False}
    metrics = {"produced": 0, "consumed": 0, "dropped": 0, "max_queue": 0}

    args = SimpleNamespace(
        sample_interval=sample_interval,
        consumer_delay=consumer_delay,
        device_id=device_id,
    )

    producer_t = Thread(target=producer_loop, args=(event_q, sampler, interp, args, metrics, stop_flag), daemon=True)
    consumer_t = Thread(target=consumer_loop, args=(event_q, out_path, args, metrics, stop_flag), daemon=True)

    producer_t.start()
    consumer_t.start()

    start = time.time()
    try:
        while time.time() - start < duration:
            if verbose:
                click.echo(
                    f"[pipeline] produced={metrics['produced']} "
                    f"consumed={metrics['consumed']} "
                    f"dropped={metrics['dropped']} "
                    f"qsize={event_q.qsize()}"
                )
            time.sleep(1.0)
    except KeyboardInterrupt:
        if verbose:
            click.echo("\n[pipeline] interrupted.")
    finally:
        stop_flag["stop"] = True
        producer_t.join()
        consumer_t.join()

    if verbose:
        click.echo(
            f"[pipeline] done. produced={metrics['produced']} "
            f"consumed={metrics['consumed']} dropped={metrics['dropped']}"
        )


if __name__ == "__main__":
    main()
