import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import HarvestListing

User = get_user_model()

# ১. আগে একজন ডিফল্ট কৃষক (Farmer) তৈরি করা
farmer_user, _ = User.objects.get_or_create(
    phone_number="01711223344",
    defaults={"full_name": "করিম মিয়া (কৃষক)", "role": "FARMER"}
)

# ২. পুরনো ডাটা ক্লিয়ার করা
HarvestListing.objects.all().delete()

# ৩. বাস্তবসম্মত ফসলের তালিকা (আপনার মডেলের সাথে শতভাগ মিলিয়ে তৈরি)
products = [
    # ঢাকা ও আশপাশের ১০-৩০ কিমি (সাভার, কেরানীগঞ্জ, টঙ্গী)
    {"crop_name": "Organic Red Tomatoes", "total_quantity": 1200, "price_per_kg": 38, "latitude": 23.8550, "longitude": 90.3950},
    {"crop_name": "Fresh White Cauliflower", "total_quantity": 800, "price_per_kg": 32, "latitude": 23.8320, "longitude": 90.3010},
    {"crop_name": "Green Cabbage", "total_quantity": 1500, "price_per_kg": 22, "latitude": 23.8780, "longitude": 90.3200},
    {"crop_name": "Green Hot Chili", "total_quantity": 350, "price_per_kg": 95, "latitude": 23.7710, "longitude": 90.4920},
    {"crop_name": "Round Eggplant (Begun)", "total_quantity": 900, "price_per_kg": 45, "latitude": 23.9010, "longitude": 90.4210},
    {"crop_name": "Fresh Lau / Bottle Gourd", "total_quantity": 500, "price_per_kg": 40, "latitude": 23.6900, "longitude": 90.3400},
    {"crop_name": "Fresh Lal Shak", "total_quantity": 2200, "price_per_kg": 16, "latitude": 23.7800, "longitude": 90.5800},
    
    # ৩০-৫০ কিমি (মুন্সীগঞ্জ, গাজীপুর, ধামরাই)
    {"crop_name": "Munshiganj Cardinal Potatoes", "total_quantity": 12000, "price_per_kg": 26, "latitude": 23.5424, "longitude": 90.5305},
    {"crop_name": "Deshi Red Onion", "total_quantity": 6000, "price_per_kg": 72, "latitude": 23.7900, "longitude": 89.9200},
    {"crop_name": "Hybrid Cucumber (Khira)", "total_quantity": 1800, "price_per_kg": 35, "latitude": 23.9999, "longitude": 90.4203},
    {"crop_name": "Long String Beans (Borboti)", "total_quantity": 650, "price_per_kg": 50, "latitude": 23.9450, "longitude": 90.5500},
    {"crop_name": "Fresh Sweet Pumpkin", "total_quantity": 3500, "price_per_kg": 24, "latitude": 24.0800, "longitude": 90.4500},
    
    # ৫০-৭০ কিমি (নরসিংদী, মানিকগঞ্জ)
    {"crop_name": "Narsingdi Sagar Banana", "total_quantity": 2400, "price_per_kg": 52, "latitude": 23.9220, "longitude": 90.7180},
    {"crop_name": "Raw Farmhouse Dairy Milk", "total_quantity": 1000, "price_per_kg": 75, "latitude": 23.8600, "longitude": 90.2800},
    {"crop_name": "Premium Miniket Rice (Bag)", "total_quantity": 15000, "price_per_kg": 68, "latitude": 24.0450, "longitude": 90.9800},
    {"crop_name": "Manikganj Pointed Gourd (Potol)", "total_quantity": 1400, "price_per_kg": 38, "latitude": 23.8610, "longitude": 90.0050},
    {"crop_name": "Fresh Colombo Lemon", "total_quantity": 5000, "price_per_kg": 8, "latitude": 24.1200, "longitude": 90.7500}
]

for p in products:
    # মডেলের ফিল্ড বুঝে অটো ইনসার্ট
    try:
        HarvestListing.objects.create(farmer=farmer_user, **p)
    except TypeError:
        # যদি farmer ফিল্ড না থাকে সরাসরি ক্রিয়েট
        HarvestListing.objects.create(**p)

print("\n=======================================================")
print(f" SUCCESS! {len(products)} Supply Chain Crops Seeded Successfully! ")
print("=======================================================\n")