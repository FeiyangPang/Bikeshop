from django.core.management.base import BaseCommand
from shop.models import Brand, Product
import csv, decimal, pathlib

class Command(BaseCommand):
    help = "Import products from a CSV with columns: name,brand,category,price,image_url"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **opts):
        path = pathlib.Path(opts["csv_path"])
        count = 0
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                brand, _ = Brand.objects.get_or_create(name=row["brand"].strip())
                price = decimal.Decimal(str(row["price"]).strip())
                obj, created = Product.objects.get_or_create(
                    name=row["name"].strip(),
                    defaults={
                        "brand": brand,
                        "category": row["category"].strip(),
                        "price": price,
                        "image_url": row.get("image_url","").strip(),
                    },
                )
                if not created:
                    obj.brand = brand
                    obj.category = row["category"].strip()
                    obj.price = price
                    obj.image_url = row.get("image_url","").strip()
                    obj.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Imported/updated {count} products."))
