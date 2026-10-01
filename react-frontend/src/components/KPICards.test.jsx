import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import KPICards from './KPICards';

describe('Компонент KPICards', () => {
  const mockMetrics = { version: 'v1.0', mae: '10.5', mse: '110.2' };
  const mockTelemetry = { solar_v: 12, solar_a: 2, bat_v: 12.5, bat_a: -1 };

  it('коректно відображає статус ОНЛАЙН та правильно рахує потужність', () => {
    render(
      <KPICards 
        status="ОНЛАЙН" 
        latestTelemetry={mockTelemetry} 
        predictedPeak={50} 
        modelMetrics={mockMetrics} 
      />
    );
    
    // Перевіряємо, чи є текст статусу
    expect(screen.getByText('ОНЛАЙН')).toBeInTheDocument();
    // Перевіряємо, чи правильно розрахована потужність сонця
    expect(screen.getByText('24.00')).toBeInTheDocument();
  });

  it('змінює колір тексту на червоний при статусі ОФЛАЙН', () => {
    render(
      <KPICards 
        status="ОФЛАЙН" 
        latestTelemetry={null} 
        predictedPeak={0} 
        modelMetrics={mockMetrics} 
      />
    );
    
    const statusElement = screen.getByText('ОФЛАЙН');
    expect(statusElement).toBeInTheDocument();
    
    // В React Testing Library кольори перевіряються через обчислені стилі (RGB)
    expect(statusElement).toHaveStyle({ color: 'rgb(239, 68, 68)' });
  });
});