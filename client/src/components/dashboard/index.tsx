import React from 'react';
import '../../styles/Dashboard.css';
import TemperatureStats from './TemperatureStats';
import TemperatureChart, { ChartPoint } from './TemperatureChart';

interface DashboardProps {
  temperatureText: string;
  humidityText: string;
  data: ChartPoint[];
}

const Dashboard: React.FC<DashboardProps> = ({ temperatureText, humidityText, data }) => {
  return (
    <main className="main-content">
      <div className="main-header">
        <svg className="main-header-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        <h2 className="main-header-title">Dashboard</h2>
      </div>

      <TemperatureStats temperatureText={temperatureText} humidityText={humidityText} />
      <TemperatureChart data={data} />
    </main>
  );
};

export default Dashboard;


