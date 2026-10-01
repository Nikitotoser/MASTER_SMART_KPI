import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PredictionChart = ({ data }) => {
  const cardStyle = {
    backgroundColor: '#FFFFFF', padding: '24px', borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', border: '1px solid #F3F4F6',
    marginBottom: '32px'
  };

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: '#0F172A' }}>🔮 Стратегічний ML-прогноз на 24 години</h3>
        <span style={{ fontSize: '13px', backgroundColor: '#EEF2FF', color: '#4F46E5', padding: '6px 14px', borderRadius: '20px', fontWeight: '600' }}>Модель: LightGBM</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="displayTime" stroke="#94A3B8" tick={{ fontSize: 12, fill: '#64748B' }} tickMargin={10} axisLine={false} tickLine={false} />
          <YAxis stroke="#94A3B8" tick={{ fontSize: 12, fill: '#64748B' }} tickMargin={10} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} itemStyle={{ fontWeight: '600' }} />
          <Area type="monotone" dataKey="power" stroke="#8B5CF6" strokeDasharray="6 4" fillOpacity={1} fill="url(#colorPred)" name="Очікувана потужність (Вт)" strokeWidth={3} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PredictionChart;