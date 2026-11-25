# MiGaraje — Guía paso a paso Hito 3 en AWS (Estocolmo)

**Estado:** código preparado y revisado; **el despliegue AWS y las evidencias están pendientes de ejecutarse**.  
**Cuenta:** nuevo AWS Free Plan, proyecto «Array of Sunshine».  
**Región única:** `eu-north-1` (Stockholm / Estocolmo, Suecia, UE).  
**Rama de trabajo:** `feature/hito3-terraform`.

> **ALERTA DE COSTES:** no ejecutes `terraform apply` antes de comprobar saldo, presupuesto, permisos, elegibilidad Free Tier y el resultado exacto del `plan`. AWS Free Plan limita el cobro ordinario mientras esté activo, pero consume créditos y puede suspender el proyecto al agotarse. No actives un Paid Plan ni características avanzadas. El objetivo de esta práctica es no desembolsar dinero.

## Arquitectura elegida

- `modules/network`: VPC, subred pública con Internet Gateway y subred privada **aislada**, tablas de rutas y Security Group. Por defecto **0 entradas**: no se exponen ni SSH ni PostgreSQL.
- `modules/compute`: Ubuntu 24.04 x86_64, rol IAM de SSM y EC2 `m7i-flex.large` como **candidata**, no como disponibilidad garantizada. `m7i-flex.large` figura entre los tipos elegibles de AWS Free Tier para cuentas nuevas (ver enlace oficial al final). Se utiliza SSM para acceso sin SSH.
- `modules/storage`: EBS gp3 cifrado para persistir Docker/PostgreSQL. El root EBS también está cifrado.
- PostgreSQL con 5 bases de datos lógicas y 6 APIs FastAPI + Nginx dentro de Docker Compose. La subred privada no aloja la BD en esta fase.
- S3 privado/versiónado para `terraform.tfstate` y `.tflock` con `use_lockfile=true` (bloqueo). Este bucket se gestiona **por fuera de Terraform**, para impedir que el estado se destruya a sí mismo.

Las variables usadas por defecto limitan `aws_region` a `eu-north-1`; cualquier intento de usar Madrid debe fallar en validación. No uses secretos ni contraseñas de tu Windows en AWS: el bootstrap genera claves diferentes dentro de EC2, en el EBS cifrado.

---

## Paso 0 — Preparación (sin crear recursos)

### 0.1. Comprobar herramientas en PowerShell

Desde `C:\Users\ASUS\Documents\MiGaraje`:

```powershell
terraform version
aws --version
session-manager-plugin
```

Terraform >=1.11, AWS CLI v2 y Session Manager plugin. Si el último comando muestra un mensaje de instalación, es suficiente; si dice «no se reconoce», instala el plugin desde la documentación de AWS.

### 0.2. Configurar sesión AWS temporal

Ya autenticada la cuenta con `aws login` (sin SSO). Si la sesión caduca, repite:

```powershell
aws login --profile migaraje-lab
aws configure set region eu-north-1 --profile migaraje-lab
$env:AWS_PROFILE = 'migaraje-lab'
$env:AWS_DEFAULT_REGION = 'eu-north-1'
aws sts get-caller-identity
aws configure get region --profile migaraje-lab
```

El resultado de la región debe ser **`eu-north-1`**. No pegues tokens, claves privadas ni URLs temporales de autenticación en el repositorio.

### 0.3. Asegurar la rama y publicar el código antes del despliegue

```powershell
git branch --show-current
git status
```

Debe ser `feature/hito3-terraform`. Copia la actualización del ZIP, revisa con `git diff` y `git status`. Antes de desplegar, publica la rama y usa `repository_ref = "feature/hito3-terraform"` en tu `terraform.tfvars`: EC2 **clona GitHub**, no los archivos locales. Si los cambios no están en GitHub, el servidor descargará una versión anterior o fallará.

```powershell
git add .gitignore README.md docs/HITO3.md infra/terraform/aws .github/workflows/terraform.yml scripts/test_hito3_structure.py
git diff --cached --stat
git commit -m "feat(iac): preparar Terraform AWS en Estocolmo y documentación del Hito 3"
git push -u origin feature/hito3-terraform
```

Si un archivo no existe o ya está en commits anteriores, ajústalo según `git status`. Comprueba que ningún archivo `terraform.tfvars`, `.env`, `backend.hcl`, `*.tfstate` o `*.tfplan` quede en staging.

### 0.4. Confirmar plan gratuito y presupuesto en AWS Console

1. En **AWS Settings → Billing / Projects**, confirma **Free Plan**, los créditos disponibles, fecha de fin y región del proyecto.
2. En **Billing and Cost Management → Budgets**, crea un presupuesto mensual pequeño (por ejemplo 5 USD) con aviso por correo y verifica el email. **Un presupuesto alerta, no detiene los recursos.** El consumo se verá antes de aplicar créditos.
3. Comprueba en el panel de EC2 de `eu-north-1` que la cuenta puede usar instancias elegibles. No pulses Launch Instance: Terraform creará la VM después.
4. No actives Paid Plan, ni Advanced Features, ni NAT Gateway, RDS o balanceadores para este laboratorio.

### 0.5. Ejecutar preflight: NO CREA recursos

```powershell
cd C:\Users\ASUS\Documents\MiGaraje\infra\terraform\aws
.\scripts\preflight-free-plan.ps1 -Profile migaraje-lab -Region eu-north-1 -InstanceType m7i-flex.large
```

Debe poder ejecutar AWS STS, verificar la región, confirmar `FreeTierEligible = True` y comprobar que el tipo aparece en la región. **Esto no asegura stock en una zona de disponibilidad ni permisos IAM/EC2 para crear.** Si falla, detente y analiza el error; no cambies a un tipo de instancia no elegible para sortear el problema. La otra candidata admitida por esta plantilla es `c7i-flex.large` (4 GiB, menos adecuada para construir todos los contenedores).

**Comprobación Terraform sin cloud:** puedes ejecutar `terraform init -backend=false` y `terraform validate` después de configurar `terraform.tfvars`; esto no crea recursos, pero descargará el plugin de Terraform. Se recomienda esperar a Paso 2 para inicializar una sola vez con backend remoto.

---

## Paso 1 — Crear backend S3 privado (primera acción que crea recursos)

El bucket S3 consume créditos según objetos/operaciones. Solo continúa cuando hayas comprobado la cuenta, el presupuesto y el preflight.

```powershell
cd C:\Users\ASUS\Documents\MiGaraje\infra\terraform\aws
$env:AWS_PROFILE = 'migaraje-lab'
$env:AWS_DEFAULT_REGION = 'eu-north-1'
$account = (aws sts get-caller-identity --query Account --output text).Trim()
$bucket = "migaraje-hito3-state-${account}-eu-north-1"
.\scripts\bootstrap-state.ps1 -BucketName $bucket -Region eu-north-1
```

El script crea o verifica un bucket, bloquea acceso público, activa versionado y SSE-S3, y genera **`backend.hcl` local ignorado**. Para confirmar la región:

```powershell
aws s3api get-bucket-location --bucket $bucket --query LocationConstraint --output text
aws s3api get-public-access-block --bucket $bucket
aws s3api get-bucket-versioning --bucket $bucket
aws s3api get-bucket-encryption --bucket $bucket
```

Si AWS rechaza la creación por las restricciones del proyecto Free Plan o por permisos, **no crees recursos en otra región ni actives Paid Plan**. Guarda el error para revisarlo. El archivo `backend-state-iam-policy.example.json` ilustra el mínimo privilegio para S3; su aplicación efectiva dependerá de las restricciones y la identidad del proyecto.

**Si ya existe `backend.hcl` o un estado anterior:** revisa su región y contenido antes de ejecutar el bootstrap. No cambies un backend con recursos existentes por otro sin una migración del estado explícita.

## Paso 2 — Inicializar, validar y planificar

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

Verifica al menos:

```hcl
aws_region        = "eu-north-1"
instance_type     = "m7i-flex.large"
repository_ref    = "feature/hito3-terraform"  # Ya publicada y accesible en GitHub
trusted_ipv4_cidr = null
```

`terraform.tfvars` no se sube al repositorio. Configura `availability_zone` **solo si la zona por defecto no ofrece capacidad**, nunca como paso inicial. Luego:

```powershell
terraform fmt -recursive
terraform init -backend-config=backend.hcl
terraform validate
terraform plan -var-file=terraform.tfvars -out=terraform.tfplan
terraform show terraform.tfplan
```

**Punto de control imprescindible:** revisa los recursos y costes de EC2, discos, IPv4 pública, S3 y tráfico. Terraform **no proporciona una estimación de precio fiable con `plan`**: usa también AWS Pricing Calculator y el estado de créditos de tu cuenta. Si el plan falla por denegación del Free Plan, no intentes evitar los controles. Guarda salida/capturas de `validate` y del plan. No publiques `terraform.tfplan` ni el estado remoto.

## Paso 3 — Aplicar, SOLO tras comprobar créditos/permisos/costes

```powershell
terraform apply terraform.tfplan
terraform output
$id = terraform output -raw instance_id
aws ec2 describe-instances --instance-ids $id --region eu-north-1 --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,Placement.AvailabilityZone]' --output table
```

Guarda capturas de `Apply complete!`, VPC, subredes, EC2, SG y EBS. Que Terraform termine no significa que Docker haya terminado la instalación. El arranque de Ubuntu instala Docker, clona la rama publicada y ejecuta `docker compose up -d --build --wait frontend-production` con límite de paralelismo.

### 3.1. Comprobar el servidor por SSM

```powershell
aws ssm describe-instance-information --region eu-north-1
aws ssm start-session --target $id --region eu-north-1
```

En la terminal Linux remota (no en PowerShell Windows):

```bash
sudo cloud-init status --wait
sudo tail -n 120 /var/log/migaraje-bootstrap.log
cd /opt/migaraje/app
sudo docker compose ps -a
sudo docker info --format '{{.DockerRootDir}}'
sudo docker volume inspect migaraje_postgres_data
curl -f http://127.0.0.1:8081/
curl -f http://127.0.0.1:8090/health/ready
```

El data-root de Docker debe ser `/mnt/migaraje-data/docker`; así PostgreSQL queda en el EBS cifrado. El servidor comienza con BBDD vacías: **no migramos tu base de Windows automáticamente**. Si falla el bootstrap, guarda el log, no borres el volumen ni reintentes `apply` a ciegas. Si SSM rechaza conexión, revisar IAM/SSM agent y políticas de tu proyecto.

### 3.2. Acceder desde navegador sin exponer puertos

Abre **otra ventana PowerShell local**, sin cerrar el túnel:

```powershell
cd C:\Users\ASUS\Documents\MiGaraje\infra\terraform\aws
$env:AWS_PROFILE = 'migaraje-lab'
$id = terraform output -raw instance_id
aws ssm start-session --target $id --region eu-north-1 --document-name AWS-StartPortForwardingSession --parameters 'portNumber=8081,localPortNumber=18081'
```

Abre `http://localhost:18081`. Para Swagger, en **otra** ventana PowerShell inicia:

```powershell
aws ssm start-session --target $id --region eu-north-1 --document-name AWS-StartPortForwardingSession --parameters 'portNumber=8090,localPortNumber=18090'
```

Abre `http://localhost:18090/docs`. Se usan 18081/18090 para no interferir con Docker local 8081/8090. Prueba login, un vehículo ficticio, un mantenimiento, estadísticas y permisos de admin (sin datos reales). **No abras HTTP público sin HTTPS**.

## Paso 4 — Experimento de drift (Reconciler Pattern)

1. **Estado deseado:** `modules/compute/main.tf` declara `DriftDemo = "terraform-managed"`. Verifica en AWS EC2 → Instances → Tags y guarda captura `01-aws-estado-inicial.png`.
2. **Drift manual:** cambia SOLO la etiqueta a `modificado-manualmente` desde consola EC2 → Tags → Manage tags. Captura `02-drift-manual.png`.
3. **Observación:** en PowerShell local:

   ```powershell
   terraform plan -var-file=terraform.tfvars
   ```

   Debe aparecer una diferencia de etiqueta indicando que Terraform quiere restablecer `terraform-managed`. Guarda traza real y captura `03-plan-drift.png`.
4. **Reconciliación:**

   ```powershell
   terraform apply -var-file=terraform.tfvars
   terraform plan -var-file=terraform.tfvars
   ```

   Revisa el plan, acepta solo la restauración esperada y verifica que ya no hay cambios. Guarda `04-apply-reconcile.png` y `05-sin-drift.png`.

**Nota técnica:** Terraform no vigila continuamente la infraestructura; el patrón de reconciliación se demuestra al invocar `plan` y `apply`.

## Paso 5 — Demostrar bloqueo de estado remoto

Tras inducir nuevamente un cambio seguro de etiqueta, abre dos terminales autenticadas en el MISMO directorio con el MISMO backend.

**Terminal 1:**

```powershell
terraform apply -var-file=terraform.tfvars
```

Mantén el plan esperando la confirmación sin escribir `yes`.

**Terminal 2:**

```powershell
terraform plan -var-file=terraform.tfvars -lock-timeout=5s
```

Si se mantiene el lock, la segunda verá un error de adquisición. Captura el resultado real. En terminal 1 escribe `no` para liberar el bloqueo y luego ejecuta un único `terraform apply` para reconciliar. Si Terraform no mantuvo el lock durante la pregunta, **no afirmes que lo demostraste**; vuelve a intentar en un experimento controlado. Nunca uses `-lock=false` ni fuerces un unlock por conveniencia.

## Paso 6 — Teardown (obligatorio, sin dejar recursos consumiendo créditos)

**Aviso:** `terraform destroy` elimina EC2 y el EBS. Primero exporta los datos si necesitas conservarlos. Si tienes sesiones SSM abiertas, cierra los túneles. En la sesión Linux:

```bash
cd /opt/migaraje/app
sudo docker compose down
sudo systemctl stop docker.service docker.socket
sudo umount /mnt/migaraje-data
exit
```

En PowerShell local:

```powershell
terraform plan -destroy -var-file=terraform.tfvars
terraform destroy -var-file=terraform.tfvars
terraform state list
```

El estado debe estar vacío. Guarda `Destroy complete!` y capturas de EC2/VPC/EBS. Si `destroy` falla, **no borres manualmente recursos gestionados sin primero analizar el estado**, para no producir deriva o perder datos.

### 6.1. Limpieza posterior del backend S3 (separado)

S3 **NO** se destruye con Terraform. Tras guardar evidencias y cuando no vayas a usar ese backend en otra sesión, en la consola S3 selecciona el bucket, elimina todos los objetos **y todas sus versiones/delete markers** y finalmente elimina el bucket. Verifica que ha desaparecido. Revisa Billing/Free Tier en AWS Settings. Si piensas continuar con Hito 4, puedes conservar el backend, pero recuerda que el almacenamiento puede consumir crédito mientras exista.

## Paso 7 — Evidencias para la entrega

Completar [`evidence/observaciones.md`](evidence/observaciones.md) con fechas y comandos **realmente ejecutados**. Capturas mínimas: configuración de backend S3 privado, `validate`, `apply`, VPC/subredes/SG, EC2/EBS y Docker saludable, etiqueta antes/después, `plan` detectando drift, reconciliación, locking, `destroy` y recursos ya eliminados. Ocultar en todas las capturas datos sensibles, tokens y contenidos del `.env`.

Al cerrar los experimentos y documentar resultados, cerrar las issues #22–#27. Abrir PR `feature/hito3-terraform` → `main` solo cuando `terraform validate` y las verificaciones reales estén completadas.

## Referencias oficiales

- [Guion universitario Hito 3](https://github.com/cvillalonga/CC-26-27/blob/main/hitos/hito3.md)
- [Instancias elegibles para EC2 Free Tier](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
- [Preguntas sobre Free Plan y créditos](https://aws.amazon.com/free/free-tier-faqs/)
- [Terraform backend S3 y lockfile](https://developer.hashicorp.com/terraform/language/backend/s3)
- [AWS Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Calculadora de costes AWS](https://calculator.aws/)
