import os
import django
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datascientist.settings")
django.setup()
from greenbook.models import asset_sold_car_test

test  = asset_sold_car_test.objects.filter(
    brand_name="Toyota",
    model_name="Yaris Ativ",
    sub_model_code="1.2 Premium CVT",
    year_of_manufacture=2022
).values("brand_name", "model_name", "sub_model_code", "year_of_manufacture", "asset_gear", "asset_group_name", "engine_size")

print(test)