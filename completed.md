# Tiến độ bài đánh giá

## Đã hoàn thành

- Báo cáo lỗi: đã ghi nhận 8 lỗi quan trọng trong `BUG_REPORT.md` theo đúng cấu
  trúc Location, Severity, Reason và Fix Proposal được yêu cầu.
- Sửa lỗi Tier 1: đã sửa toàn bộ 8 lỗi được báo cáo:
  - Kiểm tra thời hạn, chữ ký và loại access/refresh của JWT.
  - Kiểm tra quyền sở hữu todo đối với các thao tác GET, PUT và DELETE.
  - Cập nhật một phần giữ nguyên các trường không được gửi và lưu đúng giá trị
    `completed=false`.
  - Redis cache key được phân tách theo người dùng và phân trang; cache được vô
    hiệu hóa sau các thao tác thay đổi dữ liệu bằng `SCAN`.
  - Frontend xóa token và React Query cache khi đăng nhập, đăng ký, đăng xuất
    hoặc nhận HTTP 401 để dữ liệu không bị giữ lại giữa các phiên người dùng.
- Các nhóm pytest backend Tier 2A:
  - Từ chối JWT không hợp lệ.
  - Kiểm tra ranh giới phân quyền.
  - Chuyển đổi giá trị boolean.
  - Cập nhật một phần.
  - Hành vi cache và quá trình vô hiệu hóa cache.
- Kiểm tra backend:
  - Lệnh chạy từ thư mục `backend`:
    `.venv\Scripts\python.exe -m pytest tests\ -v`.
  - Kết quả: **20 bài kiểm thử thành công, 2 cảnh báo trong 6.74 giây**.
  - Cảnh báo: cấu hình `Config` dạng class của Pydantic và fixture `event_loop`
    tùy chỉnh của pytest-asyncio đều đã bị đánh dấu là sắp ngừng hỗ trợ.
- Kiểm tra frontend:
  - Lệnh chạy từ thư mục `frontend`: `npm run build`.
  - Kết quả: **thành công** (`vite v8.0.16`, 2.075 module được xử lý, hoàn
    thành trong 616ms).
  - Vite đưa ra một cảnh báo không làm build thất bại: một file chunk sau khi
    rút gọn có kích thước lớn hơn 500 kB.
- Docker build context:
  - Đã thêm `.dockerignore` cho backend để loại `.pytest_cache`, `.venv`, Python
    bytecode, coverage output, database test và file môi trường khỏi build
    context.
  - Đã thêm `.dockerignore` cho frontend để loại `node_modules`, `dist`, log npm
    và file môi trường khỏi build context.
  - Chưa xác nhận lại bằng `docker compose build` trong terminal Codex vì môi
    trường này không tìm thấy Docker CLI; cần chạy lại bằng terminal có Docker.
- Danh sách commit:
  - `docs: add assessment bug findings`
  - `fix(auth): enforce token expiration and type`
  - `fix(todos): enforce todo ownership`
  - `fix(todos): preserve partial update fields`
  - `fix(cache): scope and invalidate todo list cache`
  - `fix(frontend): clear cached state on auth changes`
  - `test(backend): cover critical regression scenarios`
  - `docs: add assessment progress summary`
  - `docs: translate assessment progress summary`
  - `build(docker): exclude local artifacts from build context`

## Chưa hoàn thành

- Kiểm tra thủ công trên trình duyệt sau khi sửa bằng hai tài khoản người dùng.
- Kiểm thử E2E bằng Playwright.
- Kế hoạch kiểm thử thủ công.
- Đặc tả Todo Sharing.
- Các cải tiến Docker thuộc Tier 3 ngoài phần loại trừ local build artifacts.
- Benchmark database và bổ sung index.
- Mô tả Pull Request và công bố việc sử dụng AI.
- Các hạng mục tùy chọn thuộc Tier 4.
