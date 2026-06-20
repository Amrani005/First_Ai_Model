import pandas as pd
from sqlalchemy import create_engine, text

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
    cols = ["brand", "model_name", "battery_mah", "cores", "ram_mb", "primary_camera_mp", "price_usd"]
    df = df[cols]

    # تنظيف الأسعار والبيانات (تحويل العملة)
    INR_TO_USD_RATE = 83.0
    df['price_usd'] = (pd.to_numeric(df['price_usd'], errors='coerce') / INR_TO_USD_RATE).round(2)
    df = df.dropna()

    print(f"📦 Injecting {len(df)} phones into Neon...")

    # 3. مسح الجدول القديم بالكامل وإنشاء واحد جديد
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS "PhoneCatalog"'))
        conn.commit()
    
    # 4. رفع البيانات كاملة
    df.to_sql('PhoneCatalog', engine, if_exists='replace', index=False)
    print("✅ Done! Neon is now fully reloaded with all data.")

if __name__ == "__main__":
    reload_full_database()