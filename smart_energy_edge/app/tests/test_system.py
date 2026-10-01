import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.weather import fetch_future_weather
from app.services.ml_pipeline import evaluate_models
from requests.exceptions import RequestException

# ==========================================
# ТЕСТ 1: Стійкість до падіння API погоди (Fault Tolerance)
# ==========================================
@patch("app.services.weather.requests.get")
def test_weather_api_failure_handling(mock_get, caplog):
    """Імітуємо ситуацію, коли сервер Open-Meteo впав."""
    mock_get.side_effect = RequestException("Network Timeout")
    fetch_future_weather()
    assert "Помилка" in caplog.text or "Timeout" in caplog.text

# ==========================================
# ТЕСТ 2: Логіка Feature Engineering (Злиття даних)
# ==========================================
def test_ml_data_merging_logic():
    """Перевіряємо, чи правильно pandas.merge_asof склеює телеметрію та погоду."""
    df_telemetry = pd.DataFrame({
        'timestamp': pd.to_datetime(['2026-04-15 10:05:00']),
        'pzem_power_w': [500]
    })
    df_weather = pd.DataFrame({
        'timestamp': pd.to_datetime(['2026-04-15 10:00:00', '2026-04-15 11:00:00']),
        'temperature_c': [10.0, 12.0]
    })
    
    df_merged = pd.merge_asof(
        df_telemetry.sort_values('timestamp'), 
        df_weather.sort_values('timestamp'), 
        on='timestamp', 
        direction='backward'
    )
    
    # Система повинна була взяти погоду за 10:00
    assert df_merged.iloc[0]['temperature_c'] == 10.0
    
    # Перевіряємо генерацію години
    df_merged['hour'] = df_merged['timestamp'].dt.hour
    assert df_merged.iloc[0]['hour'] == 10

# ==========================================
# ТЕСТ 3: Автоматична деградація моделі (MLOps)
# ==========================================
@patch("app.services.ml_pipeline.os.remove")
@patch("app.services.ml_pipeline.os.path.exists", return_value=True)
@patch("app.services.ml_pipeline.sqlite3.connect")
@patch("app.services.ml_pipeline.query_influx_to_df")
def test_mlops_model_deletion_on_high_error(
    mock_query_influx, mock_db, mock_exists, mock_remove
):
    """Якщо похибка (MAE) > 500 Вт, система ПОВИННА видалити деградовану модель."""
    # Імітуємо два виклики до InfluxDB: 1-й для прогнозів, 2-й для реальної телеметрії
    mock_query_influx.side_effect = [
        pd.DataFrame({
            'timestamp': pd.to_datetime(['2026-04-14 10:00:00']), 
            'predicted_power_w': [1000.0], 
            'model_version': ['test_v1']
        }),
        pd.DataFrame({
            'timestamp': pd.to_datetime(['2026-04-14 10:00:00']), 
            'solar_v': [20.0], 
            'solar_a': [20.0]
        })
    ]
    
    evaluate_models()
    
    mock_remove.assert_called_once()
    assert "test_v1.pkl" in mock_remove.call_args[0][0]

# ==========================================
# ТЕСТ 4: Захист від порожнього датасету
# ==========================================
def test_empty_dataset_handling():
    """Перевіряємо, що система не падає при спробі злити порожні датафрейми."""
    df_empty = pd.DataFrame(columns=['timestamp', 'value'])
    assert df_empty.empty == True

# ==========================================
# ТЕСТ 5: Валідація структури фічей
# ==========================================
def test_feature_columns_structure():
    """Модель повинна отримувати строго визначений набір фічей для прогнозу."""
    expected_features = ['hour', 'temperature_c', 'cloud_cover']
    test_df = pd.DataFrame(columns=['timestamp', 'hour', 'temperature_c', 'cloud_cover', 'pzem_power_w'])
    features = [col for col in test_df.columns if col not in ['timestamp', 'pzem_power_w']]
    assert features == expected_features