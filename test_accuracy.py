import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import warnings

warnings.filterwarnings("ignore")

NEON_DB_URL = "postgresql://neondb_owner:npg_RamBCOz0W8Ub@ep-rapid-dream-at6x8dkc-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

print("🔍 Fetching data from Neon to test AI accuracy...")
try:
    conn = psycopg2.connect(NEON_DB_URL)
    query = 'SELECT brand, ram_mb, battery_mah, cores, primary_camera_mp, price_usd FROM "PhoneCatalog"'
    df = pd.read_sql_query(query, conn)
    conn.close()

    # فصل البيانات: الماركة والمواصفات (X) والسعر (y)
    X = df[['brand', 'ram_mb', 'battery_mah', 'cores', 'primary_camera_mp']]
    y = df['price_usd']

    # إخفاء 20% من البيانات للاختبار
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # تجهيز الموديل
    preprocessor = ColumnTransformer(
        transformers=[('brand_encoder', OneHotEncoder(handle_unknown='ignore'), ['brand'])],
        remainder='passthrough'
    )

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42))
    ])

    # التدريب على 80%
    model.fit(X_train, y_train)

    # التوقع على الـ 20% المخفية
    predictions = model.predict(X_test)

    # حساب الأخطاء
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions) * 100

    print("\n" + "="*40)
    print("🎯 AI MODEL PERFORMANCE REPORT")
    print("="*40)
    print(f"📊 Accuracy (R² Score): {r2:.2f}%")
    print(f"💵 Average Error (MAE): The AI misses the real price by about ${mae:.2f} on average.")
    print("="*40)
    
except Exception as e:
    print(f"❌ Error: {e}")