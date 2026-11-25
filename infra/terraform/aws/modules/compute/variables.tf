variable "name_prefix" { type = string }
variable "subnet_id" { type = string }
variable "security_group_id" { type = string }
variable "instance_type" { type = string }
variable "root_volume_gib" { type = number }
variable "user_data" { type = string }
variable "drift_marker" { type = string }
