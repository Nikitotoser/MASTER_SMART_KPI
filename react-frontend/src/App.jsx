import React, { useState, useEffect } from 'react';
import axios from 'axios';

import Header from './components/Header';
import KPICards from './components/KPICards';
import TelemetryChart from './components/TelemetryChart';
import PredictionChart from './components/PredictionChart';
import DataTable from './components/DataTable';

const TELEMETRY_API = import.meta.env.VITE_TELEMETRY_API || 'http://localhost:6006/api/v1';
const ML_API = import.meta.env.VITE_ML_API || 'http://localhost:8000/api/predictions';

function App() {
  const [telemetry, setTelemetry] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [modelMetrics, setModelMetrics] = useState({ version: '-', mae: '0', mse: '0' });
  const [status, setStatus] = useState('ОФЛАЙН');

  const getSafeTimeMs = (t) => {
    if (!t) return Date.now();
    if (typeof t === 'string' && !isNaN(Number(t))) t = Number(t);
    if (typeof t === 'number') return t < 9999999999 ? t * 1000 : t;
    const parsed = new Date(t).getTime();
    return isNaN(parsed) ? Date.now() : parsed;
  };

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

      setTelemetry(processedData.reverse());
      const nowSeconds = Math.floor(Date.now() / 1000);
      setStatus((nowSeconds - rawData[0].ts) < 15 ? 'ОНЛАЙН' : 'ОФЛАЙН');
    } catch (error) {
      setStatus('ОФЛАЙН');
    }
  };

  const fetchMLData = async () => {
    try {
      const ML_BASE = import.meta.env.VITE_ML_API || 'http://localhost:8000/api';
      const predRes = await axios.get(`${ML_BASE}/predictions/latest`);
      if (predRes.data?.times && predRes.data?.powers) {
        const formattedPreds = predRes.data.times.map((t, i) => ({
          timestampMs: getSafeTimeMs(t),
          displayTime: new Date(getSafeTimeMs(t)).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(predRes.data.powers[i].toFixed(2))
        }));
        setPredictions(formattedPreds);
      }
      const metricRes = await axios.get(`${ML_BASE}/model/metrics`);
      if (!metricRes.data.error) setModelMetrics(metricRes.data);
    } catch (error) {}
  };

  // Функції експорту
  const downloadCSV = async (endpoint, filename) => {
    try {
        const response = await fetch(`${TELEMETRY_API}${endpoint}`);
        if (!response.ok) throw new Error('Немає даних');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert(error.message);
    }
  };

  const exportTelemetry = () => downloadCSV('/export/telemetry?days=30', 'telemetry.csv');
  const exportPredictions = () => downloadCSV('/export/predictions?days=30', 'predictions.csv');

  useEffect(() => {
    fetchTelemetry();
    fetchMLData();
    const telInterval = setInterval(fetchTelemetry, 2000);
    const mlInterval = setInterval(fetchMLData, 300000);
    return () => { clearInterval(telInterval); clearInterval(mlInterval); };
  }, []);

  return (
    <div style={{ padding: '30px 40px', backgroundColor: '#F8FAFC', minHeight: '100vh' }}>
      {/* Хедер без кнопки експорту */}
      <Header />
      
      <KPICards 
        status={status} 
        latestTelemetry={telemetry[telemetry.length - 1]} 
        predictedPeak={Math.max(...predictions.map(p => p.power), 0)}
        modelMetrics={modelMetrics} 
      />

      {/* Графік Телеметрії з кнопкою */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1E293B' }}>Графік Телеметрії</h2>
          <button onClick={exportTelemetry} style={{ padding: '8px 16px', background: '#3B82F6', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
            Експорт CSV
          </button>
        </div>
        <TelemetryChart data={telemetry} />
      </div>

      {/* Графік Прогнозу з кнопкою */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1E293B' }}>Графік Прогнозу</h2>
          <button onClick={exportPredictions} style={{ padding: '8px 16px', background: '#8B5CF6', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
            Експорт CSV
          </button>
        </div>
        <PredictionChart data={predictions} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '24px' }}>
         <DataTable title="📡 Журнал телеметрії (Факт)" data={telemetry} type="telemetry" />
         <DataTable title="🔮 Журнал прогнозування (ML)" data={predictions} type="prediction" />
      </div>
    </div>
  );
}

export default App;