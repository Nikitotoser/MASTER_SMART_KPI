import time
import random
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.core.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

def generate_fake_data():
    print("🚀 Генерація фейкових даних для SmartEnergy Lab...")
    
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        now = datetime.utcnow()
        points = []
        
        print("Створюємо телеметрію та погоду за останні 30 днів...")
        for day in range(30, -1, -1):
            for hour in range(24):
                # 15-хвилинні інтервали
                for minute in (0, 15, 30, 45):
                    timestamp = now - timedelta(days=day, hours=hour, minutes=minute)
                    
                    # Симуляція сонячного циклу (вдень напруга є, вночі майже нуль)
                    if 7 <= hour <= 19:
                        solar_v = round(random.uniform(15.0, 19.5), 2)
                        solar_a = round(random.uniform(1.5, 4.5), 2)
                        temp_c = round(random.uniform(10.0, 25.0), 1)
                        solar_rad = round(random.uniform(200.0, 800.0), 1)
                    else:
                        solar_v = round(random.uniform(0.1, 0.5), 2)
                        solar_a = round(random.uniform(0.01, 0.1), 2)
                        temp_c = round(random.uniform(5.0, 15.0), 1)
                        solar_rad = 0.0

                    # 1. Дані сенсорів
                    p_telemetry = Point("sensor_telemetry") \
                        .field("solar_v", solar_v) \
                        .field("solar_a", solar_a) \
                        .time(timestamp)
                    points.append(p_telemetry)
                    
                    # 2. Історична погода
                    p_weather = Point("weather") \
                        .tag("type", "historical") \
                        .field("temp_c", temp_c) \
                        .field("cloud_cover_pct", float(random.randint(0, 100))) \
                        .field("solar_rad_w_m2", solar_rad) \
                        .time(timestamp)
                    points.append(p_weather)

        print(f"Запис {len(points)} точок у базу...")
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print("✅ Історичні дані успішно додано!")
        
        # 3. Майбутня погода для прогнозів (на 24 години вперед)
        print("Створюємо прогноз погоди на завтра...")
        future_points = []
        for hour in range(1, 25):
            future_ts = now + timedelta(hours=hour)
            if 7 <= future_ts.hour <= 19:
                f_temp = round(random.uniform(15.0, 22.0), 1)
                f_rad = round(random.uniform(300.0, 700.0), 1)
            else:
                f_temp = round(random.uniform(8.0, 12.0), 1)
                f_rad = 0.0
                
            p_future = Point("weather") \
                .tag("type", "future") \
                .field("temp_c", f_temp) \
                .field("cloud_cover_pct", float(random.randint(10, 80))) \
                .field("solar_rad_w_m2", f_rad) \
                .time(future_ts)
            future_points.append(p_future)
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=future_points)
        print("✅ Майбутню погоду додано!")

if __name__ == "__main__":
    generate_fake_data()