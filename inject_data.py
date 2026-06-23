import pandas as pd
from sqlalchemy import create_engine

# 1. رابط قاعدة البيانات
DATABASE_URL = "postgresql://neondb_owner:npg_RamBCOz0W8Ub@ep-rapid-dream-at6x8dkc-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)

def reload_full_database():
    print("🚀 Loading the full CSV file...")
    # تأكد أن اسم الملف هو نفسه الموجود عندك في المجلد
    df = pd.read_csv('phones_data.csv')

    # 2. تغيير أسماء الأعمدة لتطابق قاعدة البيانات
    df = df.rename(columns={
        "brand": "brand",
        "model": "model_name",
        "Battery capacity (mAh)": "battery_mah",
        "Processor": "cores",
        "RAM (MB)": "ram_mb",
        "Rear camera": "primary_camera_mp",
        "Price": "price_usd"
    })

    # الاحتفاظ بالأعمدة الأساسية فقط
    # ملاحظة: إذا قمت بإضافة 'release_year' في ملف الـ CSV كما اتفقنا، أضفها هنا في هذه القائمة
    cols = ["brand", "model_name", "battery_mah", "cores", "ram_mb", "primary_camera_mp", "price_usd"]
    df = df[cols]

    # تنظيف الأسعار والبيانات (تحويل العملة)
    INR_TO_USD_RATE = 83.0
    df['price_usd'] = (pd.to_numeric(df['price_usd'], errors='coerce') / INR_TO_USD_RATE).round(2)
    df = df.dropna()

    print(f"📦 Injecting {len(df)} phones into Neon...")

    # 3. رفع البيانات كإضافة (append) بدون مسح هيكل Prisma
    df.to_sql('PhoneCatalog', engine, if_exists='append', index=False)
    
    print("✅ Done! Neon is now fully reloaded with all data safely.")

if __name__ == "__main__":
    reload_full_database()