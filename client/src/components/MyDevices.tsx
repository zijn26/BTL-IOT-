import React, { useState, useEffect } from 'react';
import '../styles/MyDevices.css';
import DeviceConfigModal from './DeviceConfigModal';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Device {
  id: number;
  device_name: string;
  device_type: 'MASTER' | 'SLAVE' | 'GUEST';
  device_access_token?: string;
  device_token?: string; // Alternative field name
  connection_status?: string; // 'ONLINE' | 'OFFLINE'
  is_online?: boolean; // Deprecated, use connection_status
  is_active?: boolean; // Alternative field name
  last_seen?: string;
  last_seen_at?: string;
  created_at?: string;
  registered_at?: string;
}

interface MyDevicesProps {
  onClose: () => void;
}

const MyDevices: React.FC<MyDevicesProps> = ({ onClose }) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [registerName, setRegisterName] = useState('');
  const [registerType, setRegisterType] = useState<'MASTER' | 'SLAVE'>('MASTER');
  const [registerLoading, setRegisterLoading] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);
  
  // Config modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  
  // Info modal state
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [deviceInfo, setDeviceInfo] = useState<any>(null);
  const [infoLoading, setInfoLoading] = useState(false);
 
  // Load devices from API
  const loadDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Chưa đăng nhập');
        return;
      }

      const res = await fetch(`${API_BASE}/devices/getDevices`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || 'Không thể tải danh sách thiết bị');
        return;
      }

      // Map devices and normalize connection_status
      const normalizedDevices = (data.devices || []).map((device: any) => ({
        ...device,
        // Đảm bảo connection_status được set từ is_active nếu chưa có
        connection_status: device.connection_status || (device.is_active ? 'ONLINE' : 'OFFLINE'),
      }));
      setDevices(normalizedDevices);
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi tải danh sách thiết bị');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  // Register new device
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisterError(null);

    if (!registerName.trim()) {
      setRegisterError('Vui lòng nhập tên thiết bị');
      return;
    }

    setRegisterLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setRegisterError('Chưa đăng nhập');
        return;
      }

      const res = await fetch(`${API_BASE}/devices/registerDevide`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_name: registerName.trim(),
          device_type: registerType,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setRegisterError(data.message || 'Đăng ký thiết bị thất bại');
        return;
      }

      // Reset form and reload devices
      setRegisterName('');
      setRegisterType('MASTER');
      setShowRegisterForm(false);
      await loadDevices();
    } catch (err: any) {
      setRegisterError(err?.message || 'Lỗi khi đăng ký thiết bị');
    } finally {
      setRegisterLoading(false);
    }
  };

  // Delete device
  const handleDelete = async (deviceToken: string, deviceName: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa thiết bị "${deviceName}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Chưa đăng nhập');
        return;
      }

      const res = await fetch(`${API_BASE}/devices/deleteDevice?device_token=${deviceToken}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || 'Xóa thiết bị thất bại');
        return;
      }

      // Reload devices list after successful deletion
      await loadDevices();
      
      // Show success message
      alert(`Đã xóa thiết bị "${deviceName}" thành công`);
    } catch (err: any) {
      alert(err?.message || 'Lỗi khi xóa thiết bị');
    }
  };

  // Handle configure (virtual pin)
  const handleConfigure = (device: Device) => {
    setSelectedDevice(device);
    setShowConfigModal(true);
  };

  // Handle show info
  const handleShowInfo = async (device: Device) => {
    setInfoLoading(true);
    setShowInfoModal(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Chưa đăng nhập');
        setShowInfoModal(false);
        return;
      }

      const res = await fetch(`${API_BASE}/devices/getDevice?device_id=${device.id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || 'Không thể lấy thông tin thiết bị');
        setShowInfoModal(false);
        return;
      }

      // API trả về device là một mảng
      const deviceList = data.device;
      if (!deviceList || deviceList.length === 0) {
        alert('Không tìm thấy thông tin thiết bị');
        setShowInfoModal(false);
        return;
      }

      setDeviceInfo(deviceList[0]);
    } catch (err: any) {
      alert(err?.message || 'Lỗi khi lấy thông tin thiết bị');
      setShowInfoModal(false);
    } finally {
      setInfoLoading(false);
    }
  };

  // Copy token to clipboard
  const copyToken = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Đã copy token vào clipboard');
    }).catch(() => {
      alert('Không thể copy token');
    });
  };

  const getStatusText = (device: Device) => {
    // Ưu tiên sử dụng connection_status từ API
    if (device.connection_status) {
      return device.connection_status.toUpperCase();
    }
    // Fallback cho các trường cũ
    const isOnline = device.is_online ?? device.is_active ?? false;
    return isOnline ? 'ONLINE' : 'OFFLINE';
  };

  const getStatusClass = (device: Device) => {
    // Ưu tiên sử dụng connection_status từ API
    if (device.connection_status) {
      const status = device.connection_status.toUpperCase();
      return status === 'ONLINE' ? 'device-status-online' : 'device-status-offline';
    }
    // Fallback cho các trường cũ
    const isOnline = device.is_online ?? device.is_active ?? false;
    return isOnline ? 'device-status-online' : 'device-status-offline';
  };

  const getTypeClass = (type: string) => {
    return type === 'MASTER' ? 'device-type-master' : 'device-type-slave';
  };

  return (
    <div className="my-devices-container">
      <div className="my-devices-header">
        <div className="my-devices-header-left">
          <div className="header-icon-wrapper">
            <svg className="header-main-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
            </svg>
          </div>
          <div>
            <h1 className="my-devices-title">Thiết bị của tôi</h1>
            <p className="my-devices-subtitle">Quản lý tất cả thiết bị IoT của bạn</p>
          </div>
        </div>
        {!showRegisterForm && (
          <button
            className="btn-register-device"
            onClick={() => setShowRegisterForm(true)}
          >
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M8 2v12M2 8h12" />
            </svg>
            Đăng ký thiết bị mới
          </button>
        )}
      </div>

      {showRegisterForm ? (
        <div className="register-form-container">
          <div className="register-form-header">
            <div className="register-form-title-section">
              <div className="register-icon-wrapper">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
                </svg>
              </div>
              <div>
                <h3>Đăng ký thiết bị mới</h3>
                <p className="register-form-subtitle">Thêm thiết bị IoT mới vào hệ thống</p>
              </div>
            </div>
            <button className="register-close-btn" onClick={() => {
              setShowRegisterForm(false);
              setRegisterError(null);
              setRegisterName('');
            }}>
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 4L4 12M4 4l8 8" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleRegister} className="register-form">
            <div className="form-group">
              <label className="form-label">
                <span>Tên thiết bị</span>
                <span className="required-indicator">*</span>
              </label>
              <input
                className="form-input"
                type="text"
                value={registerName}
                onChange={(e) => setRegisterName(e.target.value)}
                placeholder="Ví dụ: Cảm biến nhiệt độ phòng khách"
                disabled={registerLoading}
              />
              <p className="form-hint">Nhập tên dễ nhận biết cho thiết bị của bạn</p>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Loại thiết bị</span>
                <span className="required-indicator">*</span>
              </label>
              <select
                value={registerType}
                onChange={(e) => setRegisterType(e.target.value as 'MASTER' | 'SLAVE')}
                className="form-input"
                disabled={registerLoading}
              >
                <option value="MASTER">MASTER - Thiết bị chủ</option>
                <option value="SLAVE">SLAVE - Thiết bị phụ</option>
              </select>
              <p className="form-hint">MASTER: Thiết bị điều khiển chính | SLAVE: Thiết bị cảm biến/chấp hành</p>
            </div>

            {registerError && (
              <div className="register-error-alert">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{registerError}</span>
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setShowRegisterForm(false);
                  setRegisterError(null);
                  setRegisterName('');
                }}
                disabled={registerLoading}
              >
                Hủy
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={registerLoading}
              >
                {registerLoading ? (
                  <>
                    <svg className="spinner" width="18" height="18" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" strokeDasharray="60" strokeDashoffset="30">
                        <animateTransform attributeName="transform" type="rotate" values="0 12 12;360 12 12" dur="1s" repeatCount="indefinite" />
                      </circle>
                    </svg>
                    Đang xử lý...
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M8 2v12M2 8h12" />
                    </svg>
                    Đăng ký thiết bị
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <>
          {loading ? (
            <div className="loading-container">
              <p>Đang tải...</p>
            </div>
          ) : error ? (
            <div className="error-container">
              <p>{error}</p>
              <button className="btn" onClick={loadDevices}>Thử lại</button>
            </div>
          ) : devices.length === 0 ? (
            <div className="empty-container">
              <p>Chưa có thiết bị nào. Hãy đăng ký thiết bị mới!</p>
            </div>
          ) : (
            <div className="devices-grid">
              {devices.map((device) => (
                <div key={device.id} className="device-card-new">
                  <div className="device-card-header">
                    <div className="device-icon-new">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
                      </svg>
                    </div>
                    <span className="device-name-new">{device.device_name}</span>
                  </div>
                  
                  <div className="device-badges">
                    <span className={`device-badge ${getTypeClass(device.device_type)}`}>
                      {device.device_type}
                    </span>
                    <span className={`device-badge ${getStatusClass(device)}`}>
                      {getStatusText(device)}
                    </span>
                  </div>

                  <div className="device-actions">
                    {device.device_type === 'SLAVE' && (
                      <button
                        className="device-action-btn"
                        onClick={() => handleConfigure(device)}
                        title="Cấu hình"
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="8" cy="8" r="2" />
                          <path d="M8 2v1.33M8 12.67V14M2 8h1.33M12.67 8H14M3.05 3.05l.94.94M11.01 11.01l.94.94M3.05 12.95l.94-.94M11.01 4.99l.94-.94" />
                        </svg>
                        Cấu hình
                      </button>
                    )}
                    <button
                      className="device-action-btn"
                      onClick={() => handleShowInfo(device)}
                      title="Thông tin"
                    >
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="8" cy="8" r="7" />
                        <path d="M8 12V8M8 4h.01" />
                      </svg>
                      Thông tin
                    </button>
                    <button
                      className="device-action-btn device-action-delete"
                      onClick={() => {
                        const token = device.device_token || null;
                        if (token) {
                          handleDelete(token, device.device_name);
                        }
                      }}
                      title="Xóa"
                    >
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 4h8v10a1 1 0 01-1 1H5a1 1 0 01-1-1V4zM6 2h4M2 4h12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {showConfigModal && selectedDevice && (
        <DeviceConfigModal
          device={{
            id: selectedDevice.id,
            device_name: selectedDevice.device_name,
            device_token: selectedDevice.device_token,
            device_access_token: selectedDevice.device_access_token,
          }}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedDevice(null);
          }}
        />
      )}

      {/* Info Modal */}
      {showInfoModal && (
        <div className="device-info-modal-overlay" onClick={() => {
          setShowInfoModal(false);
          setDeviceInfo(null);
        }}>
          <div className="device-info-modal" onClick={(e) => e.stopPropagation()}>
            <div className="device-info-modal-header">
              <h2>Thông tin thiết bị</h2>
              <button className="modal-close-btn" onClick={() => {
                setShowInfoModal(false);
                setDeviceInfo(null);
              }}>×</button>
            </div>

            <div className="device-info-modal-content">
              {infoLoading ? (
                <div className="loading-state">Đang tải...</div>
              ) : deviceInfo ? (
                <div className="device-info-list">
                  <div className="device-info-item">
                    <label>Tên thiết bị:</label>
                    <span>{deviceInfo.device_name}</span>
                  </div>
                  <div className="device-info-item">
                    <label>Loại thiết bị:</label>
                    <span className={`device-badge ${getTypeClass(deviceInfo.device_type)}`}>
                      {deviceInfo.device_type}
                    </span>
                  </div>
                  <div className="device-info-item">
                    <label>Trạng thái kết nối:</label>
                    <span className={`device-badge ${deviceInfo.connection_status === 'ONLINE' ? 'device-status-online' : 'device-status-offline'}`}>
                      {deviceInfo.connection_status || 'OFFLINE'}
                    </span>
                  </div>
                  <div className="device-info-item">
                    <label>Token Verify:</label>
                    <div className="token-container">
                      <input
                        type="text"
                        readOnly
                        value={deviceInfo.token_verify || 'N/A'}
                        className="token-input"
                      />
                      <button
                        className="copy-token-btn"
                        onClick={() => deviceInfo.token_verify && copyToken(deviceInfo.token_verify)}
                        title="Copy token"
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M6 2v-1a1 1 0 011-1h6a1 1 0 011 1v10a1 1 0 01-1 1h-1M6 2h5a1 1 0 011 1v10a1 1 0 01-1 1H6a1 1 0 01-1-1V3a1 1 0 011-1z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div className="device-info-item">
                    <label>Ngày đăng ký:</label>
                    <span>
                      {deviceInfo.registered_at
                        ? new Date(deviceInfo.registered_at).toLocaleString('vi-VN')
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="error-state">Không có thông tin</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyDevices;

