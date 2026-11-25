data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  prefix = "${var.project}-${var.environment}"
  az     = var.availability_zone != null ? var.availability_zone : data.aws_availability_zones.available.names[0]
}

module "network" {
  source              = "./modules/network"
  name_prefix         = local.prefix
  availability_zone   = local.az
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidr  = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr
  trusted_ipv4_cidr   = var.trusted_ipv4_cidr
}

module "storage" {
  source            = "./modules/storage"
  name_prefix       = local.prefix
  availability_zone = local.az
  data_volume_gib   = var.data_volume_gib
}

module "compute" {
  source             = "./modules/compute"
  name_prefix        = local.prefix
  subnet_id          = module.network.public_subnet_id
  security_group_id  = module.network.security_group_id
  instance_type      = var.instance_type
  root_volume_gib    = var.root_volume_gib
  drift_marker       = var.drift_marker
  user_data          = templatefile("${path.module}/templates/cloud-init.sh.tftpl", {
    volume_id      = module.storage.volume_id
    repository_url = var.repository_url
    repository_ref = var.repository_ref
  })
}

# EBS separado de la instancia: disponible antes del bootstrap; este espera su unión.
resource "aws_volume_attachment" "docker_data" {
  device_name = "/dev/sdf"
  volume_id   = module.storage.volume_id
  instance_id = module.compute.instance_id
}
