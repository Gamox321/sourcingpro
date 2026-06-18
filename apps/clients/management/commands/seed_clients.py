from django.core.management.base import BaseCommand
from apps.clients.models import Client, CostCenter
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Crea datos de ejemplo para clientes y centros de costo"

    def handle(self, *args, **options):
        clientes_data = [
            {
                "nombre": "Codelco",
                "descripcion": "Corporación Nacional del Cobre de Chile",
            },
            {"nombre": "BHP", "descripcion": "BHP Group — Minera Escondida"},
            {
                "nombre": "Minera Los Pelambres",
                "descripcion": "Antofagasta Minerals — Minera Los Pelambres",
            },
            {
                "nombre": "Anglo American",
                "descripcion": "Anglo American plc — División Chilena",
            },
        ]
        created_clients = []
        for data in clientes_data:
            client, created = Client.objects.get_or_create(
                nombre=data["nombre"], defaults={"descripcion": data["descripcion"]}
            )
            created_clients.append(client)
            self.stdout.write(self.style.SUCCESS(f"  Cliente: {client.nombre}"))

        admin = User.objects.filter(is_superuser=True).first()
        cecos_data = [
            {"nombre": "Mina Rajo", "codigo": "RAJO-001", "cliente_idx": 0},
            {
                "nombre": "Planta Concentradora",
                "codigo": "PLANTA-001",
                "cliente_idx": 0,
            },
            {"nombre": "Fundición", "codigo": "FUND-001", "cliente_idx": 0},
            {"nombre": "Escondida Norte", "codigo": "ESCN-001", "cliente_idx": 1},
            {
                "nombre": "Operaciones Los Pelambres",
                "codigo": "LPEL-001",
                "cliente_idx": 2,
            },
            {"nombre": "Chagres", "codigo": "CHAG-001", "cliente_idx": 3},
        ]
        for data in cecos_data:
            cc, created = CostCenter.objects.get_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "cliente": created_clients[data["cliente_idx"]],
                    "jefatura": admin,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"  CeCo: {cc.nombre} ({cc.codigo})"))

        self.stdout.write(self.style.SUCCESS("Seed de clientes y CeCos completado."))
