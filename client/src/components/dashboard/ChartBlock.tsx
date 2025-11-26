import React, { useState, useEffect } from 'react';
import { DashboardBlock } from './Dashboard';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ChartBlockProps {
  block: DashboardBlock;
  onConfigure: () => void;
  onDelete: () => void;
}

interface SensorData {
  id: number;
  virtual_pin: number;
  value_numeric: number;
  value_string: string;
  timestamp: string;
  token_verify: string;
}

const ChartBlock: React.FC<ChartBlockProps> = ({ block, onConfigure, onDelete }) => {
  const [data, setData] = useState<SensorData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const fetchSensorData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Chưa đăng nhập');
        return;
      }

      const res = await fetch(
        `${API_BASE}/sensors/sensor-data?token_verify=${block.token_verify}&limit=10&virtual_pin=${block.virtual_pin}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.message || 'Không thể tải dữ liệu');
      }

      // Lấy tối đa 10 dữ liệu gần nhất, sắp xếp theo timestamp
      let sensorData = result.data || [];
      
      // Sắp xếp theo timestamp tăng dần (cũ -> mới) để vẽ biểu đồ đúng
      sensorData = sensorData
        .sort((a: SensorData, b: SensorData) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        )
        .slice(-10); // Lấy 10 điểm cuối (gần nhất)
      
      setData(sensorData);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching sensor data:', err);
      setError(err?.message || 'Lỗi khi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchSensorData();
  }, [block.token_verify, block.virtual_pin]);

  // Auto refresh every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchSensorData();
    }, 20000); // 5 seconds

    return () => clearInterval(interval);
  }, [block.token_verify, block.virtual_pin]);

  // Helper function để lấy giá trị numeric từ data (support cả value_numeric và value_string)
  const getNumericValue = (d: SensorData): number => {
    if (d.value_numeric !== null && d.value_numeric !== undefined) {
      return d.value_numeric;
    }
    // Nếu không có value_numeric, thử parse value_string thành number
    if (d.value_string) {
      const parsed = parseFloat(d.value_string);
      return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
  };

  // Fixed Y-axis range từ 18 đến 35 độ
  const scaleMin = 18;
  const scaleMax = 35;
  const scaleRange = scaleMax - scaleMin; // 17

  // Generate SVG path for line chart
  const generatePath = () => {
    if (data.length === 0) return '';
    
    return data.map((d, i) => {
      const x = (i / (data.length - 1 || 1)) * 100;
      const numericValue = getNumericValue(d);
      const y = 100 - ((numericValue - scaleMin) / scaleRange) * 100;
      return `${i === 0 ? 'M' : 'L'} ${x},${y}`;
    }).join(' ');
  };

  // Get current value (numeric hoặc string)
  const getDisplayValue = (d: SensorData): string => {
    if (d.value_numeric !== null && d.value_numeric !== undefined) {
      return d.value_numeric.toFixed(1);
    }
    return d.value_string || 'N/A';
  };

  // Format timestamp to time (HH:mm)
  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
    } catch (err) {
      return timestamp;
    }
  };

  // Format timestamp to date (MMM dd)
  const formatDate = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    } catch (err) {
      return '';
    }
  };

  // Format value for display
  const formatValue = (val: number): string => {
    return val.toFixed(1);
  };

  // Generate Y-axis labels (5 labels distributed evenly)
  const yAxisLabels = [
    { value: scaleMax, y: 0 },
    { value: scaleMin + scaleRange * 0.75, y: 25 },
    { value: scaleMin + scaleRange * 0.5, y: 50 },
    { value: scaleMin + scaleRange * 0.25, y: 75 },
    { value: scaleMin, y: 100 }
  ];

  // Generate X-axis labels (show every few points, max 6 labels)
  const xAxisStep = Math.max(1, Math.floor(data.length / 5));
  const xAxisLabels = data.filter((_, i) => i % xAxisStep === 0 || i === data.length - 1);

  const currentValue = data.length > 0 ? getDisplayValue(data[data.length - 1]) : '0';

  return (
    <div className="chart-block">
      <div className="block-header">
        <span className="block-label">{block.label_block}</span>
        <div className="block-actions">
          <button 
            className="block-action-btn"
            onClick={onConfigure}
            title="Cấu hình"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="8" cy="8" r="2" />
              <path d="M8 2v1.33M8 12.67V14M2 8h1.33M12.67 8H14M3.05 3.05l.94.94M11.01 11.01l.94.94M3.05 12.95l.94-.94M11.01 4.99l.94-.94" />
            </svg>
          </button>
          <button 
            className="block-action-btn block-action-delete"
            onClick={onDelete}
            title="Xóa"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4h8v10a1 1 0 01-1 1H5a1 1 0 01-1-1V4zM6 2h4M2 4h12" />
            </svg>
          </button>
        </div>
      </div>

      <div className="block-info">
        <span className="block-device">{block.device_name}</span>
        <span className="block-pin">Pin {block.virtual_pin}</span>
      </div>

      {loading ? (
        <div className="chart-loading">
          <svg className="spinner" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : error ? (
        <div className="chart-error">
          <p>{error}</p>
        </div>
      ) : data.length === 0 ? (
        <div className="chart-empty">
          <p>Chưa có dữ liệu từ cảm biến</p>
        </div>
      ) : (
        <>
          <div className="chart-current-value">
            <span className="chart-value">{currentValue}</span>
            <span className="chart-unit">{block.pin_label}</span>
          </div>

          <div className="chart-container">
            {/* Y-axis labels */}
            <div className="chart-y-axis-labels">
              {yAxisLabels.map((label, i) => (
                <div key={i} className="chart-y-label">
                  {formatValue(label.value)}
                </div>
              ))}
            </div>

            {/* Chart SVG */}
            <div className="chart-svg-wrapper">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="chart-svg">
                <defs>
                  {/* Gradient for fill area */}
                  <linearGradient id={`gradient-${block.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.05" />
                  </linearGradient>
                  {/* Glow effect for hovered point */}
                  <filter id={`glow-${block.id}`}>
                    <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>

                {/* Horizontal grid lines */}
                {[0, 25, 50, 75, 100].map((y, i) => (
                  <line
                    key={`h-${i}`}
                    x1="0"
                    y1={y}
                    x2="100"
                    y2={y}
                    stroke="rgba(148, 163, 184, 0.3)"
                    strokeWidth="0.3"
                    strokeDasharray={y === 0 || y === 100 ? "0" : "2,2"}
                    opacity={y === 0 || y === 100 ? "0.5" : "0.3"}
                  />
                ))}

                {/* Vertical grid lines */}
                {xAxisLabels.map((d, i) => {
                  const index = data.indexOf(d);
                  const x = (index / (data.length - 1 || 1)) * 100;
                  return (
                    <line
                      key={`v-${i}`}
                      x1={x}
                      y1="0"
                      x2={x}
                      y2="100"
                      stroke="rgba(148, 163, 184, 0.2)"
                      strokeWidth="0.3"
                      strokeDasharray="2,2"
                      opacity="0.2"
                    />
                  );
                })}

                {/* Fill area under the line */}
                <path
                  d={`${generatePath()} L 100,100 L 0,100 Z`}
                  fill={`url(#gradient-${block.id})`}
                />

                {/* Main line chart */}
                <path
                  d={generatePath()}
                  fill="none"
                  stroke="#22d3ee"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="chart-line"
                  style={{
                    filter: 'drop-shadow(0 0 4px rgba(34, 211, 238, 0.4))'
                  }}
                />

                {/* Data points */}
                {data.map((d, i) => {
                  const x = (i / (data.length - 1 || 1)) * 100;
                  const numericValue = getNumericValue(d);
                  const y = 100 - ((numericValue - scaleMin) / scaleRange) * 100;
                  const isHovered = hoveredIndex === i;
                  const displayValue = getDisplayValue(d);
                  
                  return (
                    <g key={d.id}>
                      {/* Outer circle */}
                      <circle
                        cx={x}
                        cy={y}
                        r={isHovered ? "2.5" : "1.8"}
                        fill={isHovered ? "#ffffff" : "#22d3ee"}
                        stroke="#22d3ee"
                        strokeWidth={isHovered ? "2" : "1.5"}
                        style={{ 
                          cursor: 'pointer',
                          transition: 'all 0.2s ease-in-out'
                        }}
                        filter={isHovered ? `url(#glow-${block.id})` : undefined}
                        onMouseEnter={() => setHoveredIndex(i)}
                        onMouseLeave={() => setHoveredIndex(null)}
                      />
                      
                      {/* Tooltip on hover */}
                      {isHovered && (
                        <g>
                          {/* Tooltip background */}
                          <rect
                            x={x < 50 ? x + 4 : x - 30}
                            y={y - 14}
                            width="26"
                            height="12"
                            rx="2"
                            fill="rgba(15, 23, 42, 0.95)"
                            stroke="#22d3ee"
                            strokeWidth="0.5"
                            opacity="0.95"
                          />
                          {/* Value */}
                          <text
                            x={x < 50 ? x + 17 : x - 17}
                            y={y - 8.5}
                            textAnchor="middle"
                            fill="#22d3ee"
                            fontSize="3.5"
                            fontWeight="600"
                          >
                            {displayValue}
                          </text>
                          {/* Time */}
                          <text
                            x={x < 50 ? x + 17 : x - 17}
                            y={y - 4.5}
                            textAnchor="middle"
                            fill="#94a3b8"
                            fontSize="2.5"
                          >
                            {formatTimestamp(d.timestamp)}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* X-axis labels */}
            <div className="chart-x-axis-labels">
              {xAxisLabels.map((d, i) => (
                <div key={i} className="chart-x-label">
                  <span className="chart-x-time">{formatTimestamp(d.timestamp)}</span>
                  <span className="chart-x-date">{formatDate(d.timestamp)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-time-info">
            <span>{data.length}/10 điểm dữ liệu</span>
            {data.length > 0 && (
              <span>{formatTimestamp(data[data.length - 1].timestamp)} (tự động cập nhật mỗi 20s)</span>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ChartBlock;

