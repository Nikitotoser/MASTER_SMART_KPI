import React from 'react';

const KPICards = ({ status, latestTelemetry, predictedPeak, modelMetrics }) => {
  const cardStyle = {
    backgroundColor: '#FFFFFF', padding: '24px', borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
    border: '1px solid #F3F4F6'
  };
  const labelStyle = { fontSize: '13px', color: '#6B7280', fontWeight: '600', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' };
  const valueStyle = { fontSize: '26px', fontWeight: '800', color: '#111827' };

  // Безпечний розрахунок поточних потужностей якщо даних ще немає
  const power = {
    solar: latestTelemetry ? (latestTelemetry.solar_v * latestTelemetry.solar_a).toFixed(2) : 0,
    battery: latestTelemetry ? (latestTelemetry.bat_v * latestTelemetry.bat_a).toFixed(2) : 0
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px', marginBottom: '32px' }}>
      <div style={{ ...cardStyle, borderLeft: status === 'ОНЛАЙН' ? '4px solid #10B981' : '4px solid #EF4444' }}>
        <div style={labelStyle}>Статус системи</div>
        <div style={{ ...valueStyle, color: status === 'ОНЛАЙН' ? '#10B981' : '#EF4444' }}>{status}</div>
      </div>
      <div style={{ ...cardStyle, borderLeft: '4px solid #F59E0B' }}>
        <div style={labelStyle}>Генерація (Сонце)</div>
        <div style={valueStyle}>{power.solar} <span style={{ fontSize: '15px', color: '#94A3B8', fontWeight: '500' }}>Вт</span></div>
      </div>
      <div style={{ ...cardStyle, borderLeft: '4px solid #3B82F6' }}>
        <div style={labelStyle}>Навантаження (Батарея)</div>
        <div style={valueStyle}>{power.battery} <span style={{ fontSize: '15px', color: '#94A3B8', fontWeight: '500' }}>Вт</span></div>
      </div>
      <div style={{ ...cardStyle, borderLeft: '4px solid #8B5CF6' }}>
        <div style={labelStyle}>Очікуваний пік (ML)</div>
        <div style={valueStyle}>{predictedPeak} <span style={{ fontSize: '15px', color: '#94A3B8', fontWeight: '500' }}>Вт</span></div>
      </div>
      <div style={{ ...cardStyle, borderLeft: '4px solid #6366F1', backgroundColor: '#F3F4F6' }}>
        <div style={labelStyle}>Якість моделі (LightGBM)</div>
        <div style={{ fontSize: '18px', fontWeight: '700', color: '#334155' }}>
          MAE: <span style={{ color: '#6366F1' }}>{modelMetrics.mae}</span> | MSE: <span style={{ color: '#6366F1' }}>{modelMetrics.mse}</span>
        </div>
        <div style={{ fontSize: '13px', color: '#94A3B8', marginTop: '6px', fontWeight: '500' }}>Версія: {modelMetrics.version}</div>
      </div>
    </div>
  );
};

export default KPICards;