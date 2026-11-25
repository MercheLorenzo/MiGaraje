#requires -Version 5.1
<#
Comprobaciones de solo lectura para el proyecto AWS Free Plan de MiGaraje.
No crea infraestructura, no altera recursos y no almacena credenciales.
#>
param(
  [string]$Profile = 'migaraje-lab',
  [string]$Region = 'eu-north-1',
  [string]$InstanceType = 'm7i-flex.large'
)
$ErrorActionPreference = 'Stop'
if ($Region -ne 'eu-north-1') { throw 'Este laboratorio usa exclusivamente eu-north-1 (Estocolmo).' }
if ($InstanceType -notin @('m7i-flex.large', 'c7i-flex.large')) {
  throw 'La instancia debe ser m7i-flex.large o c7i-flex.large para esta plantilla.'
}
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw 'AWS CLI no encontrado.' }
$env:AWS_PROFILE = $Profile
$env:AWS_DEFAULT_REGION = $Region
Write-Host '1/4 Identidad y proyecto AWS (solo lectura)'
aws sts get-caller-identity --query Arn --output text
if ($LASTEXITCODE -ne 0) { throw 'No hay sesión AWS válida. Ejecuta aws login --profile migaraje-lab.' }
Write-Host '2/4 Región del perfil'
$configured = (aws configure get region --profile $Profile).Trim()
if ($configured -ne $Region) { throw "La región del perfil es '$configured'. Debe ser $Region." }
Write-Host "Perfil: $Profile; región: $Region"
Write-Host "3/4 Elegibilidad Free Tier de $InstanceType (no equivale a coste cero)"
$eligible = (aws ec2 describe-instance-types --region $Region --instance-types $InstanceType --query 'InstanceTypes[0].FreeTierEligible' --output text).Trim()
if ($LASTEXITCODE -ne 0) { throw 'AWS no ha permitido consultar el tipo de instancia. No ejecutes apply.' }
Write-Host "FreeTierEligible = $eligible"
if ($eligible.ToLower() -ne 'true') { throw 'La instancia no figura como Free Tier eligible: no ejecutar apply.' }
Write-Host '4/4 Oferta en la región (la capacidad en una AZ puede variar)'
$offer = (aws ec2 describe-instance-type-offerings --region $Region --location-type region --filters "Name=instance-type,Values=$InstanceType" --query 'InstanceTypeOfferings[*].InstanceType' --output text).Trim()
if ($LASTEXITCODE -ne 0) { throw 'AWS no ha permitido consultar disponibilidad. No ejecutes apply.' }
if (-not $offer) { throw "No se ofrece $InstanceType en $Region." }
Write-Host "Disponible en catálogo de región: $offer"
Write-Host 'PREFLIGHT OK. Aun asi, revisa créditos, cuotas, permisos y presupuesto ANTES de apply.'
