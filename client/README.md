# MODULE CLIENT - IoT Dashboard Frontend

> 📘 *Giao diện người dùng cho hệ thống quản lý và giám sát thiết bị IoT*

---

## 🎯 MỤC TIÊU

Client (Frontend) chịu trách nhiệm:
- **Hiển thị giao diện** quản lý thiết bị IoT 
- **Dashboard tương tác** để điều khiển thiết bị và xem biểu đồ realtime
- **Quản lý thiết bị** (thêm, xóa, cấu hình pin)
- **Xác thực người dùng** (đăng nhập/đăng xuất)
- **Giao tiếp với Backend API** để thực hiện các chức năng CRUD
- **Gửi lệnh điều khiển** thiết bị qua MQTT

---

## ⚙️ CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ | Phiên bản |
|------------|-----------|-----------|
| **Framework** | React | 18.x |
| **Ngôn ngữ** | TypeScript | 4.x |
| **Build Tool** | Create React App (CRA) | 5.x |
| **Styling** | CSS3 (Custom) | - |
| **HTTP Client** | Fetch API (Native) | - |
| **State Management** | React Hooks (useState, useEffect) | - |
| **Charts** | Custom SVG Charts | - |


---

## 🚀 HƯỚNG DẪN CHẠY

### Yêu cầu hệ thống

Trước khi bắt đầu, đảm bảo bạn đã cài đặt:

- **Node.js** (>= 16.x) - [Download](https://nodejs.org/)
- **npm** 
- **Git** (để clone repository)

Kiểm tra phiên bản:
```bash
node -v    # Ví dụ: v16.20.0
npm -v     # Ví dụ: 8.19.4
```

### Cài đặt

**Bước 1:** Clone repository (nếu chưa có)
```bash
git clone <URL_REPO>
cd <repo-folder>/source/client
```

**Bước 2:** Cài đặt dependencies
```bash
npm install
```

Quá trình cài đặt sẽ tải về tất cả các package cần thiết (React, TypeScript, v.v.)

### Chạy môi trường Development

```bash
npm start
```

**Kết quả:**
- Ứng dụng sẽ tự động mở tại: `http://localhost:3000`
- Hot reload được bật (tự động refresh khi code thay đổi)

### Build cho Production

Để tạo bản build tối ưu cho production:

```bash
npm run build
```

**Kết quả:**
- Thư mục `build/` chứa các file tĩnh đã được minify và optimize
- Ready để deploy lên hosting (Vercel, Netlify, etc.)

**Xem thử bản build:**
```bash
# Cài serve (chỉ cần 1 lần)
npm install -g serve

# Chạy bản build
serve -s build -l 3000
```

### Cấu hình Backend API

Frontend kết nối với Backend qua biến môi trường:

**Tạo file `.env` trong thư mục `source/client`:**
```env
REACT_APP_API_URL=http://localhost:8000
```

**Hoặc thay đổi trực tiếp trong code:**
```typescript
// Trong các component, mặc định:
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

---

## 📦 CẤU TRÚC THỨ MỤC

```
client/
├── README.md                          # Tài liệu này
├── package.json                       # Dependencies và scripts
├── tsconfig.json                      # TypeScript config
├── public/
│   ├── index.html                    # HTML template
│   └── favicon.ico
├── src/
│   ├── index.tsx                     # Entry point
│   ├── components/
│   │   ├── App.tsx                  # Main app component
│   │   ├── Header.tsx               # Navigation header
│   │   ├── Login.tsx                # Login form
│   │   ├── MyDevices.tsx            # Device management
│   │   ├── DeviceConfigModal.tsx    # Pin configuration modal
│   │   └── dashboard/
│   │       ├── Dashboard.tsx        # Main dashboard
│   │       ├── BlockConfigModal.tsx # Block configuration
│   │       └── ChartBlock.tsx       # Chart visualization
│   └── styles/
│       ├── App.css                  # Global styles
│       ├── Dashboard.css            # Dashboard dark theme
│       ├── MyDevices.css            # Device page styles
│       ├── BlockConfigModal.css     # Modal styles
│       └── DeviceConfigModal.css    # Device modal styles
└── build/                            # Production build (sau khi build)
```

---

## 💡 SỬ DỤNG

### Đăng nhập

1. Mở `http://localhost:3000`
2. Nhập **username** và **password**
3. Hệ thống lưu JWT token vào localStorage
4. Tự động chuyển đến Dashboard

### Quản lý thiết bị (MyDevices)

```
Chức năng:
- Xem danh sách thiết bị (MASTER/SLAVE)
- Đăng ký thiết bị mới
- Cấu hình Virtual Pin cho thiết bị
- Xem thông tin chi tiết (Token, Status)
- Xóa thiết bị
```

**Đăng ký thiết bị mới:**
- Click "Đăng ký thiết bị mới"
- Nhập tên thiết bị
- Chọn loại: MASTER hoặc SLAVE
- Submit → API tạo thiết bị và trả về token

**Cấu hình Pin:**
- Click "Cấu hình" trên thiết bị SLAVE
- Thêm Virtual Pin (1-30)
- Chọn loại: INPUT (sensor) hoặc OUTPUT (actuator)
- Nhập AI Keywords (cho OUTPUT)

### Dashboard

```
Chức năng:
- Điều khiển thiết bị (Button blocks)
- Xem biểu đồ sensor realtime (Chart blocks)
- Thêm/Xóa/Cấu hình blocks
```

**Thêm nút điều khiển:**
- Click "Thêm nút"
- Chọn thiết bị và pin OUTPUT
- Nút hiển thị trạng thái: "Đang bật" / "Đang tắt"
- Click để bật/tắt thiết bị

**Thêm biểu đồ:**
- Click "Thêm biểu đồ"
- Chọn thiết bị và pin INPUT
- Biểu đồ tự động cập nhật mỗi 5 giây
- Hiển thị 10 điểm dữ liệu gần nhất

---

## 🔧 API ENDPOINTS SỬ DỤNG

Frontend gọi các API sau từ Backend:

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/auth/login` | POST | Đăng nhập |
| `/devices/getDevices` | GET | Lấy danh sách thiết bị |
| `/devices/registerDevide` | POST | Đăng ký thiết bị mới |
| `/devices/deleteDevice` | DELETE | Xóa thiết bị |
| `/devices/getConfigPin` | GET | Lấy cấu hình pin |
| `/devices/configPin` | POST | Cấu hình pin |
| `/dashborad/blocks` | GET | Lấy danh sách blocks |
| `/dashborad/block` | POST | Tạo/Update block |
| `/dashborad/block` | DELETE | Xóa block |
| `/mqtt/device-command` | POST | Gửi lệnh điều khiển |
| `/sensors/sensor-data` | GET | Lấy dữ liệu sensor |

---


## 📝 GHI CHÚ QUAN TRỌNG

### Trước khi chạy Frontend:

1. **Backend phải chạy trước** (port 8000)
   - Xem `source/server/README.md` để biết cách chạy backend
   
2. **Database phải được khởi tạo**
   - Backend cần connect được đến DB
   
3. **MQTT Broker phải online**
   - Để gửi lệnh điều khiển thiết bị
