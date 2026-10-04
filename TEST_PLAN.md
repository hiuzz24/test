# Manual Test Plan: Authentication & Authorization — Tier 2C

## 1. Scope & Objective — Phạm vi và mục tiêu

Kiểm tra thủ công xác thực, quyền sở hữu todo và cô lập phiên người dùng sau các
bản sửa Tier 1. Tài liệu dựa trên [template](templates/TEST_PLAN_TEMPLATE.md) và
[README, mục 2C](README.md#2c-manual-test-plan). Phạm vi đúng 12 case bên dưới;
không bao gồm Tier 3, sửa application code hay mở rộng chức năng.

**Tình trạng ngày 04/10/2026 (Asia/Saigon): tài liệu hoàn thành; đã thực hiện
manual trên UI và Swagger; kết quả 9 Pass / 1 Fail / 2 Blocked / 0 Not Run.**

Ứng dụng thực tế được kiểm tra bằng frontend `localhost:3000` và Swagger
`localhost:8000/docs`. Hai tài khoản test và một todo riêng của User A được tạo
trong lượt chạy. Không sử dụng kết quả pytest hoặc Playwright để điền Actual.

Hai case còn Blocked vì trình duyệt kiểm thử không cung cấp DevTools Network,
không cho đọc localStorage và không hỗ trợ tạo BrowserContext/profile độc lập.
Các phần UI và Swagger có thể quan sát vẫn được ghi lại; phần thiếu bằng chứng
không được suy diễn từ source và không được đánh dấu Pass.

### Trạng thái và tiêu chí hoàn thành

| Trạng thái | Ý nghĩa |
|---|---|
| Pass | Đã chạy đủ bước; Actual khớp toàn bộ Expected. |
| Fail | Đã quan sát được hành vi khác Expected; ghi rõ khác biệt. |
| Blocked | Đã bắt đầu case nhưng không thể hoàn thành do điều kiện/môi trường; ghi bước dừng và phạm vi chưa kiểm chứng. |
| Not Run | Chưa bắt đầu case; không có Actual để kết luận. |

- **Tài liệu hoàn thành:** đủ preconditions, bước chạy, Expected, trường Actual,
  phân loại, thống kê và hạn chế cho cả 12 case.
- **Thực thi hoàn thành:** cả 12 case đã chạy đầy đủ, không còn Blocked/Not Run.
  Có Fail thì thực thi có thể hoàn thành nhưng kết quả không đạt hoàn toàn.
- **Kiểm thử đạt:** 12 Pass. Blocked/Not Run không được tính là Pass hoặc đã
  kiểm chứng. Một case có một phần đạt nhưng còn phần chưa kiểm chứng không
  được đánh dấu Pass.

### Priority và Severity độc lập

Priority là thứ tự kiểm tra/xử lý: P0 ưu tiên đầu tiên vì chặn luồng chính hoặc
liên quan kiểm soát truy cập; P1 xử lý tiếp theo; P2 ưu tiên thấp hơn.
Severity là ảnh hưởng nếu hành vi sai: Critical cho đọc/sửa/xóa dữ liệu chéo
user; High cho mất chức năng xác thực hoặc rò rỉ thông tin xác thực/phiên;
Medium cho lỗi chức năng có ảnh hưởng giới hạn; Low cho ảnh hưởng nhỏ.

Phân loại trong ma trận mô tả rủi ro nếu case thất bại, không khẳng định đã có
lỗi. Ví dụ TC-AUTH-04 có Severity High nhưng Priority P1; TC-AUTHZ-02 có
Severity Critical và Priority P0.

## 2. Test Environment & Prerequisites — Môi trường và chuẩn bị

### Môi trường dự kiến và thông tin phải ghi lúc chạy

- Frontend: `http://localhost:3000`.
- Backend: `http://localhost:8000`; prefix API: `/api/v1`.
- Swagger: `http://localhost:8000/docs`.
- Stack Docker Compose: frontend, backend, PostgreSQL, Redis thật.
- Trình duyệt: ghi tên và phiên bản thực tế trong nhật ký; nếu công cụ không
  cung cấp phiên bản thì phải nêu rõ thay vì suy đoán.
- Source tham chiếu lúc soạn: commit `35add7c`. Khi chạy, ghi commit/image đang
  kiểm thử, ngày giờ, người thực hiện và trình duyệt vào nhật ký bên dưới.
- Môi trường đã được xác minh trực tiếp: frontend đăng ký/đăng nhập/todo hoạt
  động; Swagger thực thi được các endpoint auth và todo trên backend thật.

Khởi động từ repository root nếu cần:

```powershell
docker compose up -d --build
docker compose ps
```

Mở frontend và Swagger bằng trình duyệt, xác nhận sử dụng đúng stack. Nếu
không mở được thì ghi lý do cho case đã bắt đầu; các case chưa bắt đầu vẫn
giữ Not Run. Không reset database hay xóa volume.

### Dữ liệu và phiên kiểm thử

1. Chọn mã lần chạy `<run-id>` không trùng, ví dụ ngày giờ cộng hậu tố ngẫu nhiên.
2. Chuẩn bị email test `manual-a-<run-id>@example.com` và
   `manual-b-<run-id>@example.com`; tự chọn mật khẩu riêng cho test đáp ứng form.
   Không ghi mật khẩu vào tài liệu. Các tài khoản này không được giả định đã seed.
3. Thực hiện TC-AUTH-01 để tạo A bằng UI. Tạo B bằng UI trong một phiên trình
   duyệt tách biệt; Brave thường cho cửa sổ thường và cửa sổ riêng tư tách phiên.
   Hai cửa sổ riêng tư có thể dùng chung session, vì vậy không coi chúng là hai
   phiên độc lập. Không dùng profile có tài khoản thật đang làm việc.
4. A tạo todo `Private-A-<run-id>` có mô tả `Description-A-<run-id>` và ghi ID
   nội bộ là `TODO_A_ID`. Xác nhận tạo thành công, lưu baseline title,
   description, completed và user_id. Không dùng todo của người khác.
5. Dùng đúng phiên A/B khi kiểm tra. Mỗi lần thay Bearer trong Swagger, gọi
   `GET /api/v1/auth/me` trước để xác nhận danh tính, trừ case cố ý dùng token
   không hợp lệ. Token và thông tin phiên chỉ dùng tạm cục bộ, không commit.
6. Trước mỗi case GET/PUT/DELETE chéo user, A phải xác nhận todo tồn tại và đọc
   được (GET 200). Nếu case trước làm mất/thay đổi dữ liệu, tạo todo test mới
   của A và cập nhật ID/baseline trước khi chạy case tiếp theo.

### Cách quan sát UI, Network và Swagger

- Mở DevTools bằng F12; bật Network trước thao tác, xem Method và Status của
  request tương ứng. Chờ request kết thúc và UI hết loading; không dùng khoảng
  chờ cố định để kết luận dữ liệu không tồn tại.
- Khi kiểm tra token, xem Application → Local Storage → `http://localhost:3000`.
  Chỉ ghi hai key có/không; không đưa giá trị vào Actual hoặc ảnh báo cáo.
- Trong Swagger: mở endpoint → Try it out → nhập dữ liệu → Execute; đọc
  **Server response**, không nhầm với Example Value hoặc danh sách Responses.
- Authorize dùng HTTPBearer: nhập giá trị token vào trường Value, Swagger tự
  thêm `Bearer`. Trước khi đổi user/token, Logout authorization cũ rồi Authorize
  lại. Logout trong popup Swagger chỉ bỏ Bearer của Swagger, không thay thế
  Logout của ứng dụng.
- Token A/B lấy tạm từ response đăng nhập hoặc localStorage của đúng phiên.
  Không dán token vào tài liệu, log, website JWT bên ngoài hoặc commit.
- Không lưu HAR, ảnh chứa token, request Authorization hoặc mật khẩu vào Git.
  Actual chỉ ghi status, detail lỗi đã làm sạch, danh tính dạng User A/B và kết
  luận dữ liệu. Xóa token tạm/clipboard sau khi hoàn tất.

### Căn cứ Expected và HTTP contract

| Hành vi | Expected | Căn cứ |
|---|---|---|
| Register thành công / trùng email | 201 / 400 `Email already registered` | `backend/app/api/v1/auth.py`, hàm `register` |
| Login đúng và logout hợp lệ | 200 | `backend/app/api/v1/auth.py`, `login`, `logout` |
| Token sai chữ ký hoặc refresh dùng như access | 401 `Invalid authentication token` | `backend/app/core/security.py::verify_token` và `backend/app/api/deps.py::get_current_user` |
| GET/PUT/DELETE todo không thuộc user | 404 `Todo not found` | `backend/app/services/todo_service.py::get_todo_by_id` lọc id + user_id; các detail handler trong `backend/app/api/v1/todos.py` |
| UI logout và session isolation | Xóa token/cache; route được bảo vệ | `frontend/src/lib/authSession.ts`, auth hooks, `frontend/src/router/ProtectedRoute.tsx` |
| Sai mật khẩu / email không tồn tại | Cùng HTTP 401 và cùng lỗi chung `Invalid email or password` | Mục tiêu bảo mật trong TC-02 của template; **không phải contract hiện đang triển khai** |

Source login hiện phân biệt 404 `User with this email not found` và 401
`Incorrect password`. Đây là nhận xét tĩnh, chưa phải Actual. Expected của
TC-AUTH-04 được giữ nguyên để phát hiện chênh lệch so với mục tiêu bảo mật.
Không sửa Expected theo response sau khi chạy. Các case token yêu cầu Bearer
có giá trị; thiếu hoàn toàn header là tình huống khác, không dùng để thay thế.

## 3. Test Cases Matrix — Đúng 12 trường hợp

Các bước gọi API dưới đây đều thực hiện bằng Swagger hoặc quan sát Network
của thao tác UI. Các preconditions phải được xác nhận ở lần chạy thực tế.

| TC ID | Module / Scenario | Preconditions | Test Steps | Expected Result | Actual Result | Priority | Severity | Status |
|---|---|---|---|---|---|---|---|---|
| TC-AUTH-01 | Đăng ký tài khoản mới | Email A chưa dùng; frontend và API sẵn sàng; Network mở. | 1. Mở `/register`.<br>2. Điền email A, mật khẩu test và Confirm Password.<br>3. Bấm Create Account.<br>4. Xem POST `/api/v1/auth/register`, chờ dashboard tải. | POST 201; vào `/`; dashboard hiển thị đúng email A. | Đăng ký A trên UI thành công, tự vào `/` và hiển thị đúng email A. Một đăng ký mới riêng trên Swagger trả 201 và token response. | P0 | High | Pass |
| TC-AUTH-02 | Đăng ký trùng email | A đã đăng ký; dùng phiên đã logout. | 1. Mở `/register`.<br>2. Điền lại email A, mật khẩu test hợp lệ và xác nhận.<br>3. Bấm Create Account.<br>4. Đọc status/detail trong Network và lỗi UI. | HTTP 400, detail `Email already registered`; UI báo lỗi, không tạo session mới. | UI hiển thị `Email already registered`; lặp request trùng email trên Swagger trả 400 cùng detail và không tạo session UI mới. | P1 | Medium | Pass |
| TC-AUTH-03 | Logout và login đúng mật khẩu | A đang login; biết mật khẩu test; Network mở. | 1. Bấm Logout và đọc POST `/auth/logout`.<br>2. Trên `/login`, nhập đúng email/mật khẩu A và bấm Sign In.<br>3. Đọc POST `/auth/login`; chờ `/auth/me` và dashboard. | Logout 200; login 200; dashboard đúng email A. | UI logout về `/login`, login lại đúng mật khẩu và dashboard hiển thị A cùng todo cũ. Swagger xác nhận login 200 và logout 200 `Successfully logged out`. | P0 | High | Pass |
| TC-AUTH-04 | Chống user enumeration khi login sai | A tồn tại; chuẩn bị email chưa đăng ký có run-id mới; hai request cùng một mật khẩu sai. | 1. Ở `/login`, gửi email A + mật khẩu sai; ghi status/detail.<br>2. Gửi email chưa tồn tại + cùng mật khẩu sai; ghi status/detail.<br>3. So sánh cả response và thông báo UI; nếu toast mất do redirect 401, đọc response trong Network. | Cả hai HTTP 401, cùng lỗi chung `Invalid email or password`; không tiết lộ email tồn tại. | Email A + mật khẩu sai trả 401 `Incorrect password`; email chưa tồn tại trả 404 `User with this email not found`. UI cũng hiển thị hai thông báo khác nhau. Khác Expected, có thể dò email tồn tại. | P1 | High | Fail |
| TC-AUTH-05 | Access token sai chữ ký | Access token A còn hạn; Swagger đã xác nhận `/auth/me` 200 với bản gốc. | 1. Tạo bản sao token tạm, giữ nguyên header/payload và hai dấu chấm.<br>2. Đổi ký tự đầu của phần chữ ký sang ký tự base64url khác (A thành B, khác A thì thành A); không chỉ đổi ký tự cuối.<br>3. Authorize bản sửa.<br>4. Execute GET `/api/v1/auth/me`; đọc Server response.<br>5. Bỏ authorization sai sau test. | HTTP 401, `Invalid authentication token`; không trả dữ liệu người dùng. | Token gốc gọi `/auth/me` trả 200 đúng A; sửa ký tự đầu phần signature rồi gọi lại trả 401 `Invalid authentication token`, không có dữ liệu user. | P0 | High | Pass |
| TC-AUTH-06 | Refresh token dùng như access | Có refresh token A còn hạn từ đăng nhập; Swagger dùng đúng HTTPBearer. | 1. Bỏ Bearer cũ trong Swagger.<br>2. Authorize bằng refresh token.<br>3. Execute GET `/api/v1/auth/me`.<br>4. Đọc Server response và bỏ authorization sau test. | HTTP 401, `Invalid authentication token`; không trả dữ liệu người dùng. | Authorize Swagger bằng refresh token A rồi gọi `/auth/me` trả 401 `Invalid authentication token`; không trả dữ liệu user. | P0 | High | Pass |
| TC-AUTH-07 | Logout xóa token và dữ liệu cache UI | A đã login và có todo riêng trên UI; B tồn tại; DevTools Application/Network mở. | Thực hiện đủ quy trình chi tiết TC-AUTH-07 bên dưới: quan sát token trước/sau logout, Back/route bảo vệ, rồi login B cùng tab và kiểm tra request mới cùng dữ liệu UI. | Cả access/refresh token biến mất sau logout; route bảo vệ không hiện dữ liệu A; login B dùng dữ liệu mới và không hiển thị identity/todo A. Redirect đơn lẻ không đủ Pass. | Đã quan sát A + todo, logout về login, Back vẫn ở route bảo vệ, rồi A → logout → B trong cùng tab không F5; B hiện đúng email và không có todo A. Không thể đọc hai key localStorage hoặc DevTools Network nên chưa kiểm chứng trực tiếp token cleanup và request mới. | P0 | High | Blocked |
| TC-AUTHZ-01 | B không thấy todo riêng của A trong list | A có `Private-A-<run-id>`; B đăng nhập trong phiên tách biệt; dùng đúng dataset test nhỏ. | 1. A mở list và xác nhận todo hiện.<br>2. B login trong phiên riêng, xác nhận email B.<br>3. Chờ GET `/api/v1/todos` 200 và UI hết loading.<br>4. Kiểm tra response list và UI không chứa ID/title todo A; nếu có phân trang, kiểm tra các trang liên quan. | List B tải thành công nhưng không chứa todo A. Không yêu cầu list B rỗng. | Swagger `/auth/me` xác nhận B; GET list B trả 200 và không chứa todo A; UI B cũng không hiện todo A. Công cụ không tạo được BrowserContext/profile độc lập, nên điều kiện phiên tách biệt chưa được kiểm chứng. | P0 | Critical | Blocked |
| TC-AUTHZ-02 | B GET todo A theo ID | A vừa GET todo 200; Swagger có access token B; `/auth/me` xác nhận B. | 1. B Execute GET `/api/v1/todos/{todo_id}` với `TODO_A_ID`.<br>2. Đọc status/detail, xác nhận không có nội dung todo trả về. | HTTP 404, `Todo not found`; không lộ dữ liệu todo A. | A GET todo trả 200. Sau khi `/auth/me` xác nhận B, B GET cùng ID trả 404 `Todo not found`, không có nội dung todo A. | P0 | Critical | Pass |
| TC-AUTHZ-03 | B không sửa được todo A | A vừa GET 200 và đã ghi baseline; access token B còn hạn, `/auth/me` xác nhận B. | 1. B Execute PUT `/api/v1/todos/{todo_id}` với ID A và body `{"title":"Unauthorized change"}`.<br>2. Ghi status/detail.<br>3. Authorize A; GET đúng todo, so với baseline title/description/completed và kiểm tra UI A. | PUT 404 `Todo not found`; GET của A vẫn 200, dữ liệu không đổi. | B PUT title vào ID A trả 404 `Todo not found`. Đổi lại A, GET trả 200; title, description và completed giữ nguyên baseline; UI A vẫn hiện todo cũ. | P0 | Critical | Pass |
| TC-AUTHZ-04 | B không xóa được todo A | A vừa GET 200 xác nhận todo tồn tại; B có token hợp lệ; dùng todo test của A. | 1. Authorize B, xác nhận `/auth/me`.<br>2. Execute DELETE `/api/v1/todos/{todo_id}` với ID A.<br>3. Ghi status/detail.<br>4. Authorize A, GET lại ID và kiểm tra UI A. | DELETE 404 `Todo not found`; GET của A vẫn 200 và todo còn tồn tại. | `/auth/me` xác nhận B; DELETE ID A trả 404 `Todo not found`. Đổi lại A, GET cùng ID vẫn 200 và reload UI vẫn hiển thị todo A. | P0 | Critical | Pass |
| TC-AUTHZ-05 | Đổi A sang B trong cùng trình duyệt | A/B tồn tại; A đang login và list chứa todo A; Network mở; dùng cùng một tab. | 1. Quan sát email/todo A.<br>2. Bấm Logout, ở `/login` nhập B và Sign In.<br>3. Không F5 hoặc điều hướng bằng thanh địa chỉ giữa logout và login B.<br>4. Quan sát trong lúc chuyển phiên và sau khi `/auth/me`, `/todos` hoàn tất.<br>5. Xác nhận email B và không hiện identity/todo A. | Dữ liệu A không xuất hiện trong phiên B; list tải thành công; không cần F5. | Cùng một tab: A và todo A hiển thị, logout rồi login B ngay bằng form, không F5/nhập URL. Dashboard hiện đúng B và `No todos yet`; Swagger list B trả 200 không chứa todo A. | P0 | Critical | Pass |

### Quy trình chi tiết TC-AUTH-07

1. Khi A đang login, xác nhận dashboard có email A và todo riêng. Chờ list tải xong.
2. DevTools Application → Local Storage → đúng origin frontend: quan sát hai key
   `access_token`, `refresh_token` tồn tại. Ghi boolean có/không, không chụp giá trị.
3. Bấm Logout trong ứng dụng. Quan sát POST logout hoàn tất và trang login hiện.
4. Kiểm tra lại cùng origin: cả hai key phải biến mất. Không tự xóa key để làm test đạt.
5. Bấm Back; nếu cần thử truy cập `/`. Route bảo vệ phải chuyển về `/login`,
   không hiển thị email/todo A. Ghi riêng hành vi quan sát được.
6. Để tránh reload che giấu cache trong RAM, thực hiện thêm chuỗi liên tục ngay
   trong cùng tab: login A, chờ dữ liệu A → bấm Logout → kiểm tra hai key biến
   mất → login B bằng form. Không F5, không nhập URL và không đóng tab trong chuỗi này.
7. Network phải có request mới tới `/api/v1/auth/me` và `/api/v1/todos` sau login B,
   trả thành công; UI phải hiển thị B và không chứa identity/todo của A, kể cả
   giai đoạn chuyển phiên. Không kết luận chỉ từ redirect.
8. Actual phải ghi đủ: token trước/sau logout (hai key), Back/route, request mới,
   identity và todo quan sát được. Thiếu khả năng kiểm tra storage hoặc network
   thì ghi phần chưa kiểm chứng và Blocked, không Pass.

Giới hạn phép kiểm: quy trình kiểm chứng việc xóa token trực tiếp và **hành vi
cache UI** qua chuyển phiên không reload. Nó không đo trực tiếp toàn bộ nội
dung React Query cache trong bộ nhớ. Nếu không có công cụ xem cache, không
khẳng định đã quan sát số query hoặc mọi object trong RAM bị xóa. Source gọi
`queryClient.clear()` chỉ là căn cứ thiết kế, không phải bằng chứng manual.
Logout frontend cũng không đồng nghĩa JWT đã bị thu hồi ở server; kiểm tra
revocation không nằm trong 12 case này.

## 4. Defect Tracking & Known Limitations — Lỗi và giới hạn

### DEF-MANUAL-01 — Phản hồi login tiết lộ email đã đăng ký

- **Liên kết:** TC-AUTH-04.
- **Actual:** email tồn tại với mật khẩu sai trả 401 `Incorrect password`; email
  chưa tồn tại trả 404 `User with this email not found`. UI hiển thị hai thông
  báo khác nhau tương ứng.
- **Ảnh hưởng:** kẻ tấn công có thể phân biệt email đã đăng ký để thực hiện user
  enumeration và chuẩn bị tấn công tiếp theo.
- **Severity:** High.
- **Priority:** P1.
- **Đề xuất:** dùng cùng HTTP 401 và cùng detail chung `Invalid email or password`
  cho cả hai trường hợp; không thay đổi Expected để hợp thức hóa Actual.

- [BUG_REPORT.md](BUG_REPORT.md) chưa có mục user enumeration. Không liên kết
  TC-AUTH-04 với một BUG-01…08 không tương ứng và không tự sửa application code.
- Các liên hệ hồi quy khác: TC-AUTH-06 → BUG-02; TC-AUTH-07/TC-AUTHZ-05 → BUG-08;
  TC-AUTHZ-01 → BUG-04; TC-AUTHZ-02…04 → BUG-03. Đây là liên hệ phạm vi, không phải
  kết quả thực thi mới. Token hết hạn (BUG-01) không thuộc 12 case đã khóa.
- Chưa thể kiểm tra trực tiếp hai key localStorage và Network của frontend;
  TC-AUTH-07 còn Blocked dù phần chuyển phiên UI đã hoạt động đúng.
- Trình duyệt kiểm thử không cung cấp BrowserContext/profile độc lập;
  TC-AUTHZ-01 còn Blocked dù Swagger và UI cùng cho thấy list B không có todo A.
- Khi hoàn tất test, có thể xóa todo test bằng chính A sau khi đã ghi kết quả.
  Không xóa dữ liệu khác hay reset database; tài khoản test có thể còn lại.

### Nhật ký thực thi

| Trường | Giá trị |
|---|---|
| Ngày soạn | 04/10/2026, Asia/Saigon |
| Người thực hiện manual | Codex, thao tác trực tiếp qua UI/Swagger |
| Ngày giờ thực thi | 04/10/2026, khoảng 14:48–14:56 Asia/Saigon |
| Commit/image được kiểm thử | Application code `35add7c`; local docs commit `b4d6282` không đổi runtime |
| Browser/version | Codex In-app Browser (Chromium; phiên bản không được công cụ cung cấp) |
| Dữ liệu A/B và todo test | Đã tạo A, B, một tài khoản đăng ký phụ và một todo riêng A; không ghi credential/token |
| Giới hạn công cụ | Không có DevTools Network/localStorage và BrowserContext độc lập |

### Thống kê kết quả

| Tổng case | Pass | Fail | Blocked | Not Run |
|---|---|---|---|---|
| 12 | 9 | 1 | 2 | 0 |

### Phạm vi chưa kiểm chứng

Không còn case Not Run. Hai case dưới đây đã bắt đầu và đã kiểm tra được một
phần, nhưng chưa đủ bằng chứng để kết luận Pass.

| Case | Trạng thái | Phần còn phải kiểm chứng |
|---|---|---|
| TC-AUTH-07 | Blocked | Cần DevTools Application/Network để xác nhận hai key token biến mất và request mới `/auth/me`, `/todos`; phần route và chuyển A → B không F5 đã kiểm tra. |
| TC-AUTHZ-01 | Blocked | Cần chạy B trong BrowserContext/profile độc lập; list B 200 và không có todo A đã kiểm tra bằng Swagger/UI cùng phiên. |

**Kết luận hiện tại:** tài liệu hoàn thành nhưng thực thi chưa hoàn thành vì còn
2 Blocked. Bộ kiểm thử không đạt hoàn toàn: 9 Pass, 1 Fail xác nhận
DEF-MANUAL-01, 2 Blocked và 0 Not Run. Blocked không được tính là Pass.
