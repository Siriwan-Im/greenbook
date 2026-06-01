from django.http import HttpResponse,JsonResponse
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User,auth
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Avg
from .models import greenbook,asset_sold_car_test
import joblib
import numpy as np
from datetime import datetime
import math 
import re
import json
import time
#import templates.greenbook 
#model = joblib.load('greenbook/models/pipeline_test.pkl')

# Prepare dataframe 
df = pd.DataFrame(asset_sold_car_test.objects.all().values())
df2 = pd.DataFrame(greenbook.objects.all().values())

df.replace('-', np.nan,inplace = True)
df.replace(' ', np.nan,inplace = True)
df.replace('', np.nan,inplace = True)
df.replace({np.nan: None})

df['model_name'] = df['model_name'].astype(str)
df['sub_model_code'] = df['sub_model_code'].astype(str)

filter_df = df[(~df['asset_group_code'].isin(['N','X'])) 
                & (~df['asset_grade_check_condition'].isin(['N','U'])) 
                & (~df['brand_name'].isin(['FORKLIFT','NEW HOLLAND','HINO','UD TRUCKS']))
                & (~df['model_name'].str.contains('ล้อWHEELS',na=False,regex=False))
                & (~df['model_name'].str.contains('พ่วง',na=False,regex=False))
                & (~df['model_name'].str.contains('WHEELS',na=False,regex=False))
                & (~df['sub_model_code'].str.contains('ล้อ',na=False,regex=False))
                & (~df['sub_model_code'].str.contains('พ่วง',na=False,regex=False))
                & (~df['sub_model_code'].str.contains('ตู้',na=False,regex=False))
            ]

filter_df['sub_model_code'] = filter_df['sub_model_code'].str.upper()
filter_df['sub_model_code'] = filter_df['sub_model_code'].str.replace(' ', '', regex=False)
filter_df['sub_model_code'] = filter_df['sub_model_code'].str.replace('-', '', regex=False)
filter_df['sub_model_code'] = filter_df['sub_model_code'].str.replace('(NEW)', '', regex=False)
filter_df['sub_model_code'] = filter_df['sub_model_code'].replace(['Nan', 'nan','NaN'], np.nan)
filter_df = filter_df.replace(['Nan', 'nan','NaN'], np.nan)
filter_df['sub_key'] = filter_df['sub_key'].astype(str)
filter_df['sub_key'] = filter_df['sub_key'].replace(['Nan', 'nan','NaN'], np.nan)
filter_df = filter_df.replace({np.nan: None})

##3.Greenbook Data (New Price)
# Process 3 : Data Preprocessing
###Main
filter_df['sub_key'] = filter_df['sub_key'].astype(str)
filter_df['vehiclekey'] = filter_df['vehiclekey'].astype(str)

filter_df['sub_key'] = filter_df['sub_key'].replace(' ','',regex=False)
filter_df['vehiclekey'] = filter_df['vehiclekey'].replace(' ','',regex=False)
filter_df['sub_key'] = filter_df['sub_key'].str.strip()
filter_df['vehiclekey'] = filter_df['vehiclekey'].str.strip()

###Support Data
df2['vehiclekey'] = df2['vehiclekey'].astype(str)
df2['vehiclekey'] = df2['vehiclekey'].replace(' ','',regex=False)
df2['vehiclekey'] = df2['vehiclekey'].str.strip()

###Merge
table = filter_df.merge(df2,left_on="sub_key",right_on="vehiclekey",how="left",indicator=True)
for col in table.columns:
    table[col] = table[col].replace(['Nan', 'nan','NaN'], np.nan)
    table[col] = table[col].replace({np.nan: None})

##3.2 Data Cleansing
###Train model could have Sub_Key(Refference >> Brand_Name,Model_Name,Sub_Model_Code)
table = table[(~table['brand_name'].isna()) & (~table['model_name'].isna()) & (~table['sub_model_code'].isna())]

###3.2.1 Asset Register Year

# QuerySet.values() yields DateField as date/object; coerce to datetime64 for .dt accessor
table["auction_date"] = pd.to_datetime(table["auction_date"], errors="coerce")

table['diff_of_year'] = table['asset_register_year']-table['year_of_manufacture']
avg_diff = int(table['diff_of_year'].mode()[0])

table.loc[table['asset_register_year'].isna(),'asset_register_year'] = table[table['asset_register_year'].isna()]['year_of_manufacture'].astype(int) + avg_diff
table.loc[table['asset_register_year'] == 0,'asset_register_year'] = table[table['asset_register_year'] == 0]['year_of_manufacture'].astype(int) + avg_diff
table.loc[table['asset_register_year'].astype(int)> table['auction_date'].dt.year,'asset_register_year'] = table[table['asset_register_year'].astype(int)> table['auction_date'].dt.year]['year_of_manufacture'].astype(int) + avg_diff
table['asset_register_year'] = table['asset_register_year'].astype(int)

mile_list = []

for m in list(table['mile'].values):
    if pd.isna(m):
        mile_list.append(m)
    else:
        mile_list.append(int(m))

table['Mile_Int'] = mile_list

####Clean double value
for i in range(0,len(table)):
    if pd.notna(table['Mile_Int'][i]):
        value = str(int(table['Mile_Int'][i]))
        name = str(table['brand_name'][i])+str(table['model_name'][i]) + str(table['sub_model_code'][i])

        half_len = int(len(value)/2)
        value_list = list(value)
        
        mile_b = ''
        mile_a = ''

        if len(value) > 6 :
            for b in range(0,half_len):
                mile_b = mile_b + value_list[b]
                
            for a in range(half_len,len(value)):
                mile_a = mile_a + value_list[a]
                
            if mile_b == mile_a:
                print(f"{name} : Mile {value} dup")
                print("Update new value complete")
                table.loc[i, 'Mile_Int'] = int(mile_b)

####Fill missing values by median by year and group code
median_of_mile = pd.DataFrame(table.groupby(['asset_group_code','asset_register_year'])['mile'].agg('median').rename('median_mile'))
median_of_mile = median_of_mile.reset_index()

table = table.merge(median_of_mile, on=['asset_register_year','asset_group_code'],how='left')

mile_transform = []
for i in range(0,len(table)):
    value = table['Mile_Int'][i]
    t_value = table['median_mile'][i]

    if pd.isna(value):
        mile_transform.append(t_value)
    elif value > 1000000:
        mile_transform.append(t_value)
    else:
        mile_transform.append(value)
table['Mile_Transform'] = mile_transform

###3.2.3 Asset_Grade_Check_Condition/Asset_Grade/Asset_Grade_Assessment
####fill missing value Asset_Grade_Check_Condition by Asset_Grade
table['asset_grade_check_condition'] = table['asset_grade_check_condition'].fillna(table['asset_grade'])
table['asset_grade_check_condition'] = table['asset_grade_check_condition'].fillna(0)

####fill missing value Asset_Grade by 0
table['asset_grade'] = table['asset_grade'].fillna(0)

####fill missing value Asset_Grade_Assessment by unknown
status = []
for i in range(0,len(table)):
    
    value = table['asset_grade_assessment'][i]

    if value in ['I','N','U']:
        status.append(value)
    elif value in ['W1','W2']:
        status.append('W')
    elif pd.isna(value):
        status.append('Unknown')
    else:
        status.append('Normal')

table['Car_Status'] = status
##3.3 Feature Engineering
###3.3.1 Car_Type
conditions_car_type = [
    (table["sub_model_code"].str.contains(",EV)",na=False,regex=False)) | 
    (table['sub_model_code'].str.contains("(EV)",na=False,regex=False)) |
    (table['sub_model_code'].str.startswith("EV",na=False)),
    (table["sub_model_code"].str.contains("HEV",na=False,regex=False)) |
    (table["sub_model_code"].str.contains("HYBRID",na=False,regex=False)) | 
    (table["fuel"] == 'Hybrid')
]

values = ["EV", "Hybrid"]

table["car_type"] = np.select(conditions_car_type, values, default="Motor")

###3.3.2 Full_Name
# table['Full_Name'] = ''
full_name_list = []
for i in range(0,len(table)):
    full_name_list.append(str(table['brand_name'][i])+'-'+str(table['model_name'][i])+'-'+str(table['sub_model_code'][i]))

table['Full_Name'] = full_name_list 

###3.3.3 Grade Score
grade_list = []

for i in range(0,len(table)):
    grade = table['asset_grade'][i]

    if grade == 'I':
        grade_list.append(0)
    else:
        grade_list.append(grade)

table['Grade_Score'] = grade_list

###3.3.4 Car Age
current_date = datetime.now()
current_year = current_date.strftime('%Y')
table['Car_Age'] = table['auction_date'].dt.year- table['asset_register_year']

###3.3.5 Mile_Per_Year
table['Mile_Per_Year'] = table['Mile_Transform'] / table['Car_Age']

###3.3.6 Seasonal Field
table["auction_date"] = pd.to_datetime(table["auction_date"])
table["auction_year"] = table["auction_date"].dt.year
table["auction_month_num"] = table["auction_date"].dt.month
table["auction_month"] = table["auction_date"].dt.to_period("M").dt.to_timestamp()
table["auction_quarter"] = table["auction_date"].dt.quarter


luxury_ultra  = ['Porsche','Denza','Tesla','GWM Tank','Jaecoo','DEEPAL',
                     'Land Rover','Lexus','Aion','Audi','Mercedes-Benz','BMW','Jaguar']
luxury_mid    = ['Peugeot','Haval','Hyundai','BYD','ORA','MINI','TR',
                    'Omoda','Kia','Volvo','Citroen','MG','Volkswagen','Wuling','Subaru']
mainstream    = ['Toyota','Ford','Mitsubishi','Mazda','Isuzu','Honda','Suzuki','Foton','Neta']
budget        = ['Jeep','Chevrolet','Nissan','Volt','Tata','Proton']

def tier(b):
    if b in luxury_ultra: return 4
    if b in luxury_mid:   return 3
    if b in mainstream:   return 2
    if b in budget:       return 1
    return 2

table['Brand_Tier'] = table['brand_name'].fillna('Unknown').apply(tier)
table['Car_Age_Bucket']      = pd.cut(table['Car_Age'], bins=[-1,2,5,8,12,20,100], labels=[5,4,3,2,1,0]).astype(float)
table['Mile_Bucket']         = pd.cut(table['Mile_Transform'], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)
table['BrandTier_x_Age']     = table['Brand_Tier'] / table['Car_Age'].clip(lower=1)
table['Age_x_Mile']          = table['Car_Age'] * table['Mile_Transform'] / 1e6
table['Engine_x_BrandTier']  = table['engine_size'] * table['Brand_Tier']
brand_median = pd.DataFrame(table.groupby('brand_name')['sold_amount'].median().rename('B_Median').reset_index())
model_median = pd.DataFrame(table.groupby(['brand_name','model_name'])['sold_amount'].median().rename('BM_Median').reset_index())
sub_model_median = pd.DataFrame(table.groupby(['brand_name','model_name','sub_model_code'])['sold_amount'].median().rename('BMS_Median').reset_index())

table = table.merge(brand_median, on = 'brand_name', how = 'left')
table = table.merge(model_median, on = ['brand_name','model_name'], how = 'left')

table['year_of_manufacture'] = table['year_of_manufacture'].astype(int)
table['vat_amount'] = table['vat_amount'].astype(float)
table['sold_amount'] = table['sold_amount'].astype(float)
table['newprice'] = table['newprice'].astype(float)
table['BrandTier_x_Age'] = table['BrandTier_x_Age'].astype(float)
table['Age_x_Mile'] = table['Age_x_Mile'].astype(float)
table['Engine_x_BrandTier'] = table['Engine_x_BrandTier'].astype(float)
table['B_Median'] = table['B_Median'].astype(float)
table['BM_Median'] = table['BM_Median'].astype(float)

# ml
def ml_predict(model_name,input_data):
    input_df = pd.DataFrame(input_data)
    model = joblib.load(model_name)
    prediction = model.predict(input_df)
    pred = prediction[0] if len(prediction) else 0
    return float(pred)


def parse_engine_size_from_text(engine_text):
    if not engine_text:
        return 0
    text = str(engine_text).strip()
    if text in ("-", "—"):
        return 0
    # Prefer engine capacity in parentheses, e.g. "1.2 (1193)" -> 1193
    in_paren = re.search(r"\((\d+(?:,\d{3})*(?:\.\d+)?)\)", text)
    if in_paren:
        try:
            return float(in_paren.group(1).replace(",", ""))
        except ValueError:
            pass
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return 0
    try:
        return float(match.group(0))
    except ValueError:
        return 0

# website
def home(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        first = ''
        for i in range(0,len(first_name)):
            if i == 0:
                first = first_name[i]
            else:
                pass

        last_name = request.user.last_name
        last = ''
        for i in range(0,len(last_name)):
            if i == 0:
                last = last_name[i]
            else:
                pass

        context = {
            'first': first,
            'last': last
        }
        return render(request, 'home.html',context=context)
    else:
        return render(request, 'login.html')

def viewside(request):
    return render(request, 'side.html')

def signin(request):
    #return render("login.html")
    return render(request, 'login.html')

def login(request):
    username = request.POST['username']
    password = request.POST['password']
    
    #check username and password 
    user = auth.authenticate(username=username,password=password)
    
    #get data for condition to see
    
    #check data
    if user is not None :
        auth.login(request,user)
        return redirect('/greenbook/home')
    else :
        messages.info(request,'Invalid username or password.')
        return redirect('/greenbook/signin')

def logout(request):
    auth.logout(request)
    return redirect('/greenbook/signin')

def predict_view(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        first = ''
        for i in range(0,len(first_name)):
            if i == 0:
                first = first_name[i]
            else:
                pass

        last_name = request.user.last_name
        last = ''
        for i in range(0,len(last_name)):
            if i == 0:
                last = last_name[i]
            else:
                pass
        
        #choice brand
        brands = asset_sold_car_test.objects.values_list('brand_name',flat=True).distinct().order_by('brand_name')

        #choice model
        model_list = asset_sold_car_test.objects.values_list('model_name',flat=True).distinct().order_by('model_name')

        #choice sub-model
        sub_model_list = asset_sold_car_test.objects.values_list('sub_model_code',flat=True).distinct().order_by('sub_model_code')
        #choice year manufacture
        year_manu_list = asset_sold_car_test.objects.values_list('year_of_manufacture',flat=True).distinct().order_by('year_of_manufacture')

        context = {
            'first': first,
            'last': last,
            'brands' : brands,
            'model_list' :model_list,
            'sub_model_list' : sub_model_list,
            'year_manu_list' : year_manu_list,
        }
        return render(request, 'prediction.html',context = context)
    else:
        return render(request, 'login.html')


def predict_option(request):
    brand = request.GET.get("brand_name", "").strip()
    model = request.GET.get("model_name", "").strip()
    sub_model = request.GET.get("sub_model", "").strip()
    year_manu = request.GET.get("year_of_manufacture", "").strip()
    year_int = int(year_manu) if year_manu.isdigit() else None

    qs = asset_sold_car_test.objects.all()
    gb = greenbook.objects.all()

    # model choices: filter ตาม brand เท่านั้น
    model_qs = qs
    if brand:
        model_qs = model_qs.filter(brand_name=brand)

    models = (
        model_qs.exclude(model_name__isnull=True)
        .exclude(model_name__exact="")
        .values_list("model_name", flat=True)
        .distinct()
        .order_by("model_name")
    )

    # sub_model choices: filter ตาม brand + model
    sub_model_qs = qs
    if brand:
        sub_model_qs = sub_model_qs.filter(brand_name=brand)
    if model:
        sub_model_qs = sub_model_qs.filter(model_name=model)

    sub_models = (
        sub_model_qs.exclude(sub_model_code__isnull=True)
        .exclude(sub_model_code__exact="")
        .values_list("sub_model_code", flat=True)
        .distinct()
        .order_by("sub_model_code")
    )

    # year choices: filter ตาม brand + model + sub_model
    year_qs = qs
    if brand:
        year_qs = year_qs.filter(brand_name=brand)
    if model:
        year_qs = year_qs.filter(model_name=model)
    if sub_model:
        year_qs = year_qs.filter(sub_model_code=sub_model)

    years = (
        year_qs.exclude(year_of_manufacture__isnull=True)
        .values_list("year_of_manufacture", flat=True)
        .distinct()
        .order_by("-year_of_manufacture")
    )

    # car detail -> แสดงเมื่อเลือกครบ
    detail = {
        "car_type" : "",
        "gear": "",
        "asset_group": "",
        "fuel": "",
        "engine": "",
        "detail_found": False,
    }

    fallback_detail_choices = {
        "car_types": sorted(
            [str(v) for v in table["car_type"].dropna().unique().tolist() if str(v).strip()]
        ),
        "gears": list(
            qs.exclude(asset_gear__isnull=True)
            .exclude(asset_gear__exact="")
            .values_list("asset_gear", flat=True)
            .distinct()
            .order_by("asset_gear")
        ),
        "asset_groups": list(
            qs.exclude(asset_group_name__isnull=True)
            .exclude(asset_group_name__exact="")
            .values_list("asset_group_name", flat=True)
            .distinct()
            .order_by("asset_group_name")
        ),
        "fuels": list(
            gb.exclude(fuel__isnull=True)
            .exclude(fuel__exact="")
            .values_list("fuel", flat=True)
            .distinct()
            .order_by("fuel")
        ),
    }

    if brand and model and sub_model and year_manu:
        detail_qs = qs.filter(
            brand_name=brand,
            model_name=model,
            sub_model_code=sub_model,
            year_of_manufacture=year_int
        ).first()

        if detail_qs:
            sub_key = detail_qs.sub_key
            detail_qs2 = gb.filter(vehiclekey=sub_key).first()

            sub_model_code_trans = str(sub_model).upper()
            sub_model_code_trans = sub_model_code_trans.replace(' ', '')
            sub_model_code_trans = sub_model_code_trans.replace('-', '')
            sub_model_code_trans = sub_model_code_trans.replace('(NEW)', '')

            print(sub_model_code_trans)
            if sub_model_code_trans in ('NAN', 'NaN', 'Nan', 'nan', ''):
                sub_model_code_trans = np.nan

            car_type_qs = table[
                (table['brand_name'] == brand)
                & (table['model_name'] == model)
                & (table['sub_model_code'] == sub_model_code_trans)
                & (table['year_of_manufacture'] == year_int)
            ]["car_type"]
            car_type = str(car_type_qs.values[0]) if not car_type_qs.empty else ""
            engine_desc = ""
            if detail_qs2 and detail_qs2.enginedescription is not None:
                engine_desc = str(detail_qs2.enginedescription)

            engine_size = ""
            if detail_qs.engine_size is not None:
                engine_size = str(detail_qs.engine_size)

            if engine_desc and engine_size:
                engine_text = f"{engine_desc} ({engine_size})"
            else:
                engine_text = engine_desc or engine_size

            gb_fuel = ""
            if detail_qs2 and detail_qs2.fuel is not None:
                gb_fuel = str(detail_qs2.fuel).strip()

            detail = {
                "car_type": car_type,
                "gear": detail_qs.asset_gear or "",
                "asset_group": detail_qs.asset_group_name or "",
                "fuel": gb_fuel,
                "engine": engine_text,
                "detail_found": True,
                "new_price": detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else 0,
            }
    #print(detail)

    return JsonResponse({
    "models": list(models),
    "sub_models": list(sub_models),
    "years": list(years),
    "car_detail" : detail,
    "fallback_detail_choices": fallback_detail_choices,
})


@require_POST
def predict_price(request):
    brand = request.POST.get("brand_name", "").strip()
    model = request.POST.get("model_name", "").strip()
    sub_model = request.POST.get("sub_model", "").strip()
    year_raw = request.POST.get("year_of_manufacture", "").strip()
    register_year_raw = request.POST.get("asset_register_year", "").strip()
    mile_raw = request.POST.get("mile", "").strip()
    historical = request.POST.get("historical", "").strip()
    grade = request.POST.get("grade", "").strip().upper()
    gear = request.POST.get("gear", "").strip()
    asset_group = request.POST.get("asset_group", "").strip()
    engine = request.POST.get("engine", "").strip()
    fuel_post = request.POST.get("fuel", "").strip()
    fuel = fuel_post
    new_price_raw = request.POST.get("new_price", "").strip()
    car_type = request.POST.get("car_type", "").strip()
    
    if not (brand and model and sub_model and year_raw):
        return JsonResponse({
            "ok": False,
            "message": "Please select brand, model, sub model, and year first."
        }, status=400)

    try:
        year = int(year_raw)
    except ValueError:
        return JsonResponse({"ok": False, "message": "Invalid manufacture year."}, status=400)

    register_year = None
    if register_year_raw:
        try:
            register_year = int(float(register_year_raw))
        except ValueError:
            register_year = None

    mileage = 0
    mileage_list = []
    if mile_raw:
        mileage =int(float(mile_raw))
        mileage_list.append(mileage)
    elif not mile_raw:
        mileage_list.append(10000)
        mileage_list.append(50000)
        mileage_list.append(100000)
        mileage_list.append(150000)
        mileage_list.append(200000)

    grade_list = []
    if grade:
        grade_list.append(grade)
    elif not grade:
        grade_list.append(1)
        grade_list.append(2)
        grade_list.append(3)
        grade_list.append(4)
        grade_list.append(5)


    base_filter = asset_sold_car_test.objects.filter(
        brand_name=brand,
        model_name=model,
        sub_model_code=sub_model,
        year_of_manufacture=year,
    )
    sub_model_norm = str(sub_model).upper().replace(" ", "").replace("-", "").replace("(NEW)", "")
    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    manual_newprice = 0
    if new_price_raw:
        try:
            manual_newprice = float(new_price_raw)
        except ValueError:
            manual_newprice = 0

    base_filter_first = base_filter.first()
    asset_group_code = ""
    engine_size = parse_engine_size_from_text(engine)
    newprice = 0

    if base_filter_first:
        sub_key = base_filter_first.sub_key
        detail_qs2 = greenbook.objects.filter(vehiclekey=sub_key).first()
        if not fuel_post:
            fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        #fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        asset_group_code = base_filter_first.asset_group_code or ""
        if not engine_size:
            engine_size = base_filter_first.engine_size or 0
        newprice = detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else manual_newprice
    elif asset_group:
        asset_group_code = (
            asset_sold_car_test.objects.filter(asset_group_name=asset_group)
            .exclude(asset_group_code__isnull=True)
            .exclude(asset_group_code__exact="")
            .values_list("asset_group_code", flat=True)
            .first()
            or ""
        )
    if (not base_filter_first) and manual_newprice > 0:
        newprice = manual_newprice

    #historical transform
    if historical == "no-accident":
        historical_factor = "Normal"
    elif historical == "flood":
        historical_factor = "W"
    elif historical == "unmoved-engine":
        historical_factor = "N"
    elif historical == "unmoved":
        historical_factor = "U"
    else:
        historical_factor = "Unknown"

    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    age = int(datetime.now().strftime("%Y")) - register_year if register_year is not None else 0
    car_age_bucket = pd.cut([age], bins=[-1, 10, 20, 30, 40, 50, 1e9], labels=[5, 4, 3, 2, 1, 0]).astype(float)[0]
    is_multi = len(mileage_list) > 1 or len(grade_list) > 1
    results = []
    if car_type == "EV":
        fuel = "Electric"
    
    message = "Please"
    if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical or (year > register_year):
        if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical:
            message = " input "
            if not car_type:
                message += "Car type, "
            if not gear:
                message += "Gear, "
            if not asset_group:
                message += "Asset Group, "
            if not engine:
                message += "Engine, "
            if not newprice:
                message += "New price, "
            if not fuel:
                message += "Fuel, "
            if not register_year:
                message += "Asset Register year, "
            if not historical:
                message += "Historical, "
            message += "please."
        if year > register_year:
            message += " register year could more than year of manufacture"

        return JsonResponse({
            "ok": False,
            "message": message
        }, status=400)
    else:
        if car_filter.empty:
            for m in mileage_list:
                for g in grade_list:
                    sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                    mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                    Age_x_Mile = age * m
                    
                    if car_type == "EV":
                            
                        input_data = [{
                            "Brand_Name": brand,
                            "Model_Name": model,
                            "Sub_Model_Code": sub_model_code_trans,
                            "Fuel": fuel,
                            "Asset_Gear": gear,
                            "Asset_Group_Code": asset_group_code,
                            "Car_Status": historical_factor,
                            "Car_Type": car_type,
                            "Year_of_Manufacture": year,
                            "Asset_Register_Year": register_year,
                            "Car_Age": age,
                            "Car_Age_Bucket": car_age_bucket,
                            "Mile_Transform": m,
                            "NewPrice": newprice,
                            "Grade_Score": g,
                            "Mile_Bucket":mile_bucket,
                            "Age_x_Mile":Age_x_Mile,
                        }]
                        
                        model_predict_name = 'greenbook/models/Normal/Special/ev.pkl'
                    else:
                            
                        input_data = [{
                            "Brand_Name": brand,
                            "Model_Name": model,
                            "Sub_Model_Code": sub_model_code_trans,
                            "Fuel": fuel,
                            "Asset_Gear": gear,
                            "Asset_Group_Code": asset_group_code,
                            "Car_Status": historical_factor,
                            "Car_Type": car_type,
                            "Year_of_Manufacture": year,
                            "Engine_Size": engine_size,
                            "Asset_Register_Year": register_year,
                            "Car_Age": age,
                            "Car_Age_Bucket": car_age_bucket,
                            "Mile_Transform": m,
                            "NewPrice": newprice,
                            "Grade_Score": g,
                            "Mile_Bucket":mile_bucket,
                            "Age_x_Mile":Age_x_Mile,
                        }]
                        model_predict_name = 'greenbook/models/Normal/Special/n_ev.pkl'

                    predicted = int(round(ml_predict(model_predict_name,input_data)))
                    min_price = int(round(predicted * 0.95))
                    max_price = int(round(predicted * 1.05))

                    results.append({
                        "grade": int(g),
                        "mileage": int(m),
                        "predicted": predicted,
                        "min_price": min_price,
                        "max_price": max_price,
                    })
        else:
            #engineer feature
            B_Median = car_filter['B_Median'].median()
            brand_tier = car_filter['Brand_Tier'].unique()[0]
            BM_Median = car_filter['BM_Median'].median()

            car_filter_1 = car_filter.sort_values("auction_date")

            avg_price_lag_1_list = list(car_filter_1["sold_amount"][-1:].values)
            if len(avg_price_lag_1_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_1 = median_price
            else:
                avg_price_lag_1 = avg_price_lag_1_list[0]
            avg_price_lag_3_list = list(car_filter_1["sold_amount"][-3:].values)
            if len(avg_price_lag_3_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_3 = median_price
            else:
                avg_price_lag_3 = avg_price_lag_3_list[0]
            avg_price_roll_3_list = car_filter_1["sold_amount"][-3:].values.mean()
            if  not avg_price_roll_3_list :
                median_price = car_filter_1["sold_amount"].median()
                avg_price_roll_3 = median_price
            else:
                avg_price_roll_3 = avg_price_roll_3_list
            
            market_df = (
                car_filter.groupby("auction_month")["sold_amount"]
                .mean()
                .reset_index()
                .rename(columns={"sold_amount": "market_median_price"})
            )

            market_df = market_df.sort_values("auction_month")
            market_price_lag_1_list = list(market_df["market_median_price"][-1:].values)

            if len(market_price_lag_1_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_1 = median_price
            else:
                market_price_lag_1 = market_price_lag_1_list[0]
            market_price_lag_2_list = list(market_df["market_median_price"][-2:].values)
            if len(market_price_lag_2_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_2 = median_price
            else:
                market_price_lag_2 = market_price_lag_2_list[0]
            market_price_lag_3_list = list(market_df["market_median_price"][-3:].values)
            if len(market_price_lag_3_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_3 = median_price
            else:
                market_price_lag_3 = market_price_lag_3_list[0]
            market_price_roll_3_list = market_df["market_median_price"][-3:].values.mean()
            if not market_price_roll_3_list:
                median_price = market_df["market_median_price"].median()
                market_price_roll_3 = median_price
            else:
                market_price_roll_3 = market_price_roll_3_list
            
            BrandTier_x_Age = brand_tier * car_age_bucket
            Engine_x_BrandTier = engine_size * brand_tier
            Car_Type = car_filter["car_type"].unique()[0]

            for m in mileage_list:
                for g in grade_list:
                    sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                    mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                    Age_x_Mile = age * m
            
                    input_data = [{
                        "Brand_Name": brand,
                        "Model_Name": model,
                        "Sub_Model_Code": sub_model_code_trans,
                        "Fuel": fuel,
                        "Asset_Gear": gear,
                        "Asset_Group_Code": asset_group_code,
                        "Car_Status": historical_factor,
                        "Year_of_Manufacture": year,
                        "Asset_Register_Year": register_year,
                        "Car_Age": age,
                        "Mile_Transform": m,
                        "Engine_Size": engine_size,
                        "NewPrice": newprice,
                        "Grade_Score": g,
                        "Mile_Bucket":mile_bucket,
                        "B_Median":B_Median,
                        "Car_Age_Bucket":car_age_bucket,
                        "Age_x_Mile":Age_x_Mile,
                        "avg_price_lag_1":avg_price_lag_1,
                        "avg_price_lag_3":avg_price_lag_3,
                        "avg_price_roll_3":avg_price_roll_3,
                        "market_price_roll_3":market_price_roll_3,
                        "market_price_lag_1":market_price_lag_1,
                        "market_price_lag_2":market_price_lag_2,
                        "BrandTier_x_Age":BrandTier_x_Age,
                        "Brand_Tier":brand_tier,
                        "Engine_x_BrandTier":Engine_x_BrandTier,
                        "BM_Median":BM_Median,
                        "market_price_lag_3":market_price_lag_3,
                    }]

                    model_predict_name = f'greenbook/models/Normal/{Car_Type}/{brand}.pkl'
                    predicted = int(round(ml_predict(model_predict_name,input_data)))
                    min_price = int(round(predicted * 0.95))
                    max_price = int(round(predicted * 1.05))

                    results.append({
                        "grade": int(g),
                        "mileage": int(m),
                        "predicted": predicted,
                        "min_price": min_price,
                        "max_price": max_price,
                    })

    # Sales transaction history (x=time, y=sold)
    history_qs = (
        base_filter.exclude(auction_date__isnull=True)
        .order_by("auction_date")
        .values("auction_date", "sold_amount")
    )

    history_labels = []
    history_values = []
    for row in history_qs:
        sold_value = row["sold_amount"]
        if not sold_value:
            continue

        history_labels.append(row["auction_date"].strftime("%Y-%m-%d"))
        history_values.append(float(sold_value))

    history_message = "" if history_values else "ไม่พบข้อมูลการขายในอดีต"

    if is_multi:
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"register year {register_year if register_year else '-'}, "
            f"history {historical if historical else '-'}."
        )
    else:
        r = results[0]
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"register year {register_year if register_year else '-'}, "
            f"mileage {r['mileage']:,} km, grade {r['grade']}, "
            f"history {historical if historical else '-'}."
        )

    response_data = {
        "ok": True,
        "is_multi": is_multi,
        "grade_values": sorted(set(int(g) for g in grade_list)),
        "mileage_values": sorted(set(int(m) for m in mileage_list)),
        "results": results,
        "brand_model": f"{brand} {model} {year}",
        "year": year,
        "newprice": newprice,
        "fuel": fuel,
        "summary": summary,
        "history_labels": history_labels,
        "history_values": history_values,
        "history_message": history_message,
        "car_detail": {
            "gear": gear,
            "asset_group": asset_group,
            "engine": engine,
        },
    }

    if not is_multi:
        r = results[0]
        response_data["predicted_price"] = r["predicted"]
        response_data["min_price"] = r["min_price"]
        response_data["max_price"] = r["max_price"]
        response_data["mile"] = r["mileage"]

    return JsonResponse(response_data)


def branch_predict_view(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        first = ''
        for i in range(0,len(first_name)):
            if i == 0:
                first = first_name[i]
            else:
                pass

        last_name = request.user.last_name
        last = ''
        for i in range(0,len(last_name)):
            if i == 0:
                last = last_name[i]
            else:
                pass
        
        #choice brand
        brands = asset_sold_car_test.objects.values_list('brand_name',flat=True).distinct().order_by('brand_name')

        #choice model
        model_list = asset_sold_car_test.objects.values_list('model_name',flat=True).distinct().order_by('model_name')

        #choice sub-model
        sub_model_list = asset_sold_car_test.objects.values_list('sub_model_code',flat=True).distinct().order_by('sub_model_code')
        #choice year manufacture
        year_manu_list = asset_sold_car_test.objects.values_list('year_of_manufacture',flat=True).distinct().order_by('year_of_manufacture')

        branch_list = asset_sold_car_test.objects.values_list('branch_name',flat=True).distinct().order_by('branch_name')

        context = {
            'first': first,
            'last': last,
            'brands' : brands,
            'model_list' :model_list,
            'sub_model_list' : sub_model_list,
            'year_manu_list' : year_manu_list,
            'branch_list' : branch_list,
        }
        return render(request, 'branch_prediction.html',context = context)
    else:
        return render(request, 'login.html')


def branch_predict_option(request):
    brand = request.GET.get("brand_name", "").strip()
    model = request.GET.get("model_name", "").strip()
    sub_model = request.GET.get("sub_model", "").strip()
    year_manu = request.GET.get("year_of_manufacture", "").strip()
    year_int = int(year_manu) if year_manu.isdigit() else None

    qs = asset_sold_car_test.objects.all()
    gb = greenbook.objects.all()

    # model choices: filter ตาม brand เท่านั้น
    model_qs = qs
    if brand:
        model_qs = model_qs.filter(brand_name=brand)

    models = (
        model_qs.exclude(model_name__isnull=True)
        .exclude(model_name__exact="")
        .values_list("model_name", flat=True)
        .distinct()
        .order_by("model_name")
    )

    # sub_model choices: filter ตาม brand + model
    sub_model_qs = qs
    if brand:
        sub_model_qs = sub_model_qs.filter(brand_name=brand)
    if model:
        sub_model_qs = sub_model_qs.filter(model_name=model)

    sub_models = (
        sub_model_qs.exclude(sub_model_code__isnull=True)
        .exclude(sub_model_code__exact="")
        .values_list("sub_model_code", flat=True)
        .distinct()
        .order_by("sub_model_code")
    )

    # year choices: filter ตาม brand + model + sub_model
    year_qs = qs
    if brand:
        year_qs = year_qs.filter(brand_name=brand)
    if model:
        year_qs = year_qs.filter(model_name=model)
    if sub_model:
        year_qs = year_qs.filter(sub_model_code=sub_model)

    years = (
        year_qs.exclude(year_of_manufacture__isnull=True)
        .values_list("year_of_manufacture", flat=True)
        .distinct()
        .order_by("-year_of_manufacture")
    )

    # car detail -> แสดงเมื่อเลือกครบ
    detail = {
        "car_type" : "",
        "gear": "",
        "asset_group": "",
        "fuel": "",
        "engine": "",
        "detail_found": False,
    }

    fallback_detail_choices = {
        "car_types": sorted(
            [str(v) for v in table["car_type"].dropna().unique().tolist() if str(v).strip()]
        ),
        "gears": list(
            qs.exclude(asset_gear__isnull=True)
            .exclude(asset_gear__exact="")
            .values_list("asset_gear", flat=True)
            .distinct()
            .order_by("asset_gear")
        ),
        "asset_groups": list(
            qs.exclude(asset_group_name__isnull=True)
            .exclude(asset_group_name__exact="")
            .values_list("asset_group_name", flat=True)
            .distinct()
            .order_by("asset_group_name")
        ),
        "fuels": list(
            gb.exclude(fuel__isnull=True)
            .exclude(fuel__exact="")
            .values_list("fuel", flat=True)
            .distinct()
            .order_by("fuel")
        ),
    }

    if brand and model and sub_model and year_manu:
        detail_qs = qs.filter(
            brand_name=brand,
            model_name=model,
            sub_model_code=sub_model,
            year_of_manufacture=year_int
        ).first()

        if detail_qs:
            sub_key = detail_qs.sub_key
            detail_qs2 = gb.filter(vehiclekey=sub_key).first()

            sub_model_code_trans = str(sub_model).upper()
            sub_model_code_trans = sub_model_code_trans.replace(' ', '')
            sub_model_code_trans = sub_model_code_trans.replace('-', '')
            sub_model_code_trans = sub_model_code_trans.replace('(NEW)', '')

            print(sub_model_code_trans)
            if sub_model_code_trans in ('NAN', 'NaN', 'Nan', 'nan', ''):
                sub_model_code_trans = np.nan

            car_type_qs = table[
                (table['brand_name'] == brand)
                & (table['model_name'] == model)
                & (table['sub_model_code'] == sub_model_code_trans)
                & (table['year_of_manufacture'] == year_int)
            ]["car_type"]
            car_type = str(car_type_qs.values[0]) if not car_type_qs.empty else ""
            engine_desc = ""
            if detail_qs2 and detail_qs2.enginedescription is not None:
                engine_desc = str(detail_qs2.enginedescription)

            engine_size = ""
            if detail_qs.engine_size is not None:
                engine_size = str(detail_qs.engine_size)

            if engine_desc and engine_size:
                engine_text = f"{engine_desc} ({engine_size})"
            else:
                engine_text = engine_desc or engine_size

            gb_fuel = ""
            if detail_qs2 and detail_qs2.fuel is not None:
                gb_fuel = str(detail_qs2.fuel).strip()

            detail = {
                "car_type": car_type,
                "gear": detail_qs.asset_gear or "",
                "asset_group": detail_qs.asset_group_name or "",
                "fuel": gb_fuel,
                "engine": engine_text,
                "detail_found": True,
                "new_price": detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else 0,
            }
    #print(detail)

    return JsonResponse({
    "models": list(models),
    "sub_models": list(sub_models),
    "years": list(years),
    "car_detail" : detail,
    "fallback_detail_choices": fallback_detail_choices,
})


@require_POST
def branch_predict_price(request):
    brand = request.POST.get("brand_name", "").strip()
    model = request.POST.get("model_name", "").strip()
    sub_model = request.POST.get("sub_model", "").strip()
    year_raw = request.POST.get("year_of_manufacture", "").strip()
    register_year_raw = request.POST.get("asset_register_year", "").strip()
    mile_raw = request.POST.get("mile", "").strip()
    historical = request.POST.get("historical", "").strip()
    branch = request.POST.get("branch", "").strip()
    grade = request.POST.get("grade", "").strip().upper()
    gear = request.POST.get("gear", "").strip()
    asset_group = request.POST.get("asset_group", "").strip()
    engine = request.POST.get("engine", "").strip()
    fuel_post = request.POST.get("fuel", "").strip()
    fuel = fuel_post
    new_price_raw = request.POST.get("new_price", "").strip()
    car_type = request.POST.get("car_type", "").strip()
    # region agent log
    with open("debug-bc8fa5.log", "a", encoding="utf-8") as _dbg:
        _dbg.write(json.dumps({"sessionId":"bc8fa5","runId":"pre-fix","hypothesisId":"H1","location":"views.py:1156","message":"branch_predict_price entry","data":{"branch_raw":branch,"brand":brand,"model":model,"sub_model":sub_model,"year_raw":year_raw,"mile_raw":mile_raw,"grade_raw":grade},"timestamp":int(time.time()*1000)}, ensure_ascii=False) + "\n")
    # endregion
    
    if not (brand and model and sub_model and year_raw):
        return JsonResponse({
            "ok": False,
            "message": "Please select brand, model, sub model, and year first."
        }, status=400)

    try:
        year = int(year_raw)
    except ValueError:
        return JsonResponse({"ok": False, "message": "Invalid manufacture year."}, status=400)

    register_year = None
    if register_year_raw:
        try:
            register_year = int(float(register_year_raw))
        except ValueError:
            register_year = None

    mileage = 0
    mileage_list = []
    if mile_raw:
        mileage =int(float(mile_raw))
        mileage_list.append(mileage)
    elif not mile_raw:
        mileage_list.append(10000)
        mileage_list.append(50000)
        mileage_list.append(100000)
        mileage_list.append(150000)
        mileage_list.append(200000)

    grade_list = []
    if grade:
        grade_list.append(grade)
    elif not grade:
        grade_list.append(1)
        grade_list.append(2)
        grade_list.append(3)
        grade_list.append(4)
        grade_list.append(5)


    base_filter = asset_sold_car_test.objects.filter(
        brand_name=brand,
        model_name=model,
        sub_model_code=sub_model,
        year_of_manufacture=year,
    )
    sub_model_norm = str(sub_model).upper().replace(" ", "").replace("-", "").replace("(NEW)", "")
    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    manual_newprice = 0
    if new_price_raw:
        try:
            manual_newprice = float(new_price_raw)
        except ValueError:
            manual_newprice = 0

    base_filter_first = base_filter.first()
    asset_group_code = ""
    engine_size = parse_engine_size_from_text(engine)
    newprice = 0

    if base_filter_first:
        sub_key = base_filter_first.sub_key
        detail_qs2 = greenbook.objects.filter(vehiclekey=sub_key).first()
        if not fuel_post:
            fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        #fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        asset_group_code = base_filter_first.asset_group_code or ""
        if not engine_size:
            engine_size = base_filter_first.engine_size or 0
        newprice = detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else manual_newprice
    elif asset_group:
        asset_group_code = (
            asset_sold_car_test.objects.filter(asset_group_name=asset_group)
            .exclude(asset_group_code__isnull=True)
            .exclude(asset_group_code__exact="")
            .values_list("asset_group_code", flat=True)
            .first()
            or ""
        )
    if (not base_filter_first) and manual_newprice > 0:
        newprice = manual_newprice

    #historical transform
    if historical == "no-accident":
        historical_factor = "Normal"
    elif historical == "flood":
        historical_factor = "W"
    elif historical == "unmoved-engine":
        historical_factor = "N"
    elif historical == "unmoved":
        historical_factor = "U"
    else:
        historical_factor = "Unknown"

    #branch transform
    if branch == "Bangkok":
        branch_name = "กรุงเทพมหานคร"
    elif branch == "Nakhon Ratchasima":
        branch_name = "นครราชสีมา"
    elif branch == "Pattaya":
        branch_name = "พัทยา"
    elif branch == "Rangsit klong 8":
        branch_name = "รังสิต คลอง 8"
    elif branch == "Songkhla":
        branch_name = "สงขลา"   
    elif branch == "Surat Thani":
        branch_name = "สุราษฎร์ธานี"
    elif branch == "Udon Thani":
        branch_name = "อุดรธานี"
    elif branch == "Chaing Mai":
        branch_name = "เชียงใหม่"
    elif branch == "Khon Kaen":
        branch_name = "ขอนแก่น"
    elif branch == "Ubon Ratchathani":
        branch_name = "อุบลราชธานี"
    elif branch == "Rayong":
        branch_name = "ระยอง"
    elif branch == "Ratchaburi":
        branch_name = "ราชบุรี"
    else:
        branch_name = "Unknown"

    branch_list = []
    if branch:
        branch_list.append(branch_name)
    elif not branch:
        branch_list.append("กรุงเทพมหานคร")
        branch_list.append("นครราชสีมา")
        branch_list.append("พัทยา")
        branch_list.append("รังสิต คลอง 8")
        branch_list.append("สงขลา")
        branch_list.append("สุราษฎร์ธานี")
        branch_list.append("อุดรธานี")
        branch_list.append("เชียงใหม่")
        branch_list.append("ขอนแก่น")
        branch_list.append("อุบลราชธานี")
        branch_list.append("ระยอง")
        branch_list.append("ราชบุรี")
    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    age = int(datetime.now().strftime("%Y")) - register_year if register_year is not None else 0
    car_age_bucket = pd.cut([age], bins=[-1, 10, 20, 30, 40, 50, 1e9], labels=[5, 4, 3, 2, 1, 0]).astype(float)[0]
    is_multi = len(branch_list) > 1 or len(mileage_list) > 1 or len(grade_list) > 1
    results = []
    if car_type == "EV":
        fuel = "Electric"
    
    message = "Please"
    if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical or (year > register_year):
        if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical:
            message = " input "
            if not car_type:
                message += "Car type, "
            if not gear:
                message += "Gear, "
            if not asset_group:
                message += "Asset Group, "
            if not engine:
                message += "Engine, "
            if not newprice:
                message += "New price, "
            if not fuel:
                message += "Fuel, "
            if not register_year:
                message += "Asset Register year, "
            if not historical:
                message += "Historical, "
            message += "please."
        if year > register_year:
            message += " register year could more than year of manufacture"

        return JsonResponse({
            "ok": False,
            "message": message
        }, status=400)
    else:
        if car_filter.empty:
            for b in branch_list:
                for m in mileage_list:
                    for g in grade_list:
                        sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                        mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                        Age_x_Mile = age * m
                        
                        if car_type == "EV":
                                
                            input_data = [{
                                "Brand_Name": brand,
                                "Model_Name": model,
                                "Sub_Model_Code": sub_model_code_trans,
                                "Branch_Name" : b,
                                "Fuel": fuel,
                                "Asset_Gear": gear,
                                "Asset_Group_Code": asset_group_code,
                                "Car_Status": historical_factor,
                                "Car_Type": car_type,
                                "Year_of_Manufacture": year,
                                "Asset_Register_Year": register_year,
                                "Car_Age": age,
                                "Car_Age_Bucket": car_age_bucket,
                                "Mile_Transform": m,
                                "NewPrice": newprice,
                                "Grade_Score": g,
                                "Mile_Bucket":mile_bucket,
                                "Age_x_Mile":Age_x_Mile,
                            }]

                            model_predict_name = 'greenbook/models/Normal/Special/ev.pkl'
                        else:
                                
                            input_data = [{
                                "Brand_Name": brand,
                                "Model_Name": model,
                                "Sub_Model_Code": sub_model_code_trans,
                                "Branch_Name" : b,
                                "Fuel": fuel,
                                "Asset_Gear": gear,
                                "Asset_Group_Code": asset_group_code,
                                "Car_Status": historical_factor,
                                "Car_Type": car_type,
                                "Year_of_Manufacture": year,
                                "Engine_Size": engine_size,
                                "Asset_Register_Year": register_year,
                                "Car_Age": age,
                                "Car_Age_Bucket": car_age_bucket,
                                "Mile_Transform": m,
                                "NewPrice": newprice,
                                "Grade_Score": g,
                                "Mile_Bucket":mile_bucket,
                                "Age_x_Mile":Age_x_Mile,
                            }]

                            model_predict_name = 'greenbook/models/Normal/Special/n_ev.pkl'

                        predicted = int(round(ml_predict(model_predict_name,input_data)))
                        min_price = int(round(predicted * 0.95))
                        max_price = int(round(predicted * 1.05))

                        results.append({
                            "branch": b,
                            "grade": int(g),
                            "mileage": int(m),
                            "predicted": predicted,
                            "min_price": min_price,
                            "max_price": max_price,
                        })
        else:
            #engineer feature
            B_Median = car_filter['B_Median'].median()
            brand_tier = car_filter['Brand_Tier'].unique()[0]
            BM_Median = car_filter['BM_Median'].median()

            car_filter_1 = car_filter.sort_values("auction_date")

            avg_price_lag_1_list = list(car_filter_1["sold_amount"][-1:].values)
            if len(avg_price_lag_1_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_1 = median_price
            else:
                avg_price_lag_1 = avg_price_lag_1_list[0]
            avg_price_lag_3_list = list(car_filter_1["sold_amount"][-3:].values)
            if len(avg_price_lag_3_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_3 = median_price
            else:
                avg_price_lag_3 = avg_price_lag_3_list[0]
            avg_price_roll_3_list = car_filter_1["sold_amount"][-3:].values.mean()
            if  not avg_price_roll_3_list :
                median_price = car_filter_1["sold_amount"].median()
                avg_price_roll_3 = median_price
            else:
                avg_price_roll_3 = avg_price_roll_3_list
            
            market_df = (
                car_filter.groupby("auction_month")["sold_amount"]
                .mean()
                .reset_index()
                .rename(columns={"sold_amount": "market_median_price"})
            )

            market_df = market_df.sort_values("auction_month")
            market_price_lag_1_list = list(market_df["market_median_price"][-1:].values)

            if len(market_price_lag_1_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_1 = median_price
            else:
                market_price_lag_1 = market_price_lag_1_list[0]
            market_price_lag_2_list = list(market_df["market_median_price"][-2:].values)
            if len(market_price_lag_2_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_2 = median_price
            else:
                market_price_lag_2 = market_price_lag_2_list[0]
            market_price_lag_3_list = list(market_df["market_median_price"][-3:].values)
            if len(market_price_lag_3_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_3 = median_price
            else:
                market_price_lag_3 = market_price_lag_3_list[0]
            market_price_roll_3_list = market_df["market_median_price"][-3:].values.mean()
            if not market_price_roll_3_list:
                median_price = market_df["market_median_price"].median()
                market_price_roll_3 = median_price
            else:
                market_price_roll_3 = market_price_roll_3_list
            
            BrandTier_x_Age = brand_tier * age
            Engine_x_BrandTier = engine_size * brand_tier
            Car_Type = car_filter["car_type"].unique()[0]

            for b in branch_list:
                for m in mileage_list:
                    for g in grade_list:
                        sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                        mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                        Age_x_Mile = age * m
                        g_t = int(g)
                
                        input_data = [{
                            "Brand_Name": brand,
                            "Model_Name": model,
                            "Sub_Model_Code": sub_model_code_trans,
                            "Branch_Name" : b,
                            "Fuel": fuel,
                            "Asset_Gear": gear,
                            "Asset_Group_Code": asset_group_code,
                            "Car_Status": historical_factor,
                            "Year_of_Manufacture": year,
                            "Asset_Register_Year": register_year,
                            "Car_Age": age,
                            "Mile_Transform": m,
                            "Engine_Size": engine_size,
                            "NewPrice": newprice,
                            "Grade_Score": g_t,
                            "Mile_Bucket":mile_bucket,
                            "B_Median":B_Median,
                            "Car_Age_Bucket":car_age_bucket,
                            "Age_x_Mile":Age_x_Mile,
                            "avg_price_lag_1":avg_price_lag_1,
                            "avg_price_lag_3":avg_price_lag_3,
                            "avg_price_roll_3":avg_price_roll_3,
                            "market_price_roll_3":market_price_roll_3,
                            "market_price_lag_1":market_price_lag_1,
                            "market_price_lag_2":market_price_lag_2,
                            "BrandTier_x_Age":BrandTier_x_Age,
                            "Brand_Tier":brand_tier,
                            "Engine_x_BrandTier":Engine_x_BrandTier,
                            "BM_Median":BM_Median,
                            "market_price_lag_3":market_price_lag_3,
                        }]
                        

                        model_predict_name = f'greenbook/models/Branch/{Car_Type}/{brand}.pkl'
                        predicted = int(round(ml_predict(model_predict_name,input_data)))
                        min_price = int(round(predicted * 0.95))
                        max_price = int(round(predicted * 1.05))

                        results.append({
                            "branch": b,
                            "grade": int(g),
                            "mileage": int(m),
                            "predicted": predicted,
                            "min_price": min_price,
                            "max_price": max_price,
                        })

    # Sales transaction history (x=time, y=sold)
    history_qs = (
        base_filter.exclude(auction_date__isnull=True)
        .order_by("auction_date")
        .values("auction_date", "sold_amount")
    )

    history_labels = []
    history_values = []
    for row in history_qs:
        sold_value = row["sold_amount"]
        if not sold_value:
            continue

        history_labels.append(row["auction_date"].strftime("%Y-%m-%d"))
        history_values.append(float(sold_value))

    history_message = "" if history_values else "ไม่พบข้อมูลการขายในอดีต"

    if is_multi:
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"branch {branch_name if branch else 'all branches'}, "
            f"register year {register_year if register_year else '-'}, "
            f"history {historical if historical else '-'}."
        )
    else:
        r = results[0]
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"branch {r.get('branch', branch_name if branch else '-')}, "
            f"register year {register_year if register_year else '-'}, "
            f"mileage {r['mileage']:,} km, grade {r['grade']}, "
            f"history {historical if historical else '-'}."
        )

    response_data = {
        "ok": True,
        "is_multi": is_multi,
        "branch_values": sorted(set(b for b in branch_list)),
        "grade_values": sorted(set(int(g) for g in grade_list)),
        "mileage_values": sorted(set(int(m) for m in mileage_list)),
        "results": results,
        "brand_model": f"{brand} {model} {year}",
        "year": year,
        "newprice": newprice,
        "fuel": fuel,
        "branch": (results[0].get("branch") if results else (branch_name if branch else "")),
        "summary": summary,
        "history_labels": history_labels,
        "history_values": history_values,
        "history_message": history_message,
        "car_detail": {
            "gear": gear,
            "asset_group": asset_group,
            "engine": engine,
        },
    }

    if not is_multi:
        r = results[0]
        response_data["predicted_price"] = r["predicted"]
        response_data["min_price"] = r["min_price"]
        response_data["max_price"] = r["max_price"]
        response_data["mile"] = r["mileage"]

    return JsonResponse(response_data)



def seasonal_predict_view(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        first = ''
        for i in range(0,len(first_name)):
            if i == 0:
                first = first_name[i]
            else:
                pass

        last_name = request.user.last_name
        last = ''
        for i in range(0,len(last_name)):
            if i == 0:
                last = last_name[i]
            else:
                pass
        
        #choice brand
        brands = asset_sold_car_test.objects.values_list('brand_name',flat=True).distinct().order_by('brand_name')

        #choice model
        model_list = asset_sold_car_test.objects.values_list('model_name',flat=True).distinct().order_by('model_name')

        #choice sub-model
        sub_model_list = asset_sold_car_test.objects.values_list('sub_model_code',flat=True).distinct().order_by('sub_model_code')
        #choice year manufacture
        year_manu_list = asset_sold_car_test.objects.values_list('year_of_manufacture',flat=True).distinct().order_by('year_of_manufacture')

        branch_list = asset_sold_car_test.objects.values_list('branch_name',flat=True).distinct().order_by('branch_name')

        context = {
            'first': first,
            'last': last,
            'brands' : brands,
            'model_list' :model_list,
            'sub_model_list' : sub_model_list,
            'year_manu_list' : year_manu_list,
            'branch_list' : branch_list,
        }
        return render(request, 'seasonal_prediction.html',context = context)
    else:
        return render(request, 'login.html')


def seasonal_predict_option(request):
    brand = request.GET.get("brand_name", "").strip()
    model = request.GET.get("model_name", "").strip()
    sub_model = request.GET.get("sub_model", "").strip()
    year_manu = request.GET.get("year_of_manufacture", "").strip()
    year_int = int(year_manu) if year_manu.isdigit() else None

    qs = asset_sold_car_test.objects.all()
    gb = greenbook.objects.all()

    # model choices: filter ตาม brand เท่านั้น
    model_qs = qs
    if brand:
        model_qs = model_qs.filter(brand_name=brand)

    models = (
        model_qs.exclude(model_name__isnull=True)
        .exclude(model_name__exact="")
        .values_list("model_name", flat=True)
        .distinct()
        .order_by("model_name")
    )

    # sub_model choices: filter ตาม brand + model
    sub_model_qs = qs
    if brand:
        sub_model_qs = sub_model_qs.filter(brand_name=brand)
    if model:
        sub_model_qs = sub_model_qs.filter(model_name=model)

    sub_models = (
        sub_model_qs.exclude(sub_model_code__isnull=True)
        .exclude(sub_model_code__exact="")
        .values_list("sub_model_code", flat=True)
        .distinct()
        .order_by("sub_model_code")
    )

    # year choices: filter ตาม brand + model + sub_model
    year_qs = qs
    if brand:
        year_qs = year_qs.filter(brand_name=brand)
    if model:
        year_qs = year_qs.filter(model_name=model)
    if sub_model:
        year_qs = year_qs.filter(sub_model_code=sub_model)

    years = (
        year_qs.exclude(year_of_manufacture__isnull=True)
        .values_list("year_of_manufacture", flat=True)
        .distinct()
        .order_by("-year_of_manufacture")
    )

    # car detail -> แสดงเมื่อเลือกครบ
    detail = {
        "car_type" : "",
        "gear": "",
        "asset_group": "",
        "fuel": "",
        "engine": "",
        "detail_found": False,
    }

    fallback_detail_choices = {
        "car_types": sorted(
            [str(v) for v in table["car_type"].dropna().unique().tolist() if str(v).strip()]
        ),
        "gears": list(
            qs.exclude(asset_gear__isnull=True)
            .exclude(asset_gear__exact="")
            .values_list("asset_gear", flat=True)
            .distinct()
            .order_by("asset_gear")
        ),
        "asset_groups": list(
            qs.exclude(asset_group_name__isnull=True)
            .exclude(asset_group_name__exact="")
            .values_list("asset_group_name", flat=True)
            .distinct()
            .order_by("asset_group_name")
        ),
        "fuels": list(
            gb.exclude(fuel__isnull=True)
            .exclude(fuel__exact="")
            .values_list("fuel", flat=True)
            .distinct()
            .order_by("fuel")
        ),
    }

    if brand and model and sub_model and year_manu:
        detail_qs = qs.filter(
            brand_name=brand,
            model_name=model,
            sub_model_code=sub_model,
            year_of_manufacture=year_int
        ).first()

        if detail_qs:
            sub_key = detail_qs.sub_key
            detail_qs2 = gb.filter(vehiclekey=sub_key).first()

            sub_model_code_trans = str(sub_model).upper()
            sub_model_code_trans = sub_model_code_trans.replace(' ', '')
            sub_model_code_trans = sub_model_code_trans.replace('-', '')
            sub_model_code_trans = sub_model_code_trans.replace('(NEW)', '')

            print(sub_model_code_trans)
            if sub_model_code_trans in ('NAN', 'NaN', 'Nan', 'nan', ''):
                sub_model_code_trans = np.nan

            car_type_qs = table[
                (table['brand_name'] == brand)
                & (table['model_name'] == model)
                & (table['sub_model_code'] == sub_model_code_trans)
                & (table['year_of_manufacture'] == year_int)
            ]["car_type"]
            car_type = str(car_type_qs.values[0]) if not car_type_qs.empty else ""
            engine_desc = ""
            if detail_qs2 and detail_qs2.enginedescription is not None:
                engine_desc = str(detail_qs2.enginedescription)

            engine_size = ""
            if detail_qs.engine_size is not None:
                engine_size = str(detail_qs.engine_size)

            if engine_desc and engine_size:
                engine_text = f"{engine_desc} ({engine_size})"
            else:
                engine_text = engine_desc or engine_size

            gb_fuel = ""
            if detail_qs2 and detail_qs2.fuel is not None:
                gb_fuel = str(detail_qs2.fuel).strip()

            detail = {
                "car_type": car_type,
                "gear": detail_qs.asset_gear or "",
                "asset_group": detail_qs.asset_group_name or "",
                "fuel": gb_fuel,
                "engine": engine_text,
                "detail_found": True,
                "new_price": detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else 0,
            }
    #print(detail)

    return JsonResponse({
    "models": list(models),
    "sub_models": list(sub_models),
    "years": list(years),
    "car_detail" : detail,
    "fallback_detail_choices": fallback_detail_choices,
})


@require_POST
def seasonal_predict_price(request):
    brand = request.POST.get("brand_name", "").strip()
    model = request.POST.get("model_name", "").strip()
    sub_model = request.POST.get("sub_model", "").strip()
    year_raw = request.POST.get("year_of_manufacture", "").strip()
    register_year_raw = request.POST.get("asset_register_year", "").strip()
    mile_raw = request.POST.get("mile", "").strip()
    historical = request.POST.get("historical", "").strip()
    branch = request.POST.get("branch", "").strip()
    season = (request.POST.get("season", "") or request.POST.get("prediction_month", "")).strip()
    grade = request.POST.get("grade", "").strip().upper()
    gear = request.POST.get("gear", "").strip()
    asset_group = request.POST.get("asset_group", "").strip()
    engine = request.POST.get("engine", "").strip()
    fuel_post = request.POST.get("fuel", "").strip()
    fuel = fuel_post
    new_price_raw = request.POST.get("new_price", "").strip()
    car_type = request.POST.get("car_type", "").strip()
    # region agent log
    with open("debug-bc8fa5.log", "a", encoding="utf-8") as _dbg:
        _dbg.write(json.dumps({"sessionId":"bc8fa5","runId":"pre-fix","hypothesisId":"H1","location":"views.py:1156","message":"branch_predict_price entry","data":{"branch_raw":branch,"brand":brand,"model":model,"sub_model":sub_model,"year_raw":year_raw,"mile_raw":mile_raw,"grade_raw":grade},"timestamp":int(time.time()*1000)}, ensure_ascii=False) + "\n")
    # endregion
    
    if not (brand and model and sub_model and year_raw):
        return JsonResponse({
            "ok": False,
            "message": "Please select brand, model, sub model, and year first."
        }, status=400)

    try:
        year = int(year_raw)
    except ValueError:
        return JsonResponse({"ok": False, "message": "Invalid manufacture year."}, status=400)

    register_year = None
    if register_year_raw:
        try:
            register_year = int(float(register_year_raw))
        except ValueError:
            register_year = None

    mileage = 0
    mileage_list = []
    if mile_raw:
        mileage =int(float(mile_raw))
        mileage_list.append(mileage)
    elif not mile_raw:
        mileage_list.append(10000)
        mileage_list.append(50000)
        mileage_list.append(100000)
        mileage_list.append(150000)
        mileage_list.append(200000)

    grade_list = []
    if grade:
        grade_list.append(grade)
    elif not grade:
        grade_list.append(1)
        grade_list.append(2)
        grade_list.append(3)
        grade_list.append(4)
        grade_list.append(5)


    base_filter = asset_sold_car_test.objects.filter(
        brand_name=brand,
        model_name=model,
        sub_model_code=sub_model,
        year_of_manufacture=year,
    )
    sub_model_norm = str(sub_model).upper().replace(" ", "").replace("-", "").replace("(NEW)", "")
    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    manual_newprice = 0
    if new_price_raw:
        try:
            manual_newprice = float(new_price_raw)
        except ValueError:
            manual_newprice = 0

    base_filter_first = base_filter.first()
    asset_group_code = ""
    engine_size = parse_engine_size_from_text(engine)
    newprice = 0

    if base_filter_first:
        sub_key = base_filter_first.sub_key
        detail_qs2 = greenbook.objects.filter(vehiclekey=sub_key).first()
        if not fuel_post:
            fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        #fuel = detail_qs2.fuel if detail_qs2 and detail_qs2.fuel is not None else ""
        asset_group_code = base_filter_first.asset_group_code or ""
        if not engine_size:
            engine_size = base_filter_first.engine_size or 0
        newprice = detail_qs2.newprice if detail_qs2 and detail_qs2.newprice is not None else manual_newprice
    elif asset_group:
        asset_group_code = (
            asset_sold_car_test.objects.filter(asset_group_name=asset_group)
            .exclude(asset_group_code__isnull=True)
            .exclude(asset_group_code__exact="")
            .values_list("asset_group_code", flat=True)
            .first()
            or ""
        )
    if (not base_filter_first) and manual_newprice > 0:
        newprice = manual_newprice

    #historical transform
    if historical == "no-accident":
        historical_factor = "Normal"
    elif historical == "flood":
        historical_factor = "W"
    elif historical == "unmoved-engine":
        historical_factor = "N"
    elif historical == "unmoved":
        historical_factor = "U"
    else:
        historical_factor = "Unknown"

    #branch transform
    if branch == "Bangkok":
        branch_name = "กรุงเทพมหานคร"
    elif branch == "Nakhon Ratchasima":
        branch_name = "นครราชสีมา"
    elif branch == "Pattaya":
        branch_name = "พัทยา"
    elif branch == "Rangsit klong 8":
        branch_name = "รังสิต คลอง 8"
    elif branch == "Songkhla":
        branch_name = "สงขลา"   
    elif branch == "Surat Thani":
        branch_name = "สุราษฎร์ธานี"
    elif branch == "Udon Thani":
        branch_name = "อุดรธานี"
    elif branch == "Chaing Mai":
        branch_name = "เชียงใหม่"
    elif branch == "Khon Kaen":
        branch_name = "ขอนแก่น"
    elif branch == "Ubon Ratchathani":
        branch_name = "อุบลราชธานี"
    elif branch == "Rayong":
        branch_name = "ระยอง"
    elif branch == "Ratchaburi":
        branch_name = "ราชบุรี"
    else:
        branch_name = "Unknown"

    branch_list = []
    if branch:
        branch_list.append(branch_name)
    elif not branch:
        branch_list.append("กรุงเทพมหานคร")
        branch_list.append("นครราชสีมา")
        branch_list.append("พัทยา")
        branch_list.append("รังสิต คลอง 8")
        branch_list.append("สงขลา")
        branch_list.append("สุราษฎร์ธานี")
        branch_list.append("อุดรธานี")
        branch_list.append("เชียงใหม่")
        branch_list.append("ขอนแก่น")
        branch_list.append("อุบลราชธานี")
        branch_list.append("ระยอง")
        branch_list.append("ราชบุรี")
    car_filter = table[
        (table['brand_name'] == brand)
        & (table['model_name'] == model)
        & (table['sub_model_code'] == sub_model_norm)
    ]

    #sonsal transform

    seasonal_list = []
    if season:
        seasonal_list.append(season)
    else:
        seasonal_list.append("January")
        seasonal_list.append("February")
        seasonal_list.append("March")
        seasonal_list.append("April")
        seasonal_list.append("May")
        seasonal_list.append("June")
        seasonal_list.append("July")
        seasonal_list.append("August")
        seasonal_list.append("September")
        seasonal_list.append("October")
        seasonal_list.append("November")
        seasonal_list.append("December")

    age = int(datetime.now().strftime("%Y")) - register_year if register_year is not None else 0
    car_age_bucket = pd.cut([age], bins=[-1, 10, 20, 30, 40, 50, 1e9], labels=[5, 4, 3, 2, 1, 0]).astype(float)[0]
    is_multi = len(seasonal_list) > 1 or len(branch_list) > 1 or len(mileage_list) > 1 or len(grade_list) > 1
    results = []
    if car_type == "EV":
        fuel = "Electric"
    
    message = "Please"
    if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical or (year > register_year):
        if not car_type or not gear or not asset_group or not engine or not newprice or not fuel or not register_year or not historical:
            message = " input "
            if not car_type:
                message += "Car type, "
            if not gear:
                message += "Gear, "
            if not asset_group:
                message += "Asset Group, "
            if not engine:
                message += "Engine, "
            if not newprice:
                message += "New price, "
            if not fuel:
                message += "Fuel, "
            if not register_year:
                message += "Asset Register year, "
            if not historical:
                message += "Historical, "
            message += "please."
        if year > register_year:
            message += " register year could more than year of manufacture"

        return JsonResponse({
            "ok": False,
            "message": message
        }, status=400)
    else:
        if car_filter.empty:
            for s in seasonal_list:
                for b in branch_list:
                    for m in mileage_list:
                        for g in grade_list:
                            sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                            mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                            Age_x_Mile = age * m
                            if s == "January":
                                auction_date = datetime(datetime.now().year, 1, 1)
                            elif s == "February":
                                auction_date = datetime(datetime.now().year, 2, 1)
                            elif s == "March":
                                auction_date = datetime(datetime.now().year, 3, 1)
                            elif s == "April":
                                auction_date = datetime(datetime.now().year, 4, 1)
                            elif s == "May":
                                auction_date = datetime(datetime.now().year, 5, 1)
                            elif s == "June":
                                auction_date = datetime(datetime.now().year, 6, 1)
                            elif s == "July":
                                auction_date = datetime(datetime.now().year, 7, 1)
                            elif s == "August":
                                auction_date = datetime(datetime.now().year, 8, 1)
                            elif s == "September":
                                auction_date = datetime(datetime.now().year, 9, 1)
                            elif s == "October":
                                auction_date = datetime(datetime.now().year, 10, 1)
                            elif s == "November":
                                auction_date = datetime(datetime.now().year, 11, 1)
                            elif s == "December":
                                auction_date = datetime(datetime.now().year, 12, 1)

                            auction_year = auction_date.year
                            auction_month = auction_date.month
                            auction_quarter = (auction_month - 1) // 3 + 1

                            if car_type == "EV":
                                    
                                input_data = [{
                                    "Brand_Name": brand,
                                    "Model_Name": model,
                                    "Sub_Model_Code": sub_model_code_trans,
                                    "Branch_Name" : b,
                                    "Fuel": fuel,
                                    "Asset_Gear": gear,
                                    "Asset_Group_Code": asset_group_code,
                                    "Car_Status": historical_factor,
                                    "Car_Type": car_type,
                                    "Year_of_Manufacture": year,
                                    "Asset_Register_Year": register_year,
                                    "Car_Age": age,
                                    "Car_Age_Bucket": car_age_bucket,
                                    "Mile_Transform": m,
                                    "NewPrice": newprice,
                                    "Grade_Score": g,
                                    "Mile_Bucket":mile_bucket,
                                    "Age_x_Mile":Age_x_Mile,
                                    "Auction_Year": auction_year,
                                    "Auction_Month_Num": auction_month,
                                    "Auction_Quarter": auction_quarter
                                }]

                                model_predict_name = 'greenbook/models/Normal/Special/ev.pkl'
                            else:
                                    
                                input_data = [{
                                    "Brand_Name": brand,
                                    "Model_Name": model,
                                    "Sub_Model_Code": sub_model_code_trans,
                                    "Branch_Name" : b,
                                    "Fuel": fuel,
                                    "Asset_Gear": gear,
                                    "Asset_Group_Code": asset_group_code,
                                    "Car_Status": historical_factor,
                                    "Car_Type": car_type,
                                    "Year_of_Manufacture": year,
                                    "Engine_Size": engine_size,
                                    "Asset_Register_Year": register_year,
                                    "Car_Age": age,
                                    "Car_Age_Bucket": car_age_bucket,
                                    "Mile_Transform": m,
                                    "NewPrice": newprice,
                                    "Grade_Score": g,
                                    "Mile_Bucket":mile_bucket,
                                    "Age_x_Mile":Age_x_Mile,
                                    "Auction_Year": auction_year,
                                    "Auction_Month_Num": auction_month,
                                    "Auction_Quarter": auction_quarter
                                }]

                                model_predict_name = 'greenbook/models/Normal/Special/n_ev.pkl'

                            predicted = int(round(ml_predict(model_predict_name,input_data)))
                            min_price = int(round(predicted * 0.95))
                            max_price = int(round(predicted * 1.05))

                            results.append({
                                "branch": b,
                                "season": s,
                                "grade": int(g),
                                "mileage": int(m),
                                "predicted": predicted,
                                "min_price": min_price,
                                "max_price": max_price,
                            })
        else:
            #engineer feature
            B_Median = car_filter['B_Median'].median()
            brand_tier = car_filter['Brand_Tier'].unique()[0]
            BM_Median = car_filter['BM_Median'].median()

            car_filter_1 = car_filter.sort_values("auction_date")

            avg_price_lag_1_list = list(car_filter_1["sold_amount"][-1:].values)
            if len(avg_price_lag_1_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_1 = median_price
            else:
                avg_price_lag_1 = avg_price_lag_1_list[0]
            avg_price_lag_3_list = list(car_filter_1["sold_amount"][-3:].values)
            if len(avg_price_lag_3_list) == 0:
                median_price = car_filter_1["sold_amount"].median()
                avg_price_lag_3 = median_price
            else:
                avg_price_lag_3 = avg_price_lag_3_list[0]
            avg_price_roll_3_list = car_filter_1["sold_amount"][-3:].values.mean()
            if  not avg_price_roll_3_list :
                median_price = car_filter_1["sold_amount"].median()
                avg_price_roll_3 = median_price
            else:
                avg_price_roll_3 = avg_price_roll_3_list
            
            market_df = (
                car_filter.groupby("auction_month")["sold_amount"]
                .mean()
                .reset_index()
                .rename(columns={"sold_amount": "market_median_price"})
            )

            market_df = market_df.sort_values("auction_month")
            market_price_lag_1_list = list(market_df["market_median_price"][-1:].values)

            if len(market_price_lag_1_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_1 = median_price
            else:
                market_price_lag_1 = market_price_lag_1_list[0]
            market_price_lag_2_list = list(market_df["market_median_price"][-2:].values)
            if len(market_price_lag_2_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_2 = median_price
            else:
                market_price_lag_2 = market_price_lag_2_list[0]
            market_price_lag_3_list = list(market_df["market_median_price"][-3:].values)
            if len(market_price_lag_3_list) == 0:
                median_price = market_df["market_median_price"].median()
                market_price_lag_3 = median_price
            else:
                market_price_lag_3 = market_price_lag_3_list[0]
            market_price_roll_3_list = market_df["market_median_price"][-3:].values.mean()
            if not market_price_roll_3_list:
                median_price = market_df["market_median_price"].median()
                market_price_roll_3 = median_price
            else:
                market_price_roll_3 = market_price_roll_3_list
            
            BrandTier_x_Age = brand_tier * age
            Engine_x_BrandTier = engine_size * brand_tier
            Car_Type = car_filter["car_type"].unique()[0]

            for s in seasonal_list:
                for b in branch_list:
                    for m in mileage_list:
                        for g in grade_list:
                            sub_model_code_trans = sub_model.replace(' ', '').replace('-', '').replace('(NEW)', '')
                            mile_bucket = pd.cut([m], bins=[-1,20000,50000,100000,150000,200000,1e9], labels=[5,4,3,2,1,0]).astype(float)[0]
                            Age_x_Mile = age * m
                            g_t = int(g)
                            
                            if s == "January":
                                auction_date = datetime(datetime.now().year, 1, 1)
                            elif s == "February":
                                auction_date = datetime(datetime.now().year, 2, 1)
                            elif s == "March":
                                auction_date = datetime(datetime.now().year, 3, 1)
                            elif s == "April":
                                auction_date = datetime(datetime.now().year, 4, 1)
                            elif s == "May":
                                auction_date = datetime(datetime.now().year, 5, 1)
                            elif s == "June":
                                auction_date = datetime(datetime.now().year, 6, 1)
                            elif s == "July":
                                auction_date = datetime(datetime.now().year, 7, 1)
                            elif s == "August":
                                auction_date = datetime(datetime.now().year, 8, 1)
                            elif s == "September":
                                auction_date = datetime(datetime.now().year, 9, 1)
                            elif s == "October":
                                auction_date = datetime(datetime.now().year, 10, 1)
                            elif s == "November":
                                auction_date = datetime(datetime.now().year, 11, 1)
                            elif s == "December":
                                auction_date = datetime(datetime.now().year, 12, 1)
                            
                            auction_year = auction_date.year
                            auction_month = auction_date.month
                            auction_quarter = (auction_month - 1) // 3 + 1

                            input_data = [{
                                "Brand_Name": brand,
                                "Model_Name": model,
                                "Sub_Model_Code": sub_model_code_trans,
                                "Branch_Name" : b,
                                "Fuel": fuel,
                                "Asset_Gear": gear,
                                "Asset_Group_Code": asset_group_code,
                                "Car_Status": historical_factor,
                                "Year_of_Manufacture": year,
                                "Asset_Register_Year": register_year,
                                "Car_Age": age,
                                "Mile_Transform": m,
                                "Engine_Size": engine_size,
                                "NewPrice": newprice,
                                "Grade_Score": g_t,
                                "Mile_Bucket":mile_bucket,
                                "B_Median":B_Median,
                                "Car_Age_Bucket":car_age_bucket,
                                "Age_x_Mile":Age_x_Mile,
                                "avg_price_lag_1":avg_price_lag_1,
                                "avg_price_lag_3":avg_price_lag_3,
                                "avg_price_roll_3":avg_price_roll_3,
                                "market_price_roll_3":market_price_roll_3,
                                "market_price_lag_1":market_price_lag_1,
                                "market_price_lag_2":market_price_lag_2,
                                "BrandTier_x_Age":BrandTier_x_Age,
                                "Brand_Tier":brand_tier,
                                "Engine_x_BrandTier":Engine_x_BrandTier,
                                "BM_Median":BM_Median,
                                "market_price_lag_3":market_price_lag_3,
                                "Auction_Year": auction_year,
                                "Auction_Month_Num": auction_month,
                                "Auction_Quarter": auction_quarter
                            }]
                            
                            
                            model_predict_name = f'greenbook/models/Seasonal/{Car_Type}/{brand}.pkl'
                            predicted = int(round(ml_predict(model_predict_name,input_data)))
                            min_price = int(round(predicted * 0.95))
                            max_price = int(round(predicted * 1.05))

                            results.append({
                                "branch": b,
                                "season": s,
                                "grade": int(g),
                                "mileage": int(m),
                                "predicted": predicted,
                                "min_price": min_price,
                                "max_price": max_price,
                            })

    # Sales transaction history (x=time, y=sold)
    history_qs = (
        base_filter.exclude(auction_date__isnull=True)
        .order_by("auction_date")
        .values("auction_date", "sold_amount")
    )

    history_labels = []
    history_values = []
    for row in history_qs:
        sold_value = row["sold_amount"]
        if not sold_value:
            continue

        history_labels.append(row["auction_date"].strftime("%Y-%m-%d"))
        history_values.append(float(sold_value))

    history_message = "" if history_values else "ไม่พบข้อมูลการขายในอดีต"

    if is_multi:
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"branch {branch_name if branch else 'all branches'}, "
            f"season {season if season else 'all seasons'}, "
            f"register year {register_year if register_year else '-'}, "
            f"history {historical if historical else '-'}."
        )
    else:
        r = results[0]
        summary = (
            f"Estimated from {brand} {model}"
            f"{' (' + sub_model + ')' if sub_model else ''}, year {year}, "
            f"branch {r.get('branch', branch_name if branch else '-')}, "
            f"season {r.get('season', season if season else '-')}, "
            f"register year {register_year if register_year else '-'}, "
            f"mileage {r['mileage']:,} km, grade {r['grade']}, "
            f"history {historical if historical else '-'}."
        )

    response_data = {
        "ok": True,
        "is_multi": is_multi,
        "branch_values": sorted(set(b for b in branch_list)),
        "grade_values": sorted(set(int(g) for g in grade_list)),
        "mileage_values": sorted(set(int(m) for m in mileage_list)),
        "results": results,
        "brand_model": f"{brand} {model} {year}",
        "year": year,
        "newprice": newprice,
        "fuel": fuel,
        "branch": (results[0].get("branch") if results else (branch_name if branch else "")),
        "season": (results[0].get("season") if results else (season if season else "")),
        "summary": summary,
        "history_labels": history_labels,
        "history_values": history_values,
        "history_message": history_message,
        "car_detail": {
            "gear": gear,
            "asset_group": asset_group,
            "engine": engine,
        },
    }

    if not is_multi:
        r = results[0]
        response_data["predicted_price"] = r["predicted"]
        response_data["min_price"] = r["min_price"]
        response_data["max_price"] = r["max_price"]
        response_data["mile"] = r["mileage"]

    return JsonResponse(response_data)