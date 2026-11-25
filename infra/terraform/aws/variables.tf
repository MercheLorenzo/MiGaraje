variable "aws_region" {
  description = "Región fija del proyecto AWS Free Plan: Estocolmo, Suecia (UE)."
  type        = string
  default     = "eu-north-1"
  validation {
    condition     = var.aws_region == "eu-north-1"
    error_message = "El proyecto AWS Free Plan de MiGaraje está limitado a eu-north-1. No usar otra región."
  }
}

variable "availability_zone" {
  description = "Opcional: zona de disponibilidad con capacidad para la EC2 seleccionada; null elige la primera habilitada."
  type        = string
  default     = null
  nullable    = true
}

variable "project" {
  description = "Prefijo estable de recursos."
  type        = string
  default     = "migaraje"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,18}$", var.project))
    error_message = "project debe tener 3-19 caracteres, minúsculas/números/guiones."
  }
}

variable "environment" {
  description = "Entorno de despliegue."
  type        = string
  default     = "lab"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,12}$", var.environment))
    error_message = "environment debe usar minúsculas, números o guiones."
  }
}

variable "vpc_cidr" {
  description = "Red principal IPv4 privada."
  type        = string
  default     = "10.42.0.0/16"
}
variable "public_subnet_cidr" {
  description = "Subred pública para EC2."
  type        = string
  default     = "10.42.10.0/24"
}
variable "private_subnet_cidr" {
  description = "Subred privada aislada, sin NAT (preparada para futura ampliación)."
  type        = string
  default     = "10.42.20.0/24"
}

variable "instance_type" {
  description = "Instancia x86_64 seleccionable en nuevo Free Tier; m7i-flex.large es candidata (2 vCPU/8 GiB). Verificar cuota, elegibilidad y coste antes de apply."
  type        = string
  default     = "m7i-flex.large"
  validation {
    condition     = contains(["m7i-flex.large", "c7i-flex.large"], var.instance_type)
    error_message = "Selecciona una instancia x86_64 elegible para el Free Tier nuevo. Comprueba oferta y capacidad real en eu-north-1."
  }
}

variable "root_volume_gib" {
  description = "Tamaño disco raíz de EC2."
  type        = number
  default     = 24
  validation {
    condition     = var.root_volume_gib >= 16 && var.root_volume_gib <= 100
    error_message = "root_volume_gib debe estar entre 16 y 100 GiB."
  }
}

variable "data_volume_gib" {
  description = "Disco EBS gp3 cifrado dedicado a datos Docker/PostgreSQL."
  type        = number
  default     = 24
  validation {
    condition     = var.data_volume_gib >= 10 && var.data_volume_gib <= 100
    error_message = "data_volume_gib debe estar entre 10 y 100 GiB."
  }
}

variable "trusted_ipv4_cidr" {
  description = "Opcional: única IP /32 autorizada al HTTP 8081. null = SIN puertos entrantes (recomendado: túnel SSM)."
  type        = string
  default     = null
  nullable    = true
  validation {
    condition     = var.trusted_ipv4_cidr == null ? true : can(cidrhost(var.trusted_ipv4_cidr, 0)) && can(regex("/32$", var.trusted_ipv4_cidr))
    error_message = "Especifica null o una IP pública IPv4 /32, p. ej. 203.0.113.10/32."
  }
}

variable "repository_url" {
  description = "Repositorio público desde el que EC2 clona el código de MiGaraje."
  type        = string
  default     = "https://github.com/MercheLorenzo/MiGaraje.git"
  validation {
    condition     = can(regex("^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+([.]git)?$", var.repository_url))
    error_message = "Para este laboratorio repository_url debe ser un repositorio público de github.com por HTTPS."
  }
}

variable "repository_ref" {
  description = "Rama o tag publicado que clonará la VM. Usar rama de Hito3 durante pruebas; main después del merge."
  type        = string
  default     = "feature/hito3-terraform"
  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", var.repository_ref))
    error_message = "repository_ref debe ser una rama o tag simple, sin espacios ni caracteres shell."
  }
}

variable "drift_marker" {
  description = "Valor deseado de la etiqueta EC2 'DriftDemo'; se alterará manualmente para el experimento."
  type        = string
  default     = "terraform-managed"
}
