import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TelemetryChart = ({ data }) => {
  const cardStyle = {
    backgroundColor: '#FFFFFF', padding: '24px', borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', border: '1px solid #F3F4F6',
    marginBottom: '24px'
  };

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: '#0F172A' }}>⚡ Пульс системи: Real-time телеметрія</h3>
        <span style={{ fontSize: '13px', backgroundColor: '#EFF6FF', color: '#3B82F6', padding: '6px 14px', borderRadius: '20px', fontWeight: '600' }}>Live (Оновлення 2 сек)</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorFact" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="displayTime" stroke="#94A3B8" tick={{ fontSize: 12, fill: '#64748B' }} tickMargin={10} axisLine={false} tickLine={false} />
          <YAxis stroke="#94A3B8" tick={{ fontSize: 12, fill: '#64748B' }} tickMargin={10} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} itemStyle={{ fontWeight: '600' }} />
          <Area type="monotone" dataKey="power" stroke="#3B82F6" fillOpacity={1} fill="url(#colorFact)" name="Поточна потужність (Вт)" strokeWidth={3} activeDot={{ r: 6, strokeWidth: 2 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TelemetryChart;