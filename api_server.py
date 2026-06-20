from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
import psycopg2
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor # التغيير هنا
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "smart_pricer_cloud.pkl"
# رابط قاعدة البيانات الخاص بك
NEON_DB_URL = "postgresql://neondb_owner:npg_RamBCOz0W8Ub@ep-rapid-dream-at6x8dkc-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# ==========================================
# 1. نظام الأتمتة والتدريب
# ==========================================
def auto_retrain_system():
    print("🔄 [AUTO-SYSTEM] Fetching fresh data from Neon Database...")
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        # إصلاح اسم الجدول وإضافة علامات التنصيص لـ PostgreSQL
        query = 'SELECT brand, ram_mb, battery_mah, cores, primary_camera_mp, price_usd FROM "PhoneCatalog"'
        df = pd.read_sql_query(query, conn)
        conn.close()

        X = df[['brand', 'ram_mb', 'battery_mah', 'cores', 'primary_camera_mp']]
        y = df['price_usd']

        preprocessor = ColumnTransformer(
            transformers=[('brand_encoder', OneHotEncoder(handle_unknown='ignore'), ['brand'])],
            remainder='passthrough'
        )

        new_model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42))
        ])
        
        new_model.fit(X, y)
        joblib.dump(new_model, MODEL_PATH)
        print("✅ [AUTO-SYSTEM] AI successfully trained from Cloud! Ready to predict.")
        return new_model
    except Exception as e:
        print(f"❌ [ERROR] Training failed: {e}")
        return None

# تحميل الموديل أو تدريبه إذا لم يكن موجوداً
if os.path.exists(MODEL_PATH):
    live_model = joblib.load(MODEL_PATH)
    print("✅ Model loaded from disk.")
else:
    live_model = auto_retrain_system()


@app.post("/retrain")
def retrain_endpoint():
    global live_model
    new_model = auto_retrain_system()
    if new_model is not None:
        live_model = new_model
        return {"status": "success", "message": "Model retrained successfully"}
    else:
        return {"status": "error", "message": "Retrain failed"}
# ==========================================
# 2. رابط التوقع (محرك التسعير)
# ==========================================
@app.get("/predict")
def predict_price(brand: str, ram_mb: int, battery_mah: int, cores: int, camera: int, condition: str = "new"):
    global live_model
    
    # 1. البحث عن تطابق تام في قاعدة البيانات
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        # إصلاح اسم عمود الكاميرا واسم الجدول
        cursor.execute('SELECT price_usd FROM "PhoneCatalog" WHERE brand=%s AND ram_mb=%s AND primary_camera_mp=%s LIMIT 1', (brand, ram_mb, camera))
        result = cursor.fetchone()
        conn.close()
    except Exception as e:
        print("DB Error:", e)
        result = None

    condition_multipliers = {"new": 1.0, "like_new": 0.85, "good": 0.75, "used_mid": 0.60}
    c_multiplier = condition_multipliers.get(condition, 1.0)

    if result:
        base_price = float(result[0])
        source = "Neon Database (Exact Match)"
    else:
        if live_model is None:
            return {"error": "AI model not trained yet."}
            
        data = pd.DataFrame([[brand, ram_mb, battery_mah, cores, camera]], 
                            columns=['brand', 'ram_mb', 'battery_mah', 'cores', 'primary_camera_mp'])
        base_price = live_model.predict(data)[0]
        source = "AI Prediction (Learned from Market)"

    final_price = base_price * c_multiplier
    
    return {
        "source": source,
        "base_price_usd": round(base_price, 2),
        "final_price_usd": round(final_price, 2)
    }