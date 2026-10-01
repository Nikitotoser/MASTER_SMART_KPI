import React from 'react';

const DataTable = ({ title, data, type }) => {
  const cardStyle = {
    backgroundColor: '#FFFFFF', padding: '24px', borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', border: '1px solid #F3F4F6'
  };

  return (
    <div style={cardStyle}>
      <h3 style={{ margin: '0 0 20px 0', fontSize: '16px', fontWeight: '700', color: '#0F172A' }}>{title}</h3>
      <div style={{ overflowX: 'auto', maxHeight: '300px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead style={{ position: 'sticky', top: 0, backgroundColor: '#fff' }}>
            <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#64748B' }}>
              <th style={{ padding: '12px 10px' }}>{type === 'telemetry' ? 'Час (Факт)' : 'Очікуваний час'}</th>
              
              {/* Різні колонки залежно від типу даних */}
              {type === 'telemetry' ? (
                <>
                  <th style={{ padding: '12px 10px' }}>Сонце (V)</th>
                  <th style={{ padding: '12px 10px' }}>Сонце (A)</th>
                  <th style={{ padding: '12px 10px' }}>Батарея (V)</th>
                  <th style={{ padding: '12px 10px' }}>Батарея (A)</th>
                </>
              ) : (
                <th style={{ padding: '12px 10px' }}>Прогнозована потужність (Вт)</th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 20).map((row, index) => (
              <tr key={index} style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '10px', color: '#475569', fontWeight: '500' }}>
                  {new Date(row.timestampMs).toLocaleString('uk-UA')}
                </td>
                
                {/* Різні дані залежно від типу */}
                {type === 'telemetry' ? (
                  <>
                    <td style={{ padding: '10px', fontWeight: '700', color: '#F59E0B' }}>{row.solar_v}</td>
                    <td style={{ padding: '10px', color: '#64748B' }}>{row.solar_a}</td>
                    <td style={{ padding: '10px', fontWeight: '700', color: '#3B82F6' }}>{row.bat_v}</td>
                    <td style={{ padding: '10px', color: '#64748B' }}>{row.bat_a}</td>
                  </>
                ) : (
                  <td style={{ padding: '10px', fontWeight: '700', color: '#8B5CF6' }}>{row.power}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;