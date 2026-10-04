# Manual Test Plan: Authentication & Authorization

## 1. Scope & Objective

Kiểm thử thủ công 12 tình huống xác thực, quyền sở hữu todo và cô lập phiên;
hồi quy Tier 1 và DEF-MANUAL-01. Theo [template](templates/TEST_PLAN_TEMPLATE.md)
và [README §2C](README.md#2c-manual-test-plan), bảng giữ Preconditions, Steps,
Expected/Actual, Priority và Severity; Module được thể hiện bằng tiêu đề nhóm.

**Kết quả: 12 Pass / 0 Fail / 0 Blocked / 0 Not Run.**
11 case giữ kết quả manual trước; chỉ TC-AUTH-04 được retest sau sửa login.
Pytest/E2E được ghi riêng trong [completed.md](completed.md).

## 2. Test Environment & Prerequisites

| Hạng mục | Thiết lập |
|---|---|
| URL | Frontend `http://localhost:3000`; backend `http://localhost:8000`; Swagger `/docs`. Endpoint bên dưới dùng prefix `/api/v1`. |
| Stack | Docker Compose: frontend, backend, PostgreSQL, Redis. |
| Dữ liệu | Hai tài khoản test A/B tạo riêng; A có todo `X` với title/description duy nhất. Không lưu credential/token. |
| Phân quyền | Trước mỗi GET/PUT/DELETE chéo user: A GET X → 200, ghi baseline title/description/completed. Đổi Bearer phải gọi `/auth/me` xác nhận user. |
| Thực hiện | 04/10/2026: Codex thao tác UI/Swagger; người dùng bổ sung TC-AUTH-07 và TC-AUTHZ-01 bằng ảnh, xác nhận trong hội thoại. |
| Trình duyệt | Codex In-app Browser; Brave thường/riêng tư của người dùng. Chưa ghi phiên bản; hai tab cùng profile không phải phiên độc lập. |
| Retest | TC-AUTH-04 sau `docker compose up -d --build --no-deps backend`. |

Chờ API/list tải xong; đọc **Server response** trong Swagger.
TC-AUTH-01…03 kiểm tra UI và request Swagger riêng, không coi Swagger là capture
request UI. Expected status theo auth/todo handlers; login sai chung 401 theo
mục tiêu bảo mật của template.

## 3. Test Cases Matrix

Priority (P0/P1/P2: ưu tiên cao → thấp) và Severity (Critical/High/Medium/Low:
ảnh hưởng nếu lỗi) độc lập. Pass = khớp Expected; Fail = sai khác;
Blocked = đã bắt đầu nhưng chưa thể hoàn tất; Not Run = chưa chạy.

### Authentication

| TC ID | Scenario | Preconditions | Steps | Expected | Actual | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-AUTH-01 | Đăng ký mới | Email A chưa dùng. | Điền email, password và xác nhận tại `/register`; Create Account; chờ dashboard. Kiểm tra register trên Swagger. | 201; dashboard đúng A. | UI vào `/`, đúng A; đăng ký mới riêng trên Swagger trả 201 và token. | P0 / High | Pass |
| TC-AUTH-02 | Trùng email | A tồn tại; đã logout. | Đăng ký lại email A bằng UI và Swagger. | 400 `Email already registered`; UI báo lỗi, không tạo session mới. | UI báo đúng lỗi, không session mới; Swagger đúng 400/detail. | P1 / Medium | Pass |
| TC-AUTH-03 | Logout/login hợp lệ | A đang login; biết mật khẩu test. | Logout → Sign In bằng A; kiểm tra dashboard và login/logout trên Swagger. | Logout/login 200; dashboard đúng A. | UI về `/login`, login lại thấy A và todo cũ; Swagger login 200, logout 200 `Successfully logged out`. | P0 / High | Pass |
| TC-AUTH-04 | Login sai không lộ email | A tồn tại; email khác chưa đăng ký. | Gửi A + mật khẩu sai và email chưa tồn tại + cùng mật khẩu sai; so sánh status/body và thông báo UI. | Cùng 401 `Invalid email or password`; không token; UI hiện lỗi chung. | Swagger: hai lỗi cùng 401/body, login đúng 200. Sau sửa frontend và rebuild, manual UI cả hai hiện `Invalid email or password`, form giữ dữ liệu. | P1 / High | Pass |
| TC-AUTH-05 | JWT sai chữ ký | Access token A còn hạn; bản gốc gọi `/auth/me` 200. | Giữ header/payload; đổi ký tự đầu signature sang base64url khác. Authorize bản sửa → GET `/auth/me`; bỏ Bearer sai. | 401 `Invalid authentication token`; không dữ liệu user. | Bản gốc 200 đúng A; bản sửa 401 đúng detail, không dữ liệu user. | P0 / High | Pass |
| TC-AUTH-06 | Refresh dùng làm access | Refresh token A còn hạn. | Thay Bearer bằng refresh token → GET `/auth/me`; bỏ Bearer sau test. | 401 `Invalid authentication token`; không dữ liệu user. | Swagger đúng 401/detail, không dữ liệu user. | P0 / High | Pass |
| TC-AUTH-07 | Logout xóa token/cache UI | A có X; B tồn tại; DevTools Application/Network mở. | 1. Xác nhận email/X và hai key `access_token`, `refresh_token` trong Local Storage frontend.<br>2. Logout; kiểm tra key biến mất; Back/truy cập `/`.<br>3. Login A → logout → login B cùng tab, không F5/nhập URL/đóng tab; xem request mới và UI. | Hai key bị xóa; route về login, không dữ liệu A; `/auth/me`, `/todos` mới 200; đúng B, không X. | Codex thấy Back về login; người dùng xác nhận key bị xóa, chuyển phiên không F5. Ảnh: logout/login 200, `/me` và `/todos` mới 200; đúng B, không X. | P0 / High | Pass |

### Authorization

| TC ID | Scenario | Preconditions | Steps | Expected | Actual | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-AUTHZ-01 | List giữa hai phiên | A có X; B dùng cửa sổ riêng tư độc lập. | A xác nhận X; B login, chờ list 200; xem UI/response và các trang liên quan nếu có. | List B không chứa ID/title X; không yêu cầu list rỗng. | Codex xác nhận X của A; ảnh người dùng: phiên riêng tư đúng B, `items: [], total: 0`; xác nhận 200, không X. | P0 / Critical | Pass |
| TC-AUTHZ-02 | B không đọc được X | A GET X 200; Bearer B hợp lệ. | B GET `/todos/{X}`. | 404 `Todo not found`; không lộ nội dung. | Swagger đúng 404/detail, không dữ liệu X. | P0 / Critical | Pass |
| TC-AUTHZ-03 | B không sửa được X | X tồn tại; có baseline; Bearer B hợp lệ. | B PUT `/todos/{X}` với `{"title":"Unauthorized change"}`; A GET lại và xem UI. | PUT 404 `Todo not found`; A GET 200, dữ liệu không đổi. | Đúng 404/detail; A GET 200, title/description/completed giữ baseline; UI còn todo cũ. | P0 / Critical | Pass |
| TC-AUTHZ-04 | B không xóa được X | A GET X 200; Bearer B hợp lệ. | B DELETE `/todos/{X}`; A GET lại và reload UI. | DELETE 404 `Todo not found`; A GET 200, X còn tồn tại. | Đúng 404/detail; A GET 200, reload UI vẫn có X. | P0 / Critical | Pass |
| TC-AUTHZ-05 | Đổi A → B cùng tab | A login và thấy X; B tồn tại; Network mở. | Logout A → login B bằng form cùng tab, không F5/nhập URL; quan sát chuyển phiên và list tải xong. | Đúng B, không identity/todo A, không cần F5. | UI đúng B, `No todos yet`; Swagger list B 200, không X. | P0 / Critical | Pass |

## 4. Defect Tracking & Known Limitations

### DEF-MANUAL-01 — Login tiết lộ email tồn tại

TC-AUTH-04 · **P1 / High · Fixed / Retest Passed (04/10/2026)**

| Giai đoạn | Bằng chứng / thay đổi |
|---|---|
| Fail | Swagger: sai mật khẩu → 401 `Incorrect password`; email không tồn tại → 404 `User with this email not found`. UI chỉ quan sát được thông báo email không tồn tại. |
| Fix | `backend/app/api/v1/auth.py::login`: cả hai nhánh trả 401 `Invalid email or password`. |
| Retest | Swagger trên backend rebuild: login đúng 200; hai trường hợp sai cùng 401/body, không token. Giữ Expected ban đầu. |

Lỗi UI bổ sung: người dùng xác nhận login sai không có toast; interceptor 401
đã tải lại trang. Đã loại login/register khỏi luồng redirect phiên hết hạn.
Sau rebuild frontend, manual cả hai login sai hiện toast chung, giữ form.

Hồi quy logout: trước sửa có `/todos` 403; đã thêm điều kiện token và AbortSignal
cho query todo. E2E không ghi nhận request todo thiếu Authorization trong chuyển
trang. Ảnh Network manual người dùng gửi sau sửa chỉ có `logout` 200, không có
request `/todos` hoặc 403 trong khoảng log được chụp (Keep log bật).

### Known Limitations

- Chưa chạy lại toàn bộ 12 case manual trên image mới; TC-AUTH-04 đã retest API và UI.
- Cache được kiểm tra qua token cleanup và hành vi UI; chưa đo toàn bộ React Query cache trong RAM.
- Chưa đánh giá chênh lệch thời gian login hoặc dò email qua register (trùng email vẫn trả 400 theo contract).
- Dữ liệu test còn trong database phát triển; không reset database hoặc xóa dữ liệu có sẵn.
