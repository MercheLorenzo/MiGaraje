resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                = { Name = "${var.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.name_prefix}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name_prefix}-public" }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.name_prefix}-private-isolated" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.name_prefix}-public-rt" }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# A propósito, sin ruta por defecto ni NAT: evita costes y acceso saliente no necesario.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.name_prefix}-private-rt" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "app" {
  name        = "${var.name_prefix}-sg"
  description = "MiGaraje: SSM sin SSH, HTTP 8081 opcional limitado a una IP /32"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${var.name_prefix}-sg" }
}

# Opt-in solo para demo en red confiable. Por defecto NO hay reglas de entrada.
resource "aws_vpc_security_group_ingress_rule" "http_lab" {
  count             = var.trusted_ipv4_cidr == null ? 0 : 1
  security_group_id = aws_security_group.app.id
  description       = "HTTP temporal 8081 desde IP propia; preferir tunel SSM"
  from_port         = 8081
  to_port           = 8081
  ip_protocol       = "tcp"
  cidr_ipv4         = var.trusted_ipv4_cidr
}

# Acceso saliente mínimo práctico para apt, GitHub, ECR/Docker y AWS SSM.
resource "aws_vpc_security_group_egress_rule" "web" {
  for_each = { http = 80, https = 443 }

  security_group_id = aws_security_group.app.id
  description       = "Salida ${each.key} para bootstrap/SSM"
  from_port         = each.value
  to_port           = each.value
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "dns_udp" {
  security_group_id = aws_security_group.app.id
  description       = "Resolucion DNS UDP en la VPC"
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
  cidr_ipv4         = var.vpc_cidr
}
resource "aws_vpc_security_group_egress_rule" "dns_tcp" {
  security_group_id = aws_security_group.app.id
  description       = "Resolucion DNS TCP en la VPC"
  from_port         = 53
  to_port           = 53
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr
}
