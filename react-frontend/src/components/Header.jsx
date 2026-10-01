import React from 'react';

const Header = ({ onExport }) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
      <div>
        <h1 style={{ fontSize: '28px', fontWeight: '800', margin: 0, color: '#0F172A', display: 'flex', alignItems: 'center', gap: '8px', letterSpacing: '-0.02em' }}>
          <span style={{ color: '#3B82F6' }}>⚡</span> SmartEnergy Lab
        </h1>
        <p style={{ color: '#64748B', margin: '4px 0 0 0', fontSize: '15px' }}>
          Панель диспетчеризації та MLOps
        </p>
      </div>
      <button
        onClick={onExport}
        style={{
          padding: '10px 24px', backgroundColor: '#3B82F6', color: 'white',
          border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '14px',
          fontWeight: '600', boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)',
          transition: 'all 0.2s'
        }}
        onMouseOver={(e) => e.target.style.backgroundColor = '#2563EB'}
        onMouseOut={(e) => e.target.style.backgroundColor = '#3B82F6'}
      >
        Експорт CSV
      </button>
    </div>
  );
};

export default Header;