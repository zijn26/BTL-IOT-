import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../../styles/TemperatureChart.css';

export interface ChartPoint {
  time: string;
  temperature: number;
  humidity: number;
}

interface TemperatureChartProps {
  data: ChartPoint[];
}

const TemperatureChart: React.FC<TemperatureChartProps> = ({ data }) => {
  return (
    <div className="chart-container">
      <h3 className="chart-title">Dữ liệu cảm biến (5 phút gần nhất)</h3>
      <div className="chart-legend">
        <div className="legend-item">
          <div className="legend-dot orange"></div>
          <span className="legend-text">Nhiệt độ (°C)</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot blue"></div>
          <span className="legend-text">Độ ẩm (%)</span>
        </div>
      </div>

      <div className="chart-area">
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <Tooltip 
              contentStyle={{ 
                background: '#1f2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Legend 
              wrapperStyle={{ 
                color: '#9ca3af',
                paddingTop: '20px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="temperature" 
              stroke="#fb923c" 
              strokeWidth={3}
              dot={{ fill: '#fb923c', r: 5 }}
              activeDot={{ r: 7 }}
              name="Nhiệt độ (°C)"
            />
            <Line 
              type="monotone" 
              dataKey="humidity" 
              stroke="#60a5fa" 
              strokeWidth={3}
              dot={{ fill: '#60a5fa', r: 5 }}
              activeDot={{ r: 7 }}
              name="Độ ẩm (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TemperatureChart;


