from django.core.management.base import BaseCommand
from shop.models import Brand, Product
import random

ITEMS = [
    # (name, brand, category, image_url, price)
    ("DEORE BR-M6100 2-Piston Caliper", "Shimano", "Brakes",
     "https://picsum.photos/seed/deore_m6100/600/400", 89.00),
    ("MT5 NEXT Disc Brake", "Magura", "Brakes",
     "https://picsum.photos/seed/magura_mt5/600/400", 139.00),

    ("Road Pro Complete Cable Kit", "Jagwire", "Cables & Housings",
     "https://picsum.photos/seed/jagwire_roadpro/600/400", 39.00),

    ("Service Course SL Stem", "Zipp", "Cockpit",
     "https://picsum.photos/seed/zipp_sc_sl/600/400", 120.00),

    ("FOX 34 Trail Fork", "FOX", "Forks",
     "https://picsum.photos/seed/fox34/600/400", 899.00),

    ("Deluxe Select+ Rear Shock", "RockShox", "Rear Shock Absorbers",
     "https://picsum.photos/seed/deluxe_select_plus/600/400", 439.00),

    ("Pro 4 Rear Hub", "Hope", "Hubs & Freewheels",
     "https://picsum.photos/seed/hope_pro4/600/400", 249.00),
    ("RS4 Rear Hub", "Hope", "Hubs & Freewheels",
     "https://picsum.photos/seed/hope_rs4/600/400", 259.00),

    ("R 470 Rim (700C)", "DT Swiss", "Rims",
     "https://picsum.photos/seed/dt_r470/600/400", 79.00),

    ("Marathon Plus 700x28C", "Schwalbe", "Tires",
     "https://picsum.photos/seed/schwalbe_mp/600/400", 58.00),

    ("Race 28 Inner Tube (700x20-25)", "Continental", "Inner Tubes",
     "https://picsum.photos/seed/conti_race28/600/400", 9.50),

    ("DURA-ACE PD-R9100 SPD-SL Pedals", "Shimano", "Pedals",
     "https://picsum.photos/seed/pd_r9100/600/400", 279.00),

    ("Volt Saddle", "WTB", "Saddles",
     "https://picsum.photos/seed/wtb_volt/600/400", 64.95),
]

class Command(BaseCommand):
    help = "Load bike parts by category with different brands (uses placeholder images)."

    def handle(self, *args, **opts):
        rng = random.Random(42)
        for _, brand, _, _, _ in ITEMS:
            Brand.objects.get_or_create(name=brand)
        created = 0
        for name, brand, cat, img, price in ITEMS:
            b = Brand.objects.get(name=brand)
            Product.objects.get_or_create(
                name=name,
                defaults=dict(brand=b, category=cat, price=round(price or rng.uniform(9, 499), 2), image_url=img),
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Loaded/kept {created} products across {len(set(b for _,b,_,_,_ in ITEMS))} brands."))
