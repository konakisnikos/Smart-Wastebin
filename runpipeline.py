"""
Smart Wastebin — Modular Pipeline (Milestone 3)

"""

from datetime import datetime, timezone
import json
from queue import Empty, Full, Queue
import threading
import time
from types import SimpleNamespace
import uuid
import click
import sys
from wastebinlib.interpreter import PirInterpreter
from wastebinlib.sampler import PirSampler


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def parse_iso_utc(s: str):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def producer_loop(event_q: Queue,sampler: PirSampler,interp: PirInterpreter,args: SimpleNamespace,metrics: dict,stop_flag: dict):
    run_id = str(uuid.uuid4())
    seq = 0

    while not stop_flag["stop"]:
        now = time.time()
        raw = sampler.read()

        for _ev in interp.update(raw, now):
            seq += 1
            record = {
                "event_time": utc_now_iso(),
                "device_id": args.device_id,
                "event_type": "motion",
                "motion_state": "detected",
                "seq": seq,
                "run_id": run_id,
            }

            try:
                event_q.put_nowait(record)
                metrics["produced"] += 1
            except Full:
                metrics["dropped"] += 1

        metrics["max_queue"] = max(metrics["max_queue"], event_q.qsize())
        time.sleep(args.sample_interval)


def consumer_loop(event_q: Queue, out_path: str, args: SimpleNamespace, metrics: dict, stop_flag: dict) -> None:
    with open(out_path, "a", encoding="utf-8") as f:
        while not stop_flag["stop"] or not event_q.empty():
            try:
                record = event_q.get(timeout=0.5)
            except Empty:
                continue

            try:
                ingest_time = utc_now_iso()
                record["ingest_time"] = ingest_time

                event_dt = parse_iso_utc(record["event_time"])
                ingest_dt = parse_iso_utc(ingest_time)
                latency_ms = (ingest_dt - event_dt).total_seconds() * 1000.0
                record["pipeline_latency_ms"] = latency_ms

                f.write(json.dumps(record) + "\n")
                f.flush()

                metrics["consumed"] += 1
                metrics["max_queue"] = max(metrics["max_queue"], event_q.qsize())
            finally:
                event_q.task_done()

            if args.consumer_delay > 0:
                time.sleep(args.consumer_delay)


@click.command()
@click.option("--pin", required=True, type=int, help="BCM GPIO pin connected to the PIR sensor")
@click.option("--sample-interval", required=True, type=float, help="Seconds between sensor reads")
@click.option("--duration", required=True, type=float, help="Total run duration in seconds")
@click.option("--cooldown", type=float, default=0.0, show_default=True, help="Minimum seconds between emitted motion events")
@click.option("--queue-size", type=int, default=100, show_default=True, help="Maximum number of events to hold in the queue")
@click.option("--consumer-delay", required=True, type=float, help="Delay in seconds between consumer iterations")
@click.option("--min-high", type=float, default=0.0, show_default=True, help="Minimum HIGH duration before emitting an event")
@click.option("--out", "out_path", required=True, type=click.Path(), help="Output file path (append mode, JSONL)")
@click.option("--device-id", required=True, type=str, help="Unique identifier for this sensor/device")
@click.option("--verbose", is_flag=True, help="Print periodic status messages to the console")
def main(pin, sample_interval, duration, cooldown, queue_size, consumer_delay, min_high, out_path, device_id, verbose):
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
        click.echo(f"Runtime Error: Could not initialise PIR sensor on pin {pin}. Details: {exc}", err=True)
        sys.exit(1)

    interp = PirInterpreter(cooldown_s=cooldown, min_high_s=min_high)
    event_q = Queue(maxsize=queue_size)
    stop_flag = {"stop": False}
    metrics = {"produced": 0, "consumed": 0, "dropped": 0, "max_queue": 0}

    args = SimpleNamespace(
        pin=pin,
        sample_interval=sample_interval,
        duration=duration,
        cooldown=cooldown,
        queue_size=queue_size,
        consumer_delay=consumer_delay,
        min_high=min_high,
        out=out_path,
        device_id=device_id,
        verbose=verbose,
    )

    producer_t = threading.Thread(
        target=producer_loop,
        args=(event_q, sampler, interp, args, metrics, stop_flag),
        daemon=True,
    )
    consumer_t = threading.Thread(
        target=consumer_loop,
        args=(event_q, args.out, args, metrics, stop_flag),
        daemon=True,
    )

    producer_t.start()
    consumer_t.start()

    start = time.time()
    try:
        while time.time() - start < duration:
            if args.verbose:
                click.echo(
                    f"[pipeline] produced={metrics['produced']} consumed={metrics['consumed']} "
                    f"dropped={metrics['dropped']} qsize={event_q.qsize()}"
                )
            time.sleep(1.0)
    except KeyboardInterrupt:
        if args.verbose:
            click.echo("\n[pipeline] interrupted by Ctrl-C")
    finally:
        stop_flag["stop"] = True
        producer_t.join()
        consumer_t.join()


if __name__ == "__main__":
    main()
