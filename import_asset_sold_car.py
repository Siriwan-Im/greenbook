import os
import django
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datascientist.settings")
django.setup()

from greenbook.models import asset_sold_car_test

df = pd.read_excel("data/Asset_Sold_Car.xlsx")
print("Load data successfully")

df["Auction_Date"] = pd.to_datetime(df["Auction_Date"], errors="coerce")
print("Transform data successfully")

for _, row in df.iterrows():
    byquater = int(row["byQuater"]) if pd.notna(row["byQuater"]) else 0
    bymonth = int(row["byMonth"]) if pd.notna(row["byMonth"]) else 0
    month_name = str(row["Month_Name"]).strip() if pd.notna(row["Month_Name"]) else None
    byseasonal = str(row["bySeasonal"]).strip() if pd.notna(row["bySeasonal"]) else None
    branch_code = int(row["Branch_Code"]) if pd.notna(row["Branch_Code"]) else 0
    branch_name = str(row["Branch_Name"]).strip() if pd.notna(row["Branch_Name"]) else None
    floor = str(row["Floor"]).strip() if pd.notna(row["Floor"]) else None
    auction_no = int(row["Auction_No"]) if pd.notna(row["Auction_No"]) else 0
    makecode = str(row["MakeCode"]).strip() if pd.notna(row["MakeCode"]) else None
    brand_name = str(row["Brand_Name"]).strip() if pd.notna(row["Brand_Name"]) else None
    model_name = str(row["Model_Name"]).strip() if pd.notna(row["Model_Name"]) else None
    sub_model_code = str(row["Sub_Model_Code"]).strip() if pd.notna(row["Sub_Model_Code"]) else None
    sub_key = str(row["Sub_Key"]).strip() if pd.notna(row["Sub_Key"]) else None
    asset_gear = str(row["Asset_Gear"]).strip() if pd.notna(row["Asset_Gear"]) else None
    engine_size = float(row["Engine_Size"]) if pd.notna(row["Engine_Size"]) else 0
    chassis_no = str(row["Chassis_No"]).strip() if pd.notna(row["Chassis_No"]) else None
    engine_no = str(row["Engine_No"]).strip() if pd.notna(row["Engine_No"]) else None
    mile = float(row["Mile"]) if pd.notna(row["Mile"]) else 0
    color_in_copy = str(row["Color_in_copy"]).strip() if pd.notna(row["Color_in_copy"]) else None
    year_of_manufacture = int(row["Year_of_Manufacture"]) if pd.notna(row["Year_of_Manufacture"]) else 0
    asset_register_year = float(row["Asset_Register_Year"]) if pd.notna(row["Asset_Register_Year"]) else 0
    asset_type_code = str(row["Asset_Type_Code"]).strip() if pd.notna(row["Asset_Type_Code"]) else None
    asset_type_name = str(row["Asset_Type_Name"]).strip() if pd.notna(row["Asset_Type_Name"]) else None
    asset_group_code = str(row["Asset_Group_Code"]).strip() if pd.notna(row["Asset_Group_Code"]) else None
    asset_group_name = str(row["Asset_Group_Name"]).strip() if pd.notna(row["Asset_Group_Name"]) else None
    asset_grade_assessment = str(row["Asset_Grade_Assessment"]).strip() if pd.notna(row["Asset_Grade_Assessment"]) else None
    sales_price = float(row["Sales_Price"]) if pd.notna(row["Sales_Price"]) else 0
    vat_amount = float(row["Vat_Amount"]) if pd.notna(row["Vat_Amount"]) else 0
    vat_code = str(row["VAT_Code"]).strip() if pd.notna(row["VAT_Code"]) else None
    vat_percentage = int(row["Vat_Percentage"]) if pd.notna(row["Vat_Percentage"]) else 0
    price_including_vat = float(row["Price_including_VAT"]) if pd.notna(row["Price_including_VAT"]) else 0
    seller_approve_sales_price = int(row["Seller_Approve_Sales_Price"]) if pd.notna(row["Seller_Approve_Sales_Price"]) else 0
    approve_sales_price = int(row["Approve_Sales_Price"]) if pd.notna(row["Approve_Sales_Price"]) else 0
    sold_amount = float(row["Sold_Amount"]) if pd.notna(row["Sold_Amount"]) else 0
    sales_type = str(row["Sales_Type"]).strip() if pd.notna(row["Sales_Type"]) else None
    asset_code = str(row["Asset_Code"]).strip() if pd.notna(row["Asset_Code"]) else None
    contract_no = str(row["Contract_No"]).strip() if pd.notna(row["Contract_No"]) else None
    license_plate_no = str(row["License_Plate_No"]).strip() if pd.notna(row["License_Plate_No"]) else None
    license_plate_city = str(row["License_Plate_City"]).strip() if pd.notna(row["License_Plate_City"]) else None
    license_plate_name = str(row["License_Plate_Name"]).strip() if pd.notna(row["License_Plate_Name"]) else None
    seller_code = str(row["Seller_Code"]).strip() if pd.notna(row["Seller_Code"]) else None
    asset_name = str(row["Asset_Name"]).strip() if pd.notna(row["Asset_Name"]) else None
    highest_selling_price = int(row["Highest_Selling_Price"]) if pd.notna(row["Highest_Selling_Price"]) else 0
    asset_tax_due_date = str(row["Asset_Tax_Due_Date"]).strip() if pd.notna(row["Asset_Tax_Due_Date"]) else None
    accessories = float(row["Accessories"]) if pd.notna(row["Accessories"]) else 0
    auction_board = int(row["Auction_Board"]) if pd.notna(row["Auction_Board"]) else 0
    asset_grade = str(row["Asset_Grade"]).strip() if pd.notna(row["Asset_Grade"]) else None
    asset_grade_check_condition = str(row["Asset_Grade_Check_Condition"]).strip() if pd.notna(row["Asset_Grade_Check_Condition"]) else None
    vendor_no = str(row["Vendor_No"]).strip() if pd.notna(row["Vendor_No"]) else None
    vendor_name = str(row["Vendor_Name"]).strip() if pd.notna(row["Vendor_Name"]) else None
    vendor_type = str(row["Vendor_Type"]).strip() if pd.notna(row["Vendor_Type"]) else None
    sale_remark = str(row["sale_remark"]).strip() if pd.notna(row["sale_remark"]) else None
    vehiclekey = str(row["Vehiclekey"]).strip() if pd.notna(row["Vehiclekey"]) else None
    bodystyledescription = str(row["BodyStyleDescription"]).strip() if pd.notna(row["BodyStyleDescription"]) else None

    if pd.notna(row["Auction_Date"]):
        auction_date = row["Auction_Date"].to_pydatetime()
    else:
        auction_date = None


    asset_sold_car_test.objects.create(
    auction_date = auction_date,
    byquater = byquater,
    bymonth = bymonth,
    month_name = month_name,
    byseasonal = byseasonal,
    branch_code = branch_code,
    branch_name = branch_name,
    floor = floor,
    auction_no = auction_no,
    makecode = makecode,
    brand_name = brand_name,
    model_name = model_name,
    sub_model_code = sub_model_code,
    sub_key = sub_key,
    asset_gear = asset_gear,
    engine_size = engine_size,
    chassis_no = chassis_no,
    engine_no = engine_no,
    mile = mile,
    color_in_copy = color_in_copy,
    year_of_manufacture = year_of_manufacture,
    asset_register_year = asset_register_year,
    asset_type_code = asset_type_code,
    asset_type_name = asset_type_name,
    asset_group_code = asset_group_code,
    asset_group_name = asset_group_name,
    asset_grade_assessment = asset_grade_assessment,
    sales_price = sales_price,
    vat_amount = vat_amount,
    vat_code = vat_code,
    vat_percentage = vat_percentage,
    price_including_vat = price_including_vat,
    seller_approve_sales_price = seller_approve_sales_price,
    approve_sales_price = approve_sales_price,
    sold_amount = sold_amount,
    sales_type = sales_type,
    asset_code = asset_code,
    contract_no = contract_no,
    license_plate_no = license_plate_no,
    license_plate_city = license_plate_city,
    license_plate_name = license_plate_name,
    seller_code = seller_code,
    asset_name = asset_name,
    highest_selling_price = highest_selling_price,
    asset_tax_due_date = asset_tax_due_date,
    accessories = accessories,
    auction_board = auction_board,
    asset_grade = asset_grade,
    asset_grade_check_condition = asset_grade_check_condition,
    vendor_no = vendor_no,
    vendor_name = vendor_name,
    vendor_type = vendor_type,
    sale_remark = sale_remark,
    vehiclekey = vehiclekey,
    bodystyledescription = bodystyledescription,
    )


print("Import success")