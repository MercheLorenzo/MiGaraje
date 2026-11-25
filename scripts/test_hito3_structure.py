"""Pruebas estáticas del Hito 3 sin conectar a AWS ni leer credenciales."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
TF = ROOT / 'infra' / 'terraform' / 'aws'


class TerraformStructureTest(unittest.TestCase):
    def test_files(self):
        for name in ('main.tf', 'providers.tf', 'variables.tf', 'outputs.tf',
                     'backend.hcl.example', 'terraform.tfvars.example',
                     'templates/cloud-init.sh.tftpl', 'scripts/bootstrap-state.ps1',
                     'scripts/preflight-free-plan.ps1'):
            self.assertTrue((TF / name).is_file(), name)
        for module in ('network', 'compute', 'storage'):
            for name in ('main.tf', 'variables.tf', 'outputs.tf'):
                self.assertTrue((TF / 'modules' / module / name).is_file())

    def test_region_north(self):
        for name in ('variables.tf', 'terraform.tfvars.example', 'backend.hcl.example',
                     'scripts/bootstrap-state.ps1', 'scripts/preflight-free-plan.ps1', 'README.md'):
            value = (TF / name).read_text(encoding='utf-8')
            self.assertIn('eu-north-1', value, name)
            self.assertNotIn('eu-south-2', value, name)
        self.assertIn('var.aws_region == "eu-north-1"', (TF / 'variables.tf').read_text())

    def test_free_plan_instance(self):
        self.assertIn('m7i-flex.large', (TF / 'terraform.tfvars.example').read_text())
        compute = (TF / 'modules/compute/main.tf').read_text()
        self.assertNotIn('credit_specification {', compute)
        self.assertIn('AmazonSSMManagedInstanceCore', compute)

    def test_s3(self):
        self.assertIn('backend "s3"', (TF / 'providers.tf').read_text())
        self.assertIn('use_lockfile = true', (TF / 'backend.hcl.example').read_text())
        bootstrap = (TF / 'scripts/bootstrap-state.ps1').read_text()
        for part in ('get-bucket-location', 'put-bucket-encryption', 'put-bucket-versioning', 'put-public-access-block'):
            self.assertIn(part, bootstrap)

    def test_network_storage(self):
        network = (TF / 'modules/network/main.tf').read_text()
        for name in ('aws_vpc', 'aws_subnet', 'aws_route_table', 'aws_security_group', 'aws_internet_gateway'):
            self.assertIn(name, network)
        self.assertIn('encrypted         = true', (TF / 'modules/storage/main.tf').read_text())

    def test_secret_exclusions(self):
        for file in TF.rglob('*.tf'):
            for name in ('AWS_SECRET_ACCESS_KEY=', 'POSTGRES_PASSWORD=', 'JWT_SECRET='):
                self.assertNotIn(name, file.read_text(), str(file))
        ignore = (ROOT / '.gitignore').read_text()
        for name in ('*.tfvars', '*.tfstate', '*.tfplan', '**/backend.hcl', '.env'):
            self.assertIn(name, ignore)

    def test_docs(self):
        for name in ('docs/HITO3.md', 'README.md', 'infra/terraform/aws/README.md',
                     'infra/terraform/aws/evidence/observaciones.md', '.github/workflows/terraform.yml'):
            self.assertTrue((ROOT / name).exists(), name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
