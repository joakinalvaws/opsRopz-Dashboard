# Simulador de eventos retail

Genera eventos retail realistas y los envía a la cola SQS `events`. Corre en el
VPS Hostinger vía cron cada 5 minutos. Sustituible por un ERP/POS real.

## Archivos

| Archivo | Rol |
|---|---|
| `events.py` | Generación pura de eventos (testeable con semilla). |
| `main.py` | Entry point: genera batch + envía a SQS. |

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `EVENTS_QUEUE_URL` | URL de la cola SQS (output de Terraform) | — (obligatoria) |
| `BATCH_SIZE` | Eventos por ejecución | `10` |
| `AWS_REGION` | Región AWS | `us-east-1` |

## Ejecución local

```bash
pip install -r requirements.txt
export EVENTS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/<acct>/opsropz-events-dev"
python main.py
```

## Cron en el VPS

```cron
# /etc/cron.d/opsropz-simulator — cada 5 minutos
*/5 * * * * opsropz cd /opt/opsropz/simulator && \
  EVENTS_QUEUE_URL="..." /opt/opsropz/venv/bin/python main.py >> /var/log/opsropz-sim.log 2>&1
```
