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
    </div>
  );
};

export default Header;