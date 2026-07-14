from django.core.management.base import BaseCommand
from apps.products.models import Category, Product, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Populates the database with categories, products, and default reviews."

    def handle(self, *args, **options):
        # 1. Create a default user for reviews if not exists
        user, created = User.objects.get_or_create(
            email="admin@hopandbarley.com",
            defaults={
                "username": "admin",
                "is_staff": True,
                "is_superuser": True,
                "phone": "+380000000000",
                "address": "Default Address",
                "city": "Default City",
            }
        )
        if created:
            user.set_password("adminpass")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user"))

        # 2. Create Categories
        categories_data = ["Hops", "Malts", "Yeast", "Adjuncts"]
        categories = {}
        for cat_name in categories_data:
            cat, created = Category.objects.get_or_create(name=cat_name)
            categories[cat_name] = cat
            self.stdout.write(f"Category '{cat_name}': {'Created' if created else 'Already exists'}")

        # 3. Create Products
        products_data = [
            {
                "name": "Citra Hops",
                "description": "Citra is one of the most sought-after and recognizable hop varieties in the world of craft brewing, famous for its bright and multifaceted citrus aroma. Developed in the USA, this variety is ideal for IPAs, Pale Ales, and other styles where a distinct fruity profile is desired.\n\nCitra boasts a high alpha acid content, making it excellent for both bitterness and intense aroma. It imparts notes of grapefruit, lime, passion fruit, lychee, and melon to beer, creating a unique tropical bouquet.\n\nOur T-90 pellets are hermetically sealed to preserve freshness and maximum aromatics.",
                "price": 5.99,
                "stock": 100,
                "category_name": "Hops",
                "image": "products/citra_hops.jpg"
            },
            {
                "name": "Maris Otter Pale Malt",
                "description": "Perfect for traditional British ales. Maris Otter is a low nitrogen barley malt that has been the backbone of fine English beers for decades. It provides a rich, bready, and nutty flavor profile with excellent extract efficiency and reliable lautering.",
                "price": 2.50,
                "stock": 250,
                "category_name": "Malts",
                "image": "products/maris_otter_malt.jpg"
            },
            {
                "name": "SafAle US-05 Dry Ale Yeast",
                "description": "Clean fermenting American ale yeast. SafAle US-05 is the most famous dry active yeast for craft beer brewing. It produces well-balanced beers with low diacetyl and a clean, crisp finish, letting the hop and malt flavors shine.",
                "price": 3.25,
                "stock": 150,
                "category_name": "Yeast",
                "image": "products/safale_us05_yeast.jpg"
            },
            {
                "name": "Cascade Hops",
                "description": "Great for dry hopping. Cascade is the classic American craft beer hop variety, known for its pleasant grapefruit, floral, and citrusy aroma. It has played a key role in the US craft beer revolution.",
                "price": 7.49,
                "stock": 80,
                "category_name": "Hops",
                "image": "products/cascade_hops.jpg"
            },
            {
                "name": "Caramel Malt 60L",
                "description": "Imparts body, color, and head retention in darker beers. Caramel Malt 60L provides a rich caramel flavor, amber color, and sweetness that balances bitterness in IPAs, Porters, and Stouts.",
                "price": 3.00,
                "stock": 120,
                "category_name": "Malts",
                "image": "products/caramel_malt.jpg"
            },
            {
                "name": "Saaz Hops",
                "description": "Essential for Lagers. Saaz is a noble hop variety originating from the Czech Republic, famous for its delicate earthy, herbal, and spicy aroma. It is the signature hop of the classic Pilsner style.",
                "price": 4.75,
                "stock": 95,
                "category_name": "Hops",
                "image": "products/saaz_hops.jpg"
            },
            {
                "name": "Pilsner Malt",
                "description": "Foundation for lagers and pilsners. This premium base malt is made from high-quality 2-row spring barley, providing a light straw color and a clean, sweet, malty flavor.",
                "price": 2.20,
                "stock": 300,
                "category_name": "Malts",
                "image": "products/pilsner_malt.jpg"
            },
            {
                "name": "Imperial Organic Yeast A07",
                "description": "Perfect for American ales with subtle citrus notes. A07 Flagship is the classic, clean-fermenting dry yeast strain that is extremely versatile and excels at accentuating hop character.",
                "price": 8.99,
                "stock": 60,
                "category_name": "Yeast",
                "image": "products/imperial_yeast.jpg"
            },
            {
                "name": "Centennial Hops",
                "description": "Often called 'Super Cascade'. Centennial has similar citrusy characteristics to Cascade, but with higher alpha acids and more intense floral notes. Extremely popular in modern IPAs.",
                "price": 6.20,
                "stock": 85,
                "category_name": "Hops",
                "image": "products/centennial_hops.jpg"
            },
            {
                "name": "Mosaic Hops",
                "description": "Ideal for IPAs and Pale Ales. Mosaic features complex citrus, berry, tropical fruit, and pine characteristics, making it one of the most versatile and popular dual-purpose hops.",
                "price": 9.50,
                "stock": 110,
                "category_name": "Hops",
                "image": "products/mosaic_hops.jpg"
            },
            {
                "name": "West Coast IPA - All-Grain Kit",
                "description": "Classic West Coast IPA recipe kit including hops, malts, and yeast needed to brew a 20-liter batch of bitter, piney, and citrusy IPA.",
                "price": 60.00,
                "stock": 40,
                "category_name": "Adjuncts",
                "image": "products/ipa_kit.jpg"
            },
            {
                "name": "Unmalted Wheat",
                "description": "Essential ingredient for Belgian Witbier and traditional wheat beers, contributing protein for head retention and a characteristic pleasant haziness.",
                "price": 1.80,
                "stock": 200,
                "category_name": "Malts",
                "image": "products/unmalted_wheat.jpg"
            },
            {
                "name": "Simcoe Hops",
                "description": "Known for its unique and complex aromatic profile, featuring stone fruit, pine, citrus, and woodsy notes. Great for double IPAs.",
                "price": 6.50,
                "stock": 90,
                "category_name": "Hops",
                "image": "products/mosaic_hops.jpg"
            },
            {
                "name": "Munich Malt",
                "description": "A dark base malt that provides a robust, malty flavor, golden-orange color, and full body. Perfect for Bocks, Octoberfests, and dark ales.",
                "price": 2.80,
                "stock": 180,
                "category_name": "Malts",
                "image": "products/pilsner_malt.jpg"
            },
            {
                "name": "Lallemand Abbaye Yeast",
                "description": "Belgian ale yeast selected for its ability to produce traditional Belgian style beers including high gravity beers like Dubbel, Tripel, and Quadrupel.",
                "price": 4.10,
                "stock": 70,
                "category_name": "Yeast",
                "image": "products/safale_us05_yeast.jpg"
            },
            {
                "name": "Amarillo Hops",
                "description": "Features a distinct flowery, citrusy, and tropical fruit aroma with strong notes of grapefruit. Popular in American Pale Ales.",
                "price": 8.00,
                "stock": 115,
                "category_name": "Hops",
                "image": "products/cascade_hops.jpg"
            },
            {
                "name": "Chocolate Malt",
                "description": "Provides a rich, roasted coffee and cocoa flavor. Essential for Stouts, Porters, and dark beers where dark chocolate colors are desired.",
                "price": 3.50,
                "stock": 140,
                "category_name": "Malts",
                "image": "products/caramel_malt.jpg"
            },
            {
                "name": "Hallertauer Mittelfruh Hops",
                "description": "A classic noble hop variety with mild, spicy, and floral characteristics. The traditional hop of German Pilsners and lagers.",
                "price": 5.25,
                "stock": 100,
                "category_name": "Hops",
                "image": "products/saaz_hops.jpg"
            },
            {
                "name": "Vienna Malt",
                "description": "Kilned slightly warmer than Pilsner malt to provide a golden color and a smooth, sweet, malty flavor. Ideal for Vienna Lagers and Märzen.",
                "price": 2.40,
                "stock": 220,
                "category_name": "Malts",
                "image": "products/maris_otter_malt.jpg"
            },
            {
                "name": "SafLager W-34/70 Lager Yeast",
                "description": "The famous German strain used worldwide for lager brewing. Produces clean lager profiles with neutral flavor profiles.",
                "price": 4.50,
                "stock": 130,
                "category_name": "Yeast",
                "image": "products/safale_us05_yeast.jpg"
            },
            {
                "name": "Chinook Hops",
                "description": "A piney, spicy, and grapefruit-heavy dual-purpose hop variety. Widely used for both bittering and late kettle additions in IPAs.",
                "price": 6.80,
                "stock": 75,
                "category_name": "Hops",
                "image": "products/centennial_hops.jpg"
            },
            {
                "name": "Magnum Hops",
                "description": "A clean bittering hop variety with high alpha acids. Excellent as a base bittering addition for almost any beer style.",
                "price": 5.50,
                "stock": 120,
                "category_name": "Hops",
                "image": "products/citra_hops.jpg"
            },
            {
                "name": "American Pale Ale Kit",
                "description": "A complete recipe kit containing light malt extracts, Cascade hop pellets, and dry yeast for a citrusy, refreshing APA batch.",
                "price": 45.00,
                "stock": 35,
                "category_name": "Adjuncts",
                "image": "products/ipa_kit.jpg"
            },
            {
                "name": "Flaked Oats",
                "description": "Adds a smooth, velvety mouthfeel and rich body to Stouts, Porters, and New England IPAs. Improves head retention.",
                "price": 1.95,
                "stock": 190,
                "category_name": "Malts",
                "image": "products/unmalted_wheat.jpg"
            }
        ]

        for p_info in products_data:
            p, created = Product.objects.get_or_create(
                name=p_info["name"],
                defaults={
                    "description": p_info["description"],
                    "price": p_info["price"],
                    "stock": p_info["stock"],
                    "image": p_info["image"],
                    "is_active": True
                }
            )
            if created:
                p.categories.add(categories[p_info["category_name"]])
                self.stdout.write(self.style.SUCCESS(f"Product '{p.name}': Created"))
                
                # 4. Create some default reviews for products
                Review.objects.create(
                    product=p,
                    user=user,
                    rating=5,
                    comment=f"Awesome product! Very high quality {p.name}. Highly recommend to all brewers!"
                )
                Review.objects.create(
                    product=p,
                    user=user,
                    rating=4,
                    comment=f"Good value for money. The {p.name} worked perfectly in my recipe."
                )
                self.stdout.write(f"Added 2 default reviews for '{p.name}'")
            else:
                self.stdout.write(f"Product '{p.name}': Already exists")
