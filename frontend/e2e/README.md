# Kiểm thử E2E — Tier 2B

Suite dùng Chromium của Playwright để thao tác qua UI trên frontend, backend,
PostgreSQL và Redis thật đang chạy bằng Docker Compose. Không mock API.

## Chuẩn bị và chạy

Cần Node.js/npm tương thích với frontend và Docker Desktop đang hoạt động.
Từ repository root, khởi động ứng dụng:

```powershell
docker compose up -d --build
docker compose ps
```

Chờ frontend tại http://localhost:3000 và backend tại
http://localhost:8000/health trả thành công. Nếu backend chưa khởi động được,
kiểm tra `docker compose logs backend` trước khi chạy test.

```powershell
cd frontend
npm ci
npx playwright install chromium
npx playwright test
```

Chạy có cửa sổ để xem thao tác tự động:

```powershell
npx playwright test --headed
```

Các lệnh tương đương: `npm run test:e2e` và `npm run test:e2e:headed`.
Xem báo cáo bằng `npx playwright show-report`.
Chromium được cài riêng; không cần thay đổi trình duyệt Brave đang sử dụng.

Nếu frontend chạy ở địa chỉ khác, đặt `E2E_BASE_URL` trước khi chạy; frontend
vẫn phải được cấu hình để gọi đúng backend của môi trường đó:

```powershell
$env:E2E_BASE_URL = 'http://localhost:3000'
npx playwright test
```

## Các kịch bản

1. Full User Journey: đăng ký, đăng xuất, đăng nhập, tạo todo có mô tả, tick hoàn
   thành, tải lại để kiểm tra trạng thái được lưu, rồi đăng xuất.
2. Cross-User Data Isolation: hai BrowserContext độc lập; A tạo todo riêng;
   B đăng ký, đăng xuất rồi đăng nhập bằng form; sau khi API và UI danh sách tải
   xong, kiểm tra todo của A không xuất hiện trong phiên B. Không giả định danh
   sách của B phải rỗng.

Test dùng role/label của UI và chờ response đúng endpoint, method, status cùng
trạng thái render. Không dùng thời gian chờ cố định. Dữ liệu tài khoản và todo
được sinh riêng ở mỗi lần chạy. Test không xóa database; các tài khoản và todo
đã tạo sẽ còn lại trong database phát triển sau khi chạy.

## Kết quả và artifacts

Chỉ `2 passed` với exit code 0 mới xác nhận suite chạy thành công. Lệnh
`--list` chỉ liệt kê test, không chứng minh hành vi ứng dụng.

Trace, screenshot và video được giữ khi thất bại. Kịch bản hai context lưu
artifacts riêng cho từng user trong `test-results/`. Báo cáo HTML nằm trong
`playwright-report/`. Các thư mục này được loại khỏi Git và Docker context.
Artifacts có thể chứa dữ liệu phiên chạy; chỉ dùng cục bộ, không commit hoặc
đưa lên PR. Suite không lưu file credential hay storage state.
