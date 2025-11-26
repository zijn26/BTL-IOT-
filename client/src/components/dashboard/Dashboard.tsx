import React, { useState, useEffect } from 'react';
import '../../styles/Dashboard.css';
import BlockConfigModal from './BlockConfigModal';
import ChartBlock from './ChartBlock';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface DashboardBlock {
  id: number;
  user_id: number;
  created_at: string;
  typeblock: number;
  label_block: string;
  virtual_pin: number;
  device_name: string;
  pin_label: string;
  token_verify: string;
  value?: number;
}

const Dashboard: React.FC = () => {
  const [buttonBlocks, setButtonBlocks] = useState<DashboardBlock[]>([]);
  const [chartBlocks, setChartBlocks] = useState<DashboardBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState<DashboardBlock | null>(null);
  const [isNewBlock, setIsNewBlock] = useState(false);
  const [blockType, setBlockType] = useState<number>(0);
  
  const [togglingBlockId, setTogglingBlockId] = useState<number | null>(null);

  const normalizeValue = (value: any): number => {
    if (value === undefined || value === null) return 0;
    if (typeof value === 'string') {
      const num = parseInt(value, 10);
      return isNaN(num) ? 0 : (num >= 1 ? 1 : 0);
    }
    return Number(value) >= 1 ? 1 : 0;
  };

  const loadBlocks = async (type: number) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Chưa đăng nhập');
      }

      const res = await fetch(`${API_BASE}/dashborad/blocks?typeblock=${type}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Không thể tải blocks');
      }

      return data.blocks || [];
    } catch (err: any) {
      console.error(`Error loading ${type === 0 ? 'button' : 'chart'} blocks:`, err);
      return [];
    }
  };

  const initializeButtonsToOff = async (buttons: DashboardBlock[]) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const initPromises = buttons.map(async (block) => {
      try {
        await fetch(`${API_BASE}/mqtt/device-command`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token_verify: block.token_verify,
            virtual_pin: block.virtual_pin,
            value: 0,
          }),
        });
      } catch (err) {
        console.error(`Error initializing block ${block.id}:`, err);
      }
    });

    await Promise.allSettled(initPromises);
  };

  const loadAllBlocks = async () => {
    setLoading(true);
    setError(null);
    try {
      const [buttons, charts] = await Promise.all([
        loadBlocks(0),
        loadBlocks(1),
      ]);
      
      const buttonsWithDefaultValue = buttons.map((block: DashboardBlock) => ({
        ...block,
        value: 0,
      }));
      
      setButtonBlocks(buttonsWithDefaultValue);
      setChartBlocks(charts);

      if (buttons.length > 0) {
        await initializeButtonsToOff(buttons);
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllBlocks();
  }, []);

  // Toggle đơn giản: đổi trạng thái và gửi API
  const handleToggleButton = async (block: DashboardBlock) => {
    if (togglingBlockId === block.id) return;
    
    const currentValue = normalizeValue(block.value);
    const newValue = currentValue === 1 ? 0 : 1;
    
    setTogglingBlockId(block.id);
    
    // Đổi trạng thái ngay
    setButtonBlocks(prev => prev.map(b => 
      b.id === block.id ? { ...b, value: newValue } : b
    ));
    
    // Gửi API (không care kết quả)
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch(`${API_BASE}/mqtt/device-command`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token_verify: block.token_verify,
            virtual_pin: block.virtual_pin,
            value: newValue,
          }),
        });
      }
    } catch (err) {
      console.error('Error sending command:', err);
    } finally {
      setTogglingBlockId(null);
    }
  };
  
  const handleConfigureBlock = (block: DashboardBlock) => {
    setSelectedBlock(block);
    setIsNewBlock(false);
    setShowConfigModal(true);
  };

  const handleAddBlock = (type: number) => {
    setSelectedBlock(null);
    setBlockType(type);
    setIsNewBlock(true);
    setShowConfigModal(true);
  };

  const handleDeleteBlock = async (block: DashboardBlock) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa block "${block.label_block}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Chưa đăng nhập');
        return;
      }

      const res = await fetch(`${API_BASE}/dashborad/block?id=${block.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || 'Xóa block thất bại');
        return;
      }

      await loadAllBlocks();
      alert('Đã xóa block thành công');
    } catch (err: any) {
      alert(err?.message || 'Lỗi khi xóa block');
    }
  };

  const handleSaveConfig = async () => {
    await loadAllBlocks();
    setShowConfigModal(false);
    setSelectedBlock(null);
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-loading">Đang tải...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-error">
          <p>{error}</p>
          <button className="btn" onClick={loadAllBlocks}>Thử lại</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <div className="dashboard-icon-wrapper">
            <svg className="dashboard-main-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          <div>
            <h1 className="dashboard-title">Bảng điều khiển</h1>
            <p className="dashboard-subtitle">Quản lý và giám sát thiết bị IoT</p>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Left: Button Blocks */}
        <div className="dashboard-section">
          <div className="section-header">
            <h3 className="section-title">Điều khiển thiết bị</h3>
            <button className="btn-add-block" onClick={() => handleAddBlock(0)}>
              <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M8 2v12M2 8h12" />
              </svg>
              Thêm nút
            </button>
          </div>

          <div className="blocks-grid">
            {buttonBlocks.length === 0 ? (
              <div className="empty-state">
                <p>Chưa có nút điều khiển nào</p>
                <button className="btn-secondary" onClick={() => handleAddBlock(0)}>
                  Thêm nút đầu tiên
                </button>
              </div>
            ) : (
              buttonBlocks.map((block) => (
                <div key={block.id} className="button-block">
                  <div className="block-header">
                    <span className="block-label">{block.label_block}</span>
                    <div className="block-actions">
                      <button 
                        className="block-action-btn"
                        onClick={() => handleConfigureBlock(block)}
                        title="Cấu hình"
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="8" cy="8" r="2" />
                          <path d="M8 2v1.33M8 12.67V14M2 8h1.33M12.67 8H14M3.05 3.05l.94.94M11.01 11.01l.94.94M3.05 12.95l.94-.94M11.01 4.99l.94-.94" />
                        </svg>
                      </button>
                      <button 
                        className="block-action-btn block-action-delete"
                        onClick={() => handleDeleteBlock(block)}
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
                  <button 
                    className={`toggle-button ${normalizeValue(block.value) === 1 ? 'active' : ''} ${togglingBlockId === block.id ? 'loading' : ''}`}
                    onClick={() => handleToggleButton(block)}
                    disabled={togglingBlockId === block.id}
                  >
                    {togglingBlockId === block.id ? (
                      <div className="toggle-status-wrapper">
                        <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                        </svg> 
                        <span className="toggle-status-text">Đang xử lý...</span>
                      </div>
                    ) : (
                      <div className="toggle-status-wrapper">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          {normalizeValue(block.value) === 1 ? (
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                          ) : (
                            <circle cx="12" cy="12" r="10" opacity="0.3" />
                          )}
                        </svg>
                        <span className="toggle-status-text">
                          {normalizeValue(block.value) === 1 ? 'Đang bật' : 'Đang tắt'}
                        </span>
                      </div>
                    )}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Chart Blocks */}
        <div className="dashboard-section">
          <div className="section-header">
            <h3 className="section-title">Biểu đồ & Giám sát</h3>
            <button className="btn-add-block" onClick={() => handleAddBlock(1)}>
              <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M8 2v12M2 8h12" />
              </svg>
              Thêm biểu đồ
            </button>
          </div>

          <div className="blocks-grid">
            {chartBlocks.length === 0 ? (
              <div className="empty-state">
                <p>Chưa có biểu đồ nào</p>
                <button className="btn-secondary" onClick={() => handleAddBlock(1)}>
                  Thêm biểu đồ đầu tiên
                </button>
              </div>
            ) : (
              chartBlocks.map((block) => (
                <ChartBlock
                  key={block.id}
                  block={block}
                  onConfigure={() => handleConfigureBlock(block)}
                  onDelete={() => handleDeleteBlock(block)}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Config Modal */}
      {showConfigModal && (
        <BlockConfigModal
          block={selectedBlock}
          isNewBlock={isNewBlock}
          blockType={blockType}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedBlock(null);
          }}
          onSave={handleSaveConfig}
        />
      )}
    </div>
  );
};

export default Dashboard;