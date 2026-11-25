variable "name_prefix" { type = string }
variable "availability_zone" { type = string }
variable "vpc_cidr" { type = string }
variable "public_subnet_cidr" { type = string }
variable "private_subnet_cidr" { type = string }
variable "trusted_ipv4_cidr" {
  type     = string
  default  = null
  nullable = true
}
