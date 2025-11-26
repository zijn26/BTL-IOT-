import React, { useState, useEffect } from 'react';
import '../../styles/BlockConfigModal.css';
import { DashboardBlock } from './Dashboard';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface BlockConfigModalProps {
  block: DashboardBlock | null;
  isNewBlock: boolean;
  blockType: number; // 0: nút, 1: biểu đồ
  onClose: () => void;
  onSave: () => void;
}

interface Device {
  id: number;
  device_name: string;
  device_token: string; // UUID format - dùng để gọi API getConfigPin
  token_verify: string; // Hash format - dùng để lưu vào block config
}

interface Pin {
  virtual_pin: number;
  pin_label: string;
  pin_type: string; // INPUT or OUTPUT
  data_type?: string;
}

const BlockConfigModal: React.FC<BlockConfigModalProps> = ({
  block,
  isNewBlock,
  blockType,
  onClose,
  onSave,
}) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [pins, setPins] = useState<Pin[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [formData, setFormData] = useState({
    id: block?.id || -1,
    device_name: block?.device_name || '',
    token_verify: block?.token_verify || '',
    pin_label: block?.pin_label || '',
    virtual_pin: block?.virtual_pin || 0,
    label_block: block?.label_block || '',
    type_block: isNewBlock ? blockType : (block?.typeblock || 0),
  });
  
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load devices
  const loadDevices = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Chưa đăng nhập');
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
        throw new Error(data.message || 'Không thể tải danh sách thiết bị');
      }

      return data.devices || [];
    } catch (err: any) {
      console.error('Error loading devices:', err);
      return [];
    }
  };

  // Load pins for selected device
  const loadPins = async (deviceToken: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Chưa đăng nhập');
      }

      const res = await fetch(`${API_BASE}/devices/getConfigPin?device_token=${deviceToken}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Không thể tải danh sách pins');
      }

      // Trả về tất cả pins, sẽ filter theo type_block sau
      return data.config_pins || [];
    } catch (err: any) {
      console.error('Error loading pins:', err);
      return [];
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const deviceList = await loadDevices();
      setDevices(deviceList);
      
      // If editing existing block, load pins
      if (!isNewBlock && block?.token_verify) {
        // Tìm device từ token_verify để lấy device_token
        const device = deviceList.find((d: Device) => d.token_verify === block.token_verify);
        if (device) {
          const allPins = await loadPins(device.device_token);
          
          // Filter pins theo loại block
          const filteredPins = allPins.filter((pin: Pin) => 
            block.typeblock === 0 
              ? pin.pin_type === 'OUTPUT'
              : pin.pin_type === 'INPUT'
          );
          
          setPins(filteredPins);
        }
      }
      
      setLoading(false);
    };
    
    init();
  }, []);

  // Handle device change
  const handleDeviceChange = async (deviceName: string) => {
    const device = devices.find(d => d.device_name === deviceName);
    if (!device) return;
    
    setFormData(prev => ({
      ...prev,
      device_name: device.device_name,
      token_verify: device.token_verify,
      virtual_pin: 0,
      pin_label: '',
    }));
    
    // Load pins for this device - dùng device_token (UUID) thay vì token_verify
    const allPins = await loadPins(device.device_token);
    
    // Filter pins theo loại block:
    // - Button (type_block === 0): chỉ lấy OUTPUT pins
    // - Chart (type_block === 1): chỉ lấy INPUT pins
    const filteredPins = allPins.filter((pin: Pin) => 
      formData.type_block === 0 
        ? pin.pin_type === 'OUTPUT'  // Nút điều khiển: OUTPUT
        : pin.pin_type === 'INPUT'   // Biểu đồ: INPUT
    );
    
    setPins(filteredPins);
  };

  // Handle pin change
  const handlePinChange = (virtualPin: number) => {
    const pin = pins.find(p => p.virtual_pin === virtualPin);
    if (!pin) return;
    
    setFormData(prev => ({
      ...prev,
      virtual_pin: pin.virtual_pin,
      pin_label: pin.pin_label,
    }));
  };

  // Handle submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!formData.device_name) {
      setError('Vui lòng chọn thiết bị');
      return;
    }
    
    if (!formData.label_block.trim()) {
      setError('Vui lòng nhập tên block');
      return;
    }
    
    if (!formData.token_verify) {
      setError('Token thiết bị không hợp lệ');
      return;
    }
    
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Chưa đăng nhập');
        return;
      }

      const res = await fetch(`${API_BASE}/dashborad/block`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || 'Lưu cấu hình thất bại');
        return;
      }

      onSave();
    } catch (err: any) {
      setError(err?.message || 'Lỗi khi lưu cấu hình');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="block-config-modal-overlay" onClick={onClose}>
      <div className="block-config-modal" onClick={(e) => e.stopPropagation()}>
        <div className="block-config-modal-header">
          <h2>{isNewBlock ? 'Thêm block mới' : 'Cấu hình block'}</h2>
          <button className="modal-close-btn" onClick={onClose}>×</button>
        </div>

        <div className="block-config-modal-content">
          {loading ? (
            <div className="loading-state">Đang tải...</div>
          ) : (
            <form onSubmit={handleSubmit} className="block-config-form">
              <div className="form-group">
                <label className="form-label">
                  <span>Loại block</span>
                </label>
                <div className="block-type-display">
                  {formData.type_block === 0 ? 'Nút bật/tắt' : 'Biểu đồ'}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span>Tên block</span>
                  <span className="required-indicator">*</span>
                </label>
                <input
                  className="form-input"
                  type="text"
                  value={formData.label_block}
                  onChange={(e) => setFormData(prev => ({ ...prev, label_block: e.target.value }))}
                  placeholder="Ví dụ: Bật đèn phòng khách"
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span>Chọn thiết bị</span>
                  <span className="required-indicator">*</span>
                </label>
                <select
                  className="form-input"
                  value={formData.device_name}
                  onChange={(e) => handleDeviceChange(e.target.value)}
                  disabled={saving}
                >
                  <option value="">-- Chọn thiết bị --</option>
                  {devices.map((device) => (
                    <option key={device.id} value={device.device_name}>
                      {device.device_name}
                    </option>
                  ))}
                </select>
              </div>

              {formData.device_name && pins.length > 0 && (
                <div className="form-group">
                  <label className="form-label">
                    <span>{formData.type_block === 0 ? 'Chọn pin điều khiển (OUTPUT)' : 'Chọn chân cảm biến (INPUT)'}</span>
                    <span className="required-indicator">*</span>
                  </label>
                  <select
                    className="form-input"
                    value={formData.virtual_pin}
                    onChange={(e) => handlePinChange(Number(e.target.value))}
                    disabled={saving}
                  >
                    <option value={0}>
                      {formData.type_block === 0 ? '-- Chọn pin OUTPUT --' : '-- Chọn pin INPUT --'}
                    </option>
                    {pins.map((pin) => (
                      <option key={pin.virtual_pin} value={pin.virtual_pin}>
                        Pin {pin.virtual_pin} - {pin.pin_label} ({pin.pin_type})
                      </option>
                    ))}
                  </select>
                  {formData.type_block === 0 ? (
                    <p className="form-hint">Chọn chân OUTPUT để điều khiển thiết bị (đèn, motor, relay...)</p>
                  ) : (
                    <p className="form-hint">Chọn chân INPUT để đọc dữ liệu từ cảm biến. Tạo nhiều biểu đồ để hiển thị nhiều loại dữ liệu.</p>
                  )}
                </div>
              )}

              {formData.device_name && pins.length === 0 && (
                <div className="form-hint">
                  {formData.type_block === 0 
                    ? 'Thiết bị này chưa có pin OUTPUT nào. Vui lòng cấu hình pin OUTPUT trong "Thiết bị của tôi".'
                    : 'Thiết bị này chưa có pin INPUT nào. Vui lòng cấu hình pin INPUT trong "Thiết bị của tôi".'
                  }
                </div>
              )}

              {error && (
                <div className="error-alert">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={onClose}
                  disabled={saving}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={
                    saving || 
                    !formData.device_name || 
                    !formData.label_block ||
                    !formData.virtual_pin
                  }
                >
                  {saving ? 'Đang lưu...' : (isNewBlock ? 'Thêm block' : 'Lưu thay đổi')}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default BlockConfigModal;

