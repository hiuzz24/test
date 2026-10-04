# Tiến độ bài đánh giá

## Đã hoàn thành

- Hồi quy frontend sau phản hồi manual:
  - Login/register 401 được trả về form xử lý; endpoint cần xác thực vẫn xóa
    phiên và redirect khi gặp 401.
  - Query todo chỉ chạy khi có access token; dùng AbortSignal để hủy request
    đang chạy khi clear cache, tránh request thiếu token sau logout.
  - Rebuild frontend Docker thành công; `npm run build` pass (Vite 2.89s), còn
    cảnh báo chunk lớn hơn 500 kB.
  - `npx playwright test`: **4 passed (27.5s)** trên Chromium headless, API thật.
    Thêm hai case login sai hiện toast/không reload; các bước logout xác nhận
    hai token bị xóa, không có request todo thiếu Authorization trong chuyển trang.
  - Manual UI sau rebuild: mật khẩu sai và email chưa tồn tại đều hiện
    `Invalid email or password`, form giữ dữ liệu. Đã cập nhật TC-AUTH-04.
  - Người dùng đã bổ sung ảnh Network manual sau sửa: Keep log bật, chỉ có
    `logout` 200; không có request `/todos` hoặc 403 trong khoảng log được chụp.
    Bằng chứng manual này được ghi riêng với kết quả E2E.

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
- Tier 2B — Playwright E2E:
  - Đã cài `@playwright/test`, cấu hình Chromium với một worker và thêm hai
    kịch bản trong `frontend/e2e/todos.spec.ts`.
  - Full User Journey: đăng ký, đăng xuất, đăng nhập, tạo todo, tick hoàn thành,
    tải lại để xác nhận trạng thái được lưu và đăng xuất.
  - Cross-User Data Isolation: A và B dùng hai BrowserContext độc lập; B đăng
    ký, đăng xuất rồi đăng nhập thật bằng form; sau khi API và UI danh sách tải
    xong, xác nhận todo riêng của A không xuất hiện trong phiên B.
  - Đã xác nhận bằng `docker compose ps`: frontend, backend, PostgreSQL và
    Redis đều đang chạy. Frontend cổng 3000 và backend `/health` cổng 8000 trả
    HTTP 200. Docker CLI được tìm thấy tại thư mục DockerDesktop của user;
    giai đoạn E2E sử dụng stack đang chạy, không build lại container.
  - Lệnh chạy từ `frontend`: `npx playwright test`.
  - Kết quả Chromium headless giai đoạn Tier 2B: **2 passed (18.0s)**, exit code 0;
    Full User Journey 7.2s và Cross-User Data Isolation 7.4s. Không mock API.
  - Lần chạy đầu: hành trình người dùng pass, bài hai context lỗi cấu hình
    trace trùng lặp; đã sửa cấu hình và chạy lại toàn bộ suite thành công.
  - Một lần chạy thủ công sau đó phát hiện `locator.check()` kiểm tra trạng thái
    quá sớm với Radix checkbox cập nhật bất đồng bộ. Đã đổi sang `click()`, chờ
    PUT và GET hoàn tất rồi mới assert; toàn bộ suite đã pass lại.
  - `npm run build` thành công (1.12s); `npx tsc -b` và
    `npx eslint playwright.config.ts e2e/*.ts` đã chạy thành công.
  - Lệnh headed đã được hướng dẫn nhưng chưa chạy: `npx playwright test --headed`.
  - Hướng dẫn cài đặt/chạy tại `frontend/e2e/README.md`. Artifacts bị loại khỏi
    Git và Docker context; thông tin tài khoản được sinh lúc chạy, không lưu
    credential hoặc storage state trong repository.
  - Dữ liệu test còn trong database phát triển; không xóa dữ liệu có sẵn.
- Tài liệu Tier 2C: đã tạo `TEST_PLAN.md` tại root theo template, đúng 12 case,
  có Preconditions, Steps, Expected/Actual, Priority, Severity và Status.
  - Đã thao tác trực tiếp trên UI frontend và Swagger với hai user cùng một todo
    riêng của A; không dùng pytest hoặc Playwright làm bằng chứng manual.
  - Kết quả trước bản sửa login: **11 Pass / 1 Fail / 0 Blocked / 0 Not Run**.
  - Fail: TC-AUTH-04 xác nhận user enumeration — mật khẩu sai trả 401
    `Incorrect password`, còn email chưa tồn tại trả 404
    `User with this email not found`; đã ghi `DEF-MANUAL-01`.
  - Người dùng bổ sung ảnh và xác nhận manual: hai key token biến mất sau logout,
    chuyển A → B không F5, list B trong cửa sổ riêng tư trả 200 và không chứa
    todo A. TC-AUTH-07 và TC-AUTHZ-01 chuyển thành Pass.
  - Đã sửa DEF-MANUAL-01: hai nhánh login sai cùng trả 401 và
    `Invalid email or password`. TC-AUTH-04 retest trực tiếp trên Swagger sau
    rebuild backend: login đúng 200, hai trường hợp sai cùng 401/body giống nhau.
  - Kết quả tổng hợp mới nhất: **12 Pass / 0 Fail / 0 Blocked / 0 Not Run**;
    11 case giữ kết quả trước, chỉ TC-AUTH-04 được manual retest trên image mới.
  - TEST_PLAN.md đã được trình bày theo bốn mục của template, tách Module /
    Feature và Test Scenario; giữ Actual Result, Priority/Severity độc lập và
    lịch sử Fail → Fixed / Retest Passed.
  - Kiểm tra hồi quy sau sửa: từ backend chạy
    `.venv\Scripts\python.exe -m pytest tests/ -v`: **22 passed, 2 warnings
    in 8.15s** (hai cảnh báo deprecation cũ).
  - Rebuild riêng backend thành công: `docker compose up -d --build --no-deps backend`.
  - Từ frontend chạy `npx playwright test`: **2 passed (15.7s)** trên Chromium
    headless với stack Docker mới. Kết quả tự động tách riêng bằng chứng manual.
  - Ảnh Network trước sửa ghi nhận /todos 403 sau logout; kết quả sửa và
    kiểm chứng E2E bổ sung nằm ở mục hồi quy frontend đầu tài liệu.
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
  - `test(e2e): cover user journey and data isolation`
  - `test(e2e): handle async checkbox state update`
  - `test(manual): add authentication and authorization test plan`
  - `test(manual): record authentication test results`

## Chưa hoàn thành

- Đặc tả Todo Sharing.
- Các cải tiến Docker thuộc Tier 3 ngoài phần loại trừ local build artifacts.
- Benchmark database và bổ sung index.
- Mô tả Pull Request và công bố việc sử dụng AI.
- Các hạng mục tùy chọn thuộc Tier 4.
