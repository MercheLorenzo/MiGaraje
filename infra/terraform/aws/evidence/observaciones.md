# Bitácora de experimentos (PENDIENTE DE REALIZACIÓN)

> Sustituir los campos `[PENDIENTE]` solo después de ejecutar cada acción en tu AWS. No presentar como evidencia un comando que no se haya ejecutado.

- Fecha y hora (Europe/Madrid, hora de la alumna): [PENDIENTE]
- Región y zona: eu-north-1 / [zona AZ pendiente]
- Rama y commit desplegado: [PENDIENTE]
- Cuenta cloud (sin incluir secretos): [PENDIENTE]
- Bucket state (opcional, anonimizado): [PENDIENTE]

## Estado inicial

Comandos `terraform init -backend-config=backend.hcl`, `terraform validate`, `terraform plan -out=...`, `terraform apply ...`, `terraform output`: [TRAZAS SANITIZADAS PENDIENTES]

Capturas: `01-terraform-validate.png`, `02-apply-inicial.png`, `03-aws-ec2-antes.png`.

## Drift inducido

- Recurso: etiqueta `DriftDemo` de EC2
- Esperado (`main.tf`/módulo): `terraform-managed`
- Valor manual: `modificado-manualmente`
- Procedimiento usado: [AWS Console / AWS CLI y prueba de modificación]
- Captura: `04-aws-drift-manual.png`

## Detección

`terraform plan` sin `-refresh=false` debe mostrar `DriftDemo = "modificado-manualmente" -> "terraform-managed"` para la EC2. Incluir salida REAL y explicación de qué atributo cambió. Captura: `05-plan-drift.png`.

## Reconciliación

`terraform apply` sobre plan nuevo y verificación desde AWS Console. Capturas: `06-apply-reconcile.png`, `07-aws-ec2-despues.png`.

## Bloqueo del estado

Prueba de dos terminales (una sesión `apply` reteniendo bloqueo durante la confirmación y otra `plan -lock-timeout=5s`). Anotar resultado real y cómo se liberó el bloqueo: [PENDIENTE]. Captura `08-locking.png`.

## Destroy y coste

- Comando: `terraform destroy -var-file=terraform.tfvars`.
- Resultado: [PENDIENTE]
- `terraform state list` (debe ser vacío): [PENDIENTE]
- Comprobación AWS EC2/VPC/EBS: [PENDIENTE]
- Recursos residuales: bucket S3/versiones de estado; [otros si los hay]
- Capturas: `09-destroy.png`, `10-sin-recursos.png`.
