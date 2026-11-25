output "instance_id" {
  description = "ID EC2 para SSM, sin acceso SSH."
  value       = module.compute.instance_id
}
output "instance_public_ip" {
  description = "IP pública de EC2 (no implica que haya entradas abiertas)."
  value       = module.compute.public_ip
}
output "vpc_id" {
  value = module.network.vpc_id
}
output "public_subnet_id" {
  value = module.network.public_subnet_id
}
output "private_subnet_id" {
  value = module.network.private_subnet_id
}
output "security_group_id" {
  value = module.network.security_group_id
}
output "data_volume_id" {
  value = module.storage.volume_id
}
output "ssm_tunnel_command_example" {
  description = "Ejemplo: sustituir el ID y ejecutar con AWS CLI y Session Manager plugin."
  value       = "aws ssm start-session --target ${module.compute.instance_id} --region ${var.aws_region} --document-name AWS-StartPortForwardingSession --parameters portNumber=8081,localPortNumber=8081"
}
output "direct_http_url_if_opted_in" {
  description = "Solo si se activó trusted_ipv4_cidr; HTTP sin TLS exclusivamente para laboratorio."
  value       = var.trusted_ipv4_cidr != null ? "http://${module.compute.public_ip}:8081" : null
}
