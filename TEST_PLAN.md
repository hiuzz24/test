# Manual Test Plan: Authentication & Authorization Regression

## 1. Scope & Objective

- Mục tiêu: kiểm thử thủ công xác thực, quyền sở hữu todo và cô lập phiên người dùng.
- Phạm vi: đúng 12 case Authentication/Authorization đã thống nhất; hồi quy Tier 1 và DEF-MANUAL-01.
- Cấu trúc theo [TEST_PLAN_TEMPLATE.md](templates/TEST_PLAN_TEMPLATE.md): giữ bốn mục và các cột của template; bổ sung Actual Result theo yêu cầu bài đánh giá.
- Pass: Actual khớp Expected; Fail: có sai khác; Blocked: đã bắt đầu nhưng không đủ điều kiện hoàn tất; Not Run: chưa thực hiện.
- Priority và Severity được đánh giá độc lập dù hiển thị cùng cột: P0/P1/P2 là mức ưu tiên; Critical/High/Medium/Low là mức ảnh hưởng nếu hành vi sai.
- Tài liệu hoàn thành khi đủ nội dung; thực thi hoàn thành khi không còn Blocked/Not Run; kiểm thử đạt khi tất cả case Pass.

## 2. Test Environment & Prerequisites

- Base URL Backend: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`.
- Base URL Frontend: `http://localhost:3000`.
- Stack: Docker Compose với backend, frontend, PostgreSQL và Redis.
- Tài khoản: A/B được tạo riêng lúc manual, không giả định các tài khoản mẫu trong template đã seed. Không lưu mật khẩu/token trong tài liệu.
- A có một todo riêng với title/description duy nhất; ghi baseline trước các phép thử GET/PUT/DELETE chéo user. Chỉ dùng dữ liệu test.
- Trình duyệt: Codex In-app Browser; người dùng bổ sung Brave thường/riêng tư. Chưa ghi phiên bản.
- Ngày kiểm thử: 04/10/2026. Lượt đầu chạy 12 case, người dùng bổ sung hai case về storage và phiên riêng tư; lượt retest chỉ chạy lại TC-AUTH-04 trên backend vừa rebuild bằng `docker compose up -d --build --no-deps backend`.
- Người thực hiện: Codex thao tác trực tiếp UI/Swagger; người dùng kiểm tra bổ sung TC-AUTH-07 và TC-AUTHZ-01, cung cấp ảnh và xác nhận trong hội thoại.
- Expected status: register 201, duplicate 400 theo `auth.py::register`; login/logout 200 theo handlers; login sai chung 401 theo mục tiêu bảo mật của template và bản sửa `auth.py::login`; token sai 401 theo `deps.py::get_current_user`; todo khác chủ 404 theo handlers và owner-filtered lookup.
- Với HTTP status ở TC-AUTH-01…03, kiểm tra UI và thực thi request tương ứng riêng trên Swagger; không coi response Swagger là bản capture request UI.
- Chờ list/API hoàn tất trước kết luận không có dữ liệu. Trong Swagger đọc **Server response**, không đọc Example Value làm Actual.
- Khi đổi Bearer A/B, gọi `/auth/me` xác nhận danh tính. Không đưa token vào ảnh/tài liệu/commit.
- Kiểm tra phiên độc lập bằng cửa sổ thường và riêng tư; không coi hai tab cùng profile là hai phiên độc lập.

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Actual Result | Priority / Severity | Status (Pass/Fail/Blocked/Not Run) |
|---|---|---|---|---|---|---|---|---|
| TC-AUTH-01 | Authentication | Đăng ký tài khoản mới | Email A chưa dùng; frontend và API sẵn sàng; Network mở. | 1. Mở `/register`.<br>2. Điền email A, mật khẩu test và Confirm Password.<br>3. Bấm Create Account.<br>4. Xem POST `/api/v1/auth/register`, chờ dashboard tải. | POST 201; vào `/`; dashboard hiển thị đúng email A. | Đăng ký A trên UI thành công, tự vào `/` và hiển thị đúng email A. Một đăng ký mới riêng trên Swagger trả 201 và token response. | P0 / High | Pass |
| TC-AUTH-02 | Authentication | Đăng ký trùng email | A đã đăng ký; dùng phiên đã logout. | 1. Mở `/register`.<br>2. Điền lại email A, mật khẩu test hợp lệ và xác nhận.<br>3. Bấm Create Account.<br>4. Đọc status/detail trong Network và lỗi UI. | HTTP 400, detail `Email already registered`; UI báo lỗi, không tạo session mới. | UI hiển thị `Email already registered`; lặp request trùng email trên Swagger trả 400 cùng detail và không tạo session UI mới. | P1 / Medium | Pass |
| TC-AUTH-03 | Authentication | Logout và login đúng mật khẩu | A đang login; biết mật khẩu test; Network mở. | 1. Bấm Logout và đọc POST `/auth/logout`.<br>2. Trên `/login`, nhập đúng email/mật khẩu A và bấm Sign In.<br>3. Đọc POST `/auth/login`; chờ `/auth/me` và dashboard. | Logout 200; login 200; dashboard đúng email A. | UI logout về `/login`, login lại đúng mật khẩu và dashboard hiển thị A cùng todo cũ. Swagger xác nhận login 200 và logout 200 `Successfully logged out`. | P0 / High | Pass |
| TC-AUTH-04 | Authentication | Chống user enumeration khi login sai | A tồn tại; chuẩn bị email chưa đăng ký có run-id mới; hai request cùng một mật khẩu sai. | 1. Ở `/login`, gửi email A + mật khẩu sai; ghi status/detail.<br>2. Gửi email chưa tồn tại + cùng mật khẩu sai; ghi status/detail.<br>3. So sánh cả response và thông báo UI; nếu toast mất do redirect 401, đọc response trong Network. | Cả hai HTTP 401, cùng lỗi chung `Invalid email or password`; không tiết lộ email tồn tại. | Lần đầu: Fail, hai response khác status/detail. Retest 04/10/2026 trên Swagger sau rebuild backend: A login đúng 200; A + mật khẩu sai và email mới không tồn tại + cùng mật khẩu sai đều 401, body `{"detail":"Invalid email or password"}`. Không trả token. UI toast sau sửa chưa kiểm tra lại. | P1 / High | Pass |
| TC-AUTH-05 | Authentication | Access token sai chữ ký | Access token A còn hạn; Swagger đã xác nhận `/auth/me` 200 với bản gốc. | 1. Tạo bản sao token tạm, giữ nguyên header/payload và hai dấu chấm.<br>2. Đổi ký tự đầu của phần chữ ký sang ký tự base64url khác (A thành B, khác A thì thành A); không chỉ đổi ký tự cuối.<br>3. Authorize bản sửa.<br>4. Execute GET `/api/v1/auth/me`; đọc Server response.<br>5. Bỏ authorization sai sau test. | HTTP 401, `Invalid authentication token`; không trả dữ liệu người dùng. | Token gốc gọi `/auth/me` trả 200 đúng A; sửa ký tự đầu phần signature rồi gọi lại trả 401 `Invalid authentication token`, không có dữ liệu user. | P0 / High | Pass |
| TC-AUTH-06 | Authentication | Refresh token dùng như access | Có refresh token A còn hạn từ đăng nhập; Swagger dùng đúng HTTPBearer. | 1. Bỏ Bearer cũ trong Swagger.<br>2. Authorize bằng refresh token.<br>3. Execute GET `/api/v1/auth/me`.<br>4. Đọc Server response và bỏ authorization sau test. | HTTP 401, `Invalid authentication token`; không trả dữ liệu người dùng. | Authorize Swagger bằng refresh token A rồi gọi `/auth/me` trả 401 `Invalid authentication token`; không trả dữ liệu user. | P0 / High | Pass |
| TC-AUTH-07 | Authentication | Logout xóa token và dữ liệu cache UI | A đã login và có todo riêng trên UI; B tồn tại; DevTools Application/Network mở. | Thực hiện đủ quy trình chi tiết TC-AUTH-07 bên dưới: quan sát token trước/sau logout, Back/route bảo vệ, rồi login B cùng tab và kiểm tra request mới cùng dữ liệu UI. | Cả access/refresh token biến mất sau logout; route bảo vệ không hiện dữ liệu A; login B dùng dữ liệu mới và không hiển thị identity/todo A. Redirect đơn lẻ không đủ Pass. | Codex quan sát A + todo, logout và Back vẫn về login. Người dùng kiểm tra bổ sung và xác nhận cả hai key token biến mất sau logout, chuyển A → B không F5. Ảnh Network cho thấy logout 200, login B 200, request mới /me và /todos đều 200; dashboard đúng B, không có todo A. | P0 / High | Pass |
| TC-AUTHZ-01 | Authorization | B không thấy todo riêng của A trong list | A có `Private-A-<run-id>`; B đăng nhập trong phiên tách biệt; dùng đúng dataset test nhỏ. | 1. A mở list và xác nhận todo hiện.<br>2. B login trong phiên riêng, xác nhận email B.<br>3. Chờ GET `/api/v1/todos` 200 và UI hết loading.<br>4. Kiểm tra response list và UI không chứa ID/title todo A; nếu có phân trang, kiểm tra các trang liên quan. | List B tải thành công nhưng không chứa todo A. Không yêu cầu list B rỗng. | Codex xác nhận A có todo riêng. Người dùng kiểm tra B trong cửa sổ riêng tư độc lập: ảnh hiển thị email B và response `items: [], total: 0`; người dùng xác nhận GET list trả 200. UI/response B không chứa todo A. | P0 / Critical | Pass |
| TC-AUTHZ-02 | Authorization | B GET todo A theo ID | A vừa GET todo 200; Swagger có access token B; `/auth/me` xác nhận B. | 1. B Execute GET `/api/v1/todos/{todo_id}` với `TODO_A_ID`.<br>2. Đọc status/detail, xác nhận không có nội dung todo trả về. | HTTP 404, `Todo not found`; không lộ dữ liệu todo A. | A GET todo trả 200. Sau khi `/auth/me` xác nhận B, B GET cùng ID trả 404 `Todo not found`, không có nội dung todo A. | P0 / Critical | Pass |
| TC-AUTHZ-03 | Authorization | B không sửa được todo A | A vừa GET 200 và đã ghi baseline; access token B còn hạn, `/auth/me` xác nhận B. | 1. B Execute PUT `/api/v1/todos/{todo_id}` với ID A và body `{"title":"Unauthorized change"}`.<br>2. Ghi status/detail.<br>3. Authorize A; GET đúng todo, so với baseline title/description/completed và kiểm tra UI A. | PUT 404 `Todo not found`; GET của A vẫn 200, dữ liệu không đổi. | B PUT title vào ID A trả 404 `Todo not found`. Đổi lại A, GET trả 200; title, description và completed giữ nguyên baseline; UI A vẫn hiện todo cũ. | P0 / Critical | Pass |
| TC-AUTHZ-04 | Authorization | B không xóa được todo A | A vừa GET 200 xác nhận todo tồn tại; B có token hợp lệ; dùng todo test của A. | 1. Authorize B, xác nhận `/auth/me`.<br>2. Execute DELETE `/api/v1/todos/{todo_id}` với ID A.<br>3. Ghi status/detail.<br>4. Authorize A, GET lại ID và kiểm tra UI A. | DELETE 404 `Todo not found`; GET của A vẫn 200 và todo còn tồn tại. | `/auth/me` xác nhận B; DELETE ID A trả 404 `Todo not found`. Đổi lại A, GET cùng ID vẫn 200 và reload UI vẫn hiển thị todo A. | P0 / Critical | Pass |
| TC-AUTHZ-05 | Authorization | Đổi A sang B trong cùng trình duyệt | A/B tồn tại; A đang login và list chứa todo A; Network mở; dùng cùng một tab. | 1. Quan sát email/todo A.<br>2. Bấm Logout, ở `/login` nhập B và Sign In.<br>3. Không F5 hoặc điều hướng bằng thanh địa chỉ giữa logout và login B.<br>4. Quan sát trong lúc chuyển phiên và sau khi `/auth/me`, `/todos` hoàn tất.<br>5. Xác nhận email B và không hiện identity/todo A. | Dữ liệu A không xuất hiện trong phiên B; list tải thành công; không cần F5. | Cùng một tab: A và todo A hiển thị, logout rồi login B ngay bằng form, không F5/nhập URL. Dashboard hiện đúng B và `No todos yet`; Swagger list B trả 200 không chứa todo A. | P0 / Critical | Pass |

### Chi tiết TC-AUTH-07

1. Login A, chờ email và todo A hiển thị.
2. DevTools Application → Local Storage → origin frontend: xác nhận có hai key `access_token` và `refresh_token`; không sao chép giá trị.
3. Logout và xác nhận cả hai key biến mất.
4. Back/truy cập route bảo vệ: về login và không hiện dữ liệu A.
5. Thực hiện chuỗi A login → logout → B login trong cùng tab bằng form, không F5/nhập URL/đóng tab.
6. Network có request mới `/auth/me` và `/todos` trả 200; UI đúng B và không có todo A.
7. Kết quả được người dùng bổ sung bằng ảnh Network và xác nhận key đã bị xóa, chuyển phiên không F5. Không suy diễn việc xóa mọi object React Query trong RAM từ phép thử này.

### Kết quả thực thi

| Tổng case | Pass | Fail | Blocked | Not Run |
|---|---|---|---|---|
| 12 | 12 | 0 | 0 | 0 |

Kết quả tổng hợp mới nhất: 11 case Pass từ lượt manual trước và xác nhận của
người dùng; TC-AUTH-04 Pass sau retest Swagger trên bản sửa. Không tuyên bố đã
chạy lại toàn bộ 12 case trên image mới. Pytest/E2E được ghi riêng trong
`completed.md`, không dùng làm bằng chứng manual.

## 4. Defect Tracking & Known Limitations

### DEF-MANUAL-01 — Login tiết lộ email tồn tại

- Liên kết: TC-AUTH-04. Priority P1; Severity High.
- Lần đầu: email tồn tại + mật khẩu sai trả 401 `Incorrect password`; email không tồn tại trả 404 `User with this email not found`. Quan sát trực tiếp trên Swagger. UI chỉ quan sát được thông báo email không tồn tại.
- Sửa: `backend/app/api/v1/auth.py::login` trả cùng HTTP 401 và detail `Invalid email or password` cho hai nhánh thất bại.
- Retest: sau rebuild backend, gọi login trên Swagger bằng A đúng mật khẩu → 200; A sai mật khẩu → 401; email chưa đăng ký với cùng mật khẩu sai → 401. Hai body lỗi giống hệt nhau, không trả token.
- Trạng thái: **Fixed / Retest Passed** ngày 04/10/2026. Giữ Expected ban đầu; không xóa lịch sử Fail.

### Giới hạn còn lại

- Không còn case Blocked/Not Run trong phạm vi 12 case. Chưa đo trực tiếp toàn bộ React Query cache; chứng cứ là cleanup token và hành vi UI khi đổi phiên.
- UI toast sau sửa TC-AUTH-04 chưa chạy lại; kết luận retest dựa trên Server response Swagger.
- Bản sửa đồng nhất status/body login; chưa đánh giá khác biệt thời gian phản hồi hoặc khả năng dò email qua register (duplicate vẫn trả 400 theo contract).
- Ảnh người dùng có request `/todos` trả 403 ngay sau logout; nguyên nhân chưa xác minh. Request sau login B trả 200. Đây là quan sát bổ sung, chưa kết luận lỗi mới.
- Tài khoản/todo test còn trong database phát triển; không reset database hoặc xóa dữ liệu có sẵn.
- Không mở rộng sang Tier 3 trong đợt này.
