import React from 'react';
import '../../styles/TemperatureStats.css';

interface TemperatureStatsProps {
  temperatureText: string; // e.g. "27.7°C"
  humidityText: string; // e.g. "61.1%"
}

const TemperatureStats: React.FC<TemperatureStatsProps> = ({ temperatureText, humidityText }) => {
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <h3 className="stat-label">Nhiệt độ</h3>
        <p className="stat-value temperature">{temperatureText}</p>
      </div>
      <div className="stat-card">
        <h3 className="stat-label">Độ ẩm</h3>
        <p className="stat-value humidity">{humidityText}</p>
      </div>
    </div>
  );
};

export default TemperatureStats;


