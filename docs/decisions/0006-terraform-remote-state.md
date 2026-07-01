# 0006 — Estado remoto de Terraform en S3 + locks en DynamoDB

- **Estado**: Aceptada
- **Fecha**: 2026-07-01

## Contexto

La infraestructura de OpsRopz se gestiona por completo con Terraform (57 recursos
AWS). El *state* de Terraform es la fuente de verdad de qué existe en la nube: si
se guarda localmente (`terraform.tfstate` en disco), aparecen tres problemas.

- **No es compartible**: el pipeline de CI/CD (`terraform.yml`) y cualquier otra
  máquina no verían el mismo estado; cada quien recrearía o divergería recursos.
- **Riesgo de corrupción/pérdida**: un archivo local se puede perder o quedar a
  medias si un `apply` se interrumpe.
- **`apply` concurrentes**: dos ejecuciones simultáneas sobre el mismo estado se
  pisan y dejan la infra inconsistente.

## Decisión

Usar un **backend remoto S3 con locking en DynamoDB** (`infra/main.tf`):

1. **State en S3**: bucket `opsropz-tfstate`, key `infra/terraform.tfstate`,
   región `us-east-1`, con `encrypt = true` (cifrado en reposo).
2. **Locks en DynamoDB**: tabla `opsropz-tflocks`. Terraform toma un lock antes de
   cada operación de escritura, evitando `apply` concurrentes.
3. **Bootstrap manual una sola vez**: el bucket y la tabla de locks se crean fuera
   de este Terraform (manualmente o con un workspace de bootstrap) antes del primer
   `terraform init`, porque no pueden gestionar el estado que aún no existe
   (problema del huevo y la gallina).

## Consecuencias

**Positivas**
- Estado único, compartido y versionado entre desarrollo local y CI/CD.
- Cifrado en reposo y bloqueo que impide corrupción por ejecuciones simultáneas.
- Base para trabajar en equipo y para automatizar despliegues (ver
  [0007-terraform-cd-manual](0007-terraform-cd-manual.md)).

**Negativas**
- Cualquier operación —incluido `terraform plan`— requiere credenciales AWS para
  leer el state remoto; no se puede planificar totalmente offline.
- Hay un paso de bootstrap previo fuera de Terraform (crear bucket + tabla), que
  debe documentarse para reproducir el entorno desde cero.
