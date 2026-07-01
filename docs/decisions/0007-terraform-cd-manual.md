# 0007 — CD de infraestructura con apply manual (workflow_dispatch)

- **Estado**: Aceptada
- **Fecha**: 2026-07-01

## Contexto

El código de las Lambdas se empaqueta y despliega con el propio Terraform
(`archive_file`), así que aplicar la infraestructura también despliega el código
nuevo. La pregunta es **cómo disparar ese `apply` desde GitHub Actions**.

Un CD totalmente automático (aplicar en cada push a `main`) tiene dos costos
concretos en este proyecto:

- **Credenciales AWS permanentes en GitHub**: exige guardar llaves de larga vida
  como secrets, ampliando la superficie de exposición.
- **Despliegues no intencionados**: cualquier merge tocaría infraestructura de
  producción sin una revisión humana explícita del `plan`.

## Decisión

CD de infra con **disparo manual** (`.github/workflows/terraform.yml`):

1. **`workflow_dispatch`** desde la pestaña Actions, no en cada push.
2. **Plan por defecto, apply opt-in**: un input booleano `apply` (default `false`).
   El workflow siempre corre `terraform plan`; solo ejecuta `terraform apply
   -auto-approve` si quien lo dispara marca `apply = true`.
3. **Credenciales vía secrets** (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) por
   ahora, con **OIDC** (`role-to-assume`) señalado como la evolución preferida para
   producción, para eliminar las llaves de larga vida.

Complementa a la separación de responsabilidades del CI (`ci.yml`), que sí corre
en cada push pero se limita a `terraform fmt`/`validate` sin tocar la nube.

## Consecuencias

**Positivas**
- Control humano sobre cada despliegue de infraestructura: se revisa el `plan`
  antes de aplicar.
- Menor exposición: no hace falta habilitar credenciales AWS activas en cada push;
  el `apply` es un acto deliberado.
- Camino de mejora claro y documentado (migrar a OIDC).

**Negativas**
- El despliegue no es totalmente automático: hay un paso manual en la pestaña
  Actions, con la latencia operativa que eso implica.
- Con secrets estáticos, la seguridad depende de rotarlos; la mitigación real
  (OIDC) queda como trabajo pendiente.
