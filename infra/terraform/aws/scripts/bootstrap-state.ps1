#requires -Version 5.1
<#
Crear bucket S3 exclusivo para el estado de MiGaraje.
Usa las credenciales que AWS CLI ya tenga configuradas (AWS_PROFILE o SSO).
No guarda ni solicita access keys en el repositorio.
#>
param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9][a-z0-9.-]{3,60}[a-z0-9]$')][string]$BucketName,
  [string]$Region = 'eu-north-1'
)
$ErrorActionPreference='Stop'
if ($Region -ne 'eu-north-1') { throw 'Región no admitida en este proyecto: utiliza eu-north-1.' }
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw 'Instala AWS CLI v2 y autentícate antes de continuar.' }

aws sts get-caller-identity --query Account --output text
if ($LASTEXITCODE -ne 0) { throw 'AWS CLI no está autenticado. Comprueba AWS_PROFILE / aws sso login.' }

$headExit = 1
try {
  aws s3api head-bucket --bucket $BucketName 2>$null | Out-Null
  $headExit = $LASTEXITCODE
} catch { $headExit = 1 }
if ($headExit -eq 0) {
  $actualLocation = (aws s3api get-bucket-location --bucket $BucketName --query LocationConstraint --output text).Trim()
  if ($LASTEXITCODE -ne 0 -or $actualLocation -ne $Region) { throw "El bucket existente no está en $Region. No modificar un backend de otra región." }
  Write-Host "Bucket existente y accesible en $Region: $BucketName"
} else {
  Write-Host "Creando bucket $BucketName en $Region"
  aws s3api create-bucket --bucket $BucketName --region $Region --create-bucket-configuration "LocationConstraint=$Region"
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el bucket. El nombre puede estar ocupado o faltar permisos.' }
}

aws s3api put-public-access-block --bucket $BucketName --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'
if ($LASTEXITCODE -ne 0) { throw 'No se pudo bloquear el acceso público al bucket.' }
aws s3api put-bucket-versioning --bucket $BucketName --versioning-configuration 'Status=Enabled'
if ($LASTEXITCODE -ne 0) { throw 'No se pudo habilitar el versionado.' }

$encryptConfig = Join-Path ([IO.Path]::GetTempPath()) ('migaraje-s3-encryption-' + [guid]::NewGuid().ToString('N') + '.json')
try {
  [IO.File]::WriteAllText($encryptConfig, '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}')
  aws s3api put-bucket-encryption --bucket $BucketName --server-side-encryption-configuration "file://$encryptConfig"
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo activar el cifrado SSE-S3.' }
} finally { Remove-Item $encryptConfig -ErrorAction SilentlyContinue }

$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root 'backend.hcl'
$backendText = @"
bucket       = "$BucketName"
key          = "migaraje/hito3/terraform.tfstate"
region       = "$Region"
encrypt      = true
use_lockfile = true
"@
# Sin BOM: compatible con parser HCL de Terraform en Windows PowerShell 5.1.
[IO.File]::WriteAllText($backend, $backendText, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Backend generado en $backend (excluido de Git)."
Write-Host 'Siguiente paso: terraform init -backend-config=backend.hcl'
