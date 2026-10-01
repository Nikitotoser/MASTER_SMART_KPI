import React, { useState, useEffect } from 'react';
import axios from 'axios';

import Header from './components/Header';
import KPICards from './components/KPICards';
import TelemetryChart from './components/TelemetryChart';
import PredictionChart from './components/PredictionChart';
import DataTable from './components/DataTable';

// Ініціалізація ендпоінтів через змінні середовища для підтримки контейнеризації
const TELEMETRY_API = import.meta.env.VITE_TELEMETRY_API || 'http://localhost:6006/api/v1';
const ML_API = import.meta.env.VITE_ML_API || 'http://localhost:8000/api/predictions';

function App() {
  const [telemetry, setTelemetry] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [modelMetrics, setModelMetrics] = useState({ version: '-', mae: '0', mse: '0' });
  const [status, setStatus] = useState('ОФЛАЙН');

  /**
   * Нормалізація часових міток (UNIX timestamp)
   * Забезпечує сумісність з різними форматами відповідей від мікросервісів
   */
  const getSafeTimeMs = (t) => {
    if (!t) return Date.now();
    if (typeof t === 'string' && !isNaN(Number(t))) t = Number(t);
    if (typeof t === 'number') return t < 9999999999 ? t * 1000 : t;
    const parsed = new Date(t).getTime();
    return isNaN(parsed) ? Date.now() : parsed;
  };

  /**
   * Асинхронний запит телеметрії реального часу
   * Оновлює стан графіків та статус підключення Edge-пристрою
   */
  const fetchTelemetry = async () => {
    try {
      const response = await axios.get(`${TELEMETRY_API}/telemetry/latest?limit=50`);
      const rawData = response.data;
      if (!rawData?.length) return;

      const processedData = rawData.map(item => ({
        ...item,
        timestampMs: getSafeTimeMs(item.ts),
        displayTime: new Date(getSafeTimeMs(item.ts)).toLocaleTimeString('uk-UA'),
        power: parseFloat((item.solar_v * item.solar_a).toFixed(2))
      }));

      // Реверсування масиву для коректного рендерингу осей графіка
      setTelemetry(processedData.reverse());
      
      // Детекція втрати зв'язку (Таймаут: 15 секунд)
      const nowSeconds = Math.floor(Date.now() / 1000);
      setStatus((nowSeconds - rawData[0].ts) < 15 ? 'ОНЛАЙН' : 'ОФЛАЙН');
    } catch (error) {
      console.error("Помилка синхронізації телеметрії:", error);
      setStatus('ОФЛАЙН');
    }
  };

  /**
   * Асинхронний запит ML-прогнозів та MLOps метрик
   */
  const fetchMLData = async () => {
    try {
      // Базова URL-адреса з твого docker-compose
      const ML_BASE = import.meta.env.VITE_ML_API || 'http://localhost:8000/api';

      // 1. Точний шлях до прогнозів
      const predRes = await axios.get(`${ML_BASE}/predictions/latest`);
      if (predRes.data?.times && predRes.data?.powers) {
        const formattedPreds = predRes.data.times.map((t, i) => ({
          timestampMs: getSafeTimeMs(t),
          displayTime: new Date(getSafeTimeMs(t)).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(predRes.data.powers[i].toFixed(2))
        }));
        setPredictions(formattedPreds);
      }

      // 2. Точний шлях до метрик
      const metricRes = await axios.get(`${ML_BASE}/model/metrics`);
      if (!metricRes.data.error) setModelMetrics(metricRes.data);

    } catch (error) {
      console.error("Помилка синхронізації з ML-сервісом:", error);
    }
  };

  /**
   * Ініціалізація життєвого циклу компонента та фонового поллінгу
   */
  useEffect(() => {
    fetchTelemetry();
    fetchMLData();

    const telInterval = setInterval(fetchTelemetry, 2000); // Оновлення HMI кожні 2 сек
    const mlInterval = setInterval(fetchMLData, 300000);   // Оновлення ML кожні 5 хв

    return () => {
      clearInterval(telInterval);
      clearInterval(mlInterval);
    };
  }, []);

  return (
    <div style={{ padding: '30px 40px', backgroundColor: '#F8FAFC', minHeight: '100vh' }}>
      <Header onExport={() => console.log("Ініціалізація експорту CSV")} />
      
      <KPICards 
        status={status} 
        latestTelemetry={telemetry[telemetry.length - 1]} 
        predictedPeak={Math.max(...predictions.map(p => p.power), 0)}
        modelMetrics={modelMetrics} 
      />

      <TelemetryChart data={telemetry} />
      <PredictionChart data={predictions} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '24px' }}>
         <DataTable title="📡 Журнал телеметрії (Факт)" data={telemetry} type="telemetry" />
         <DataTable title="🔮 Журнал прогнозування (ML)" data={predictions} type="prediction" />
      </div>
    </div>
  );
}

export default App;