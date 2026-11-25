# Evidencias reales del Hito 3

**No son resultados ejecutados ni capturas de ejemplo.** Rellenar tras operar en la cuenta cloud propia.

Colocar aquí imágenes PNG de la consola de AWS y las trazas de Terraform **revisadas para no incluir credenciales, nombres de cuentas privadas ni contenido sensible del estado**.

Propuesta de nombres:

1. `01-terraform-validate.png` — validación local.
2. `02-apply-inicial.png` — creación de recursos.
3. `03-aws-ec2-antes.png` — etiqueta `DriftDemo=terraform-managed`.
4. `04-aws-drift-manual.png` — edición manual de esa etiqueta a `modificado-manualmente`.
5. `05-plan-drift.png` — diferencia detectada por `terraform plan`.
6. `06-apply-reconcile.png` — corrección aplicada.
7. `07-aws-ec2-despues.png` — etiqueta restaurada.
8. `08-locking.png` — bloqueo real del backend S3.
9. `09-destroy.png` — `Destroy complete!`.
10. `10-sin-recursos.png` — comprobación en AWS de recursos gestionados eliminados.

Guardar extractos saneados de la salida en `observaciones.md` (plantilla inferior) y anotar la fecha exacta, zona, identificadores anonimizados si procede, y qué demuestra cada figura.

**No versionar** archivos `.tfstate`, `.tfplan`, `.env`, claves, `backend.hcl` ni `terraform.tfvars`.
