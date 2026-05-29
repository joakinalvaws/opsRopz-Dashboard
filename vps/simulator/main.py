"""Simulador de eventos retail — corre en el VPS vía cron cada 5 minutos.

Genera un batch de eventos y los envía a la cola SQS `events` en AWS. En una
empresa real, aquí se conectaría el ERP o POS en lugar del generador.
"""

from __future__ import annotations

import json
import logging
import os
import sys

import boto3

from events import generate_batch

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
_log = logging.getLogger("simulator")


def send_batch(events: list[dict], sqs_client, queue_url: str) -> int:
    """Envía eventos a SQS en lotes de 10 (límite de send_message_batch)."""
    sent = 0
    for i in range(0, len(events), 10):
        chunk = events[i : i + 10]
        entries = [
            {"Id": str(idx), "MessageBody": json.dumps(ev)} for idx, ev in enumerate(chunk)
        ]
        resp = sqs_client.send_message_batch(QueueUrl=queue_url, Entries=entries)
        sent += len(resp.get("Successful", []))
        for failure in resp.get("Failed", []):
            _log.error(json.dumps({"service": "simulator", "level": "ERROR", "failure": failure}))
    return sent


def main() -> None:
    queue_url = os.environ["EVENTS_QUEUE_URL"]
    batch_size = int(os.environ.get("BATCH_SIZE", "10"))
    region = os.environ.get("AWS_REGION", "us-east-1")

    events = generate_batch(batch_size)
    sqs = boto3.client("sqs", region_name=region)
    sent = send_batch(events, sqs, queue_url)
    _log.info(
        json.dumps(
            {
                "service": "simulator",
                "level": "INFO",
                "event_type": "batch_sent",
                "generated": len(events),
                "sent": sent,
            }
        )
    )


if __name__ == "__main__":
    main()
