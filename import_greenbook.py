import os
import django
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datascientist.settings")
django.setup()

from greenbook.models import greenbook

df = pd.read_excel("data/Greenbook.xlsx")
print("Load data successfully")

df["Created_Date"] = pd.to_datetime(df["Created_Date"], errors="coerce")
df["Last_Modified_Date"] = pd.to_datetime(df["Last_Modified_Date"], errors="coerce")
df["Cancelled_Datetime"] = pd.to_datetime(df["Cancelled_Datetime"], errors="coerce")
print("Transform data successfully")

for _, row in df.iterrows():
    companycode = str(row["CompanyCode"]).strip() if pd.notna(row["CompanyCode"]) else None
    recordid = int(row["RecordID"]) if pd.notna(row["RecordID"]) else 0
    dels = int(row["del"]) if pd.notna(row["del"]) else 0
    vehiclekey = str(row["Vehiclekey"]).strip() if pd.notna(row["Vehiclekey"]) else None
    vehicletypecode = str(row["VehicleTypeCode"]).strip() if pd.notna(row["VehicleTypeCode"]) else None
    yeargroup = int(row["YearGroup"]) if pd.notna(row["YearGroup"]) else 0
    monthgroup = int(row["MonthGroup"]) if pd.notna(row["MonthGroup"]) else 0
    auctmakecode = str(row["AuctMakeCode"]).strip() if pd.notna(row["AuctMakeCode"]) else None
    makecode = str(row["MakeCode"]).strip() if pd.notna(row["MakeCode"]) else None
    makename = str(row["MakeName"]).strip() if pd.notna(row["MakeName"]) else None
    auctfamilycode = str(row["AuctFamilyCode"]).strip() if pd.notna(row["AuctFamilyCode"]) else None
    familycode = str(row["FamilyCode"]).strip() if pd.notna(row["FamilyCode"]) else None
    familyname = str(row["FamilyName"]).strip() if pd.notna(row["FamilyName"]) else None
    submodeldesc = str(row["SubmodelDesc"]).strip() if pd.notna(row["SubmodelDesc"]) else None
    submodeldesc2 = str(row["SubmodelDesc2"]).strip() if pd.notna(row["SubmodelDesc2"]) else None
    modelss = int(row["ModelS"]) if pd.notna(row["ModelS"]) else 0
    modelf = str(row["ModelF"]).strip() if pd.notna(row["ModelF"]) else None
    nickname = str(row["NickName"]).strip() if pd.notna(row["NickName"]) else None
    submodelname = str(row["SubmodelName"]).strip() if pd.notna(row["SubmodelName"]) else None
    series = str(row["Series"]).strip() if pd.notna(row["Series"]) else None
    badgedescription = str(row["BadgeDescription"]).strip() if pd.notna(row["BadgeDescription"]) else None
    badgesecondarydescription = str(row["BadgeSecondaryDescription"]).strip() if pd.notna(row["BadgeSecondaryDescription"]) else None
    bodystyledescription = str(row["BodyStyleDescription"]).strip() if pd.notna(row["BodyStyleDescription"]) else None
    bodyconfigdescription = str(row["BodyConfigDescription"]).strip() if pd.notna(row["BodyConfigDescription"]) else None
    extraidentification = str(row["ExtraIdentification"]).strip() if pd.notna(row["ExtraIdentification"]) else None
    drive = str(row["Drive"]).strip() if pd.notna(row["Drive"]) else None
    gear = str(row["Gear"]).strip() if pd.notna(row["Gear"]) else None
    gearnum = float(row["GearNum"]) if pd.notna(row["GearNum"]) else 0
    doornum = int(row["DoorNum"]) if pd.notna(row["DoorNum"]) else 0
    enginesize = float(row["EngineSize"]) if pd.notna(row["EngineSize"]) else 0
    enginedescription = float(row["EngineDescription"]) if pd.notna(row["EngineDescription"]) else 0
    cc = float(row["CC"]) if pd.notna(row["CC"]) else 0
    fuel = str(row["Fuel"]).strip() if pd.notna(row["Fuel"]) else None
    avgwholesale = int(row["AvgWholesale"]) if pd.notna(row["AvgWholesale"]) else 0
    avgretail = int(row["AvgRetail"]) if pd.notna(row["AvgRetail"]) else 0
    goodwholesale = int(row["GoodWholesale"]) if pd.notna(row["GoodWholesale"]) else 0
    goodretail = int(row["GoodRetail"]) if pd.notna(row["GoodRetail"]) else 0
    newprice = float(row["NewPrice"]) if pd.notna(row["NewPrice"]) else 0
    vin = str(row["VIN"]).strip() if pd.notna(row["VIN"]) else None
    modelcode = str(row["Modelcode"]).strip() if pd.notna(row["Modelcode"]) else None
    enginenum = str(row["Enginenum"]).strip() if pd.notna(row["Enginenum"]) else None
    showstat = float(row["ShowStat"]) if pd.notna(row["ShowStat"]) else 0
    brand = float(row["Brand"]) if pd.notna(row["Brand"]) else 0
    buildcountryorigindescription = str(row["BuildCountryOriginDescription"]).strip() if pd.notna(row["BuildCountryOriginDescription"]) else None
    auctbodyname = str(row["AUCTBodyName"]).strip() if pd.notna(row["AUCTBodyName"]) else None
    created_by = float(row["Created_By"]) if pd.notna(row["Created_By"]) else 0
    #created_date = float(row["Created_Date"]) if pd.notna(row["Created_Date"]) else 0
    last_modified_by = float(row["Last_Modified_By"]) if pd.notna(row["Last_Modified_By"]) else 0
    #last_modified_date = float(row["Last_Modified_Date"]) if pd.notna(row["Last_Modified_Date"]) else 0
    cancelled = int(row["Cancelled"]) if pd.notna(row["Cancelled"]) else 0
    #cancelled_datetime = float(row["Cancelled_Datetime"]) if pd.notna(row["Cancelled_Datetime"]) else 0
    cancelled_by = float(row["Cancelled_By"]) if pd.notna(row["Cancelled_By"]) else 0
    created_at = None

    if pd.notna(row["Created_Date"]):
        created_date = row["Created_Date"].to_pydatetime()
    else:
        created_date = None

    if pd.notna(row["Last_Modified_Date"]):
        last_modified_date = row["Last_Modified_Date"].to_pydatetime()
    else:
        last_modified_date = None

    if pd.notna(row["Cancelled_Datetime"]):
        cancelled_datetime = row["Cancelled_Datetime"].to_pydatetime()
    else:
        cancelled_datetime = None

    greenbook.objects.create(
    companycode = companycode,
    recordid = recordid,
    dels = dels,
    vehiclekey = vehiclekey,
    vehicletypecode = vehicletypecode,
    yeargroup = yeargroup,
    monthgroup = monthgroup,
    auctmakecode = auctmakecode,
    makecode = makecode,
    makename = makename,
    auctfamilycode = auctfamilycode,
    familycode = familycode,
    familyname = familyname,
    submodeldesc = submodeldesc,
    submodeldesc2 = submodeldesc2,
    modelss = modelss,
    modelf = modelf,
    nickname = nickname,
    submodelname = submodelname,
    series = series,
    badgedescription = badgedescription,
    badgesecondarydescription = badgesecondarydescription,
    bodystyledescription = bodystyledescription,
    bodyconfigdescription = bodyconfigdescription,
    extraidentification = extraidentification,
    drive = drive,
    gear = gear,
    gearnum = gearnum,
    doornum = doornum,
    enginesize = enginesize,
    enginedescription = enginedescription,
    cc = cc,
    fuel = fuel,
    avgwholesale = avgwholesale,
    avgretail = avgretail,
    goodwholesale = goodwholesale,
    goodretail = goodretail,
    newprice = newprice,
    vin = vin,
    modelcode = modelcode,
    enginenum = enginenum,
    showstat = showstat,
    brand = brand,
    buildcountryorigindescription = buildcountryorigindescription,
    auctbodyname = auctbodyname,
    created_by = created_by,
    created_date = created_date,
    last_modified_by = last_modified_by,
    last_modified_date = last_modified_date,
    cancelled = cancelled,
    cancelled_datetime = cancelled_datetime,
    cancelled_by = cancelled_by,
    )

# df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

# for _, row in df.iterrows():
#     name = str(row["name"]).strip() if pd.notna(row["name"]) else None
#     price = float(row["price"]) if pd.notna(row["price"]) else 0
#     quantity = int(row["quantity"]) if pd.notna(row["quantity"]) else 0

#     created_at = None
#     if pd.notna(row["created_at"]):
#         created_at = row["created_at"].to_pydatetime()

#     if not name:
#         continue

#     greenbook.objects.create(
#         name=name,
#         price=price,
#         quantity=quantity,
#         created_at=created_at
#     )

# for _, row in df.iterrows():
#     greenbook.objects.create(
#         companycode = row["CompanyCode"],
#         recordid = row["RecordID"],
#         dels = row["del"],
#         vehiclekey = row["Vehiclekey"],
#         vehicletypecode = row["VehicleTypeCode"],
#         yeargroup = row["YearGroup"],
#         monthgroup = row["MonthGroup"],
#         auctmakecode = row["AuctMakeCode"],
#         makecode = row["MakeCode"],
#         makename = row["MakeName"],
#         auctfamilycode = row["AuctFamilyCode"],
#         familycode = row["FamilyCode"],
#         familyname = row["FamilyName"],
#         submodeldesc = row["SubmodelDesc"],
#         submodeldesc2 = row["SubmodelDesc2"],
#         modelss = row["ModelS"],
#         modelf = row["ModelF"],
#         nickname = row["NickName"],
#         submodelname = row["SubmodelName"],
#         series = row["Series"],
#         badgedescription = row["BadgeDescription"],
#         badgesecondarydescription = row["BadgeSecondaryDescription"],
#         bodystyledescription = row["BodyStyleDescription"],
#         bodyconfigdescription = row["BodyConfigDescription"],
#         extraidentification = row["ExtraIdentification"],
#         drive = row["Drive"],
#         gear = row["Gear"],
#         gearnum = row["GearNum"],
#         doornum = row["DoorNum"],
#         enginesize = row["EngineSize"],
#         enginedescription = row["EngineDescription"],
#         cc = row["CC"],
#         fuel = row["Fuel"],
#         avgwholesale = row["AvgWholesale"],
#         avgretail = row["AvgRetail"],
#         goodwholesale = row["GoodWholesale"],
#         goodretail = row["GoodRetail"],
#         newprice = row["NewPrice"],
#         vin = row["VIN"],
#         modelcode = row["Modelcode"],
#         enginenum = row["Enginenum"],
#         showstat = row["ShowStat"],
#         brand = row["Brand"],
#         buildcountryorigindescription = row["BuildCountryOriginDescription"],
#         auctbodyname = row["AUCTBodyName"],
#         created_by = row["Created_By"],
#         created_date = row["Created_Date"],
#         last_modified_by = row["Last_Modified_By"],
#         last_modified_date = row["Last_Modified_Date"],
#         cancelled = row["Cancelled"],
#         cancelled_datetime = row["Cancelled_Datetime"],
#         cancelled_by = row["Cancelled_By"],
#     )

print("Import success")