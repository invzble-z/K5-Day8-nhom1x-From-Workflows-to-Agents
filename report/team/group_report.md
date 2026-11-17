# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu trích xuất trực tiếp từ các file trong `src/reports/`.

## 1. Thông tin nhóm

- Tên nhóm: nhom1x
- Lớp: L3A
- Thành viên: Nguyễn Khắc Bào (MSSV: 2A202604072) — xem chi tiết tại [TEAM.md](../../TEAM.md)
- Commit chốt: `815c41a` (trùng khớp với [report/team/decision_adr.md](decision_adr.md))

---

## 2. Mục tiêu và cách tiếp cận

Bài toán yêu cầu xử lý khiếu nại (claims) bồi thường tiền vận chuyển và thiệt hại hàng hóa cho công ty giả lập LogiX-VN theo 4 hình thái kiến trúc (shapes):
1. **Shape A — Deterministic Workflow**: Quy trình các bước tuần tự cố định bằng code Python.
2. **Shape B — Single Agent (ReAct)**: Vòng lặp ReAct đơn tác tử (tối đa 8 bước) chọn công cụ đọc.
3. **Shape C — Orchestrator**: Kiến trúc điều phối kết hợp các điều tra viên (investigators) chỉ đọc qua gói bàn giao dữ liệu sạch (sanitized handoff).
4. **Shape D — Swarm Reference**: Mô hình bầy đàn đối chứng có sự trao đổi giữa các peer agent.

**Mục tiêu cốt lõi**:
- Xác lập ranh giới nghiêm ngặt giữa **Code** và **Model**: Code quyết định toàn bộ logic tính tiền (`compute_compensation`), kiểm soát quyền sở hữu (`principal_id`), trần hoàn tiền theo đơn (`per-order cap`), xác thực approval và thực thi giao dịch nguyên tử vào ledger; Model chỉ đóng vai trò phân tích nội dung ticket và diễn đạt câu chữ.
- Đảm bảo độ bền bỉ giao dịch (Durability & Idempotency) và khả năng phục hồi an toàn tuyệt đối khi hệ thống gặp sự cố (`crash_at`).
- Giữ vững ranh giới bảo mật: Không làm rò rỉ secret (`CANARY_SECRET_*`) hay thông tin định danh cá nhân (PII) qua trace hay handoff.
- Đo lường thực nghiệm công bằng để lựa chọn kiến trúc tối ưu theo nguyên tắc: **chọn kiến trúc ít tự chủ nhất nhưng giải quyết trọn vẹn bài toán**.

---

## 3. Giải pháp

### 3.1. Ranh giới Code / Model và Ranh giới Bảo mật (Security Boundary)
- **Quyền ghi duy nhất thuộc về Host**: Các shape tuyệt đối không được ghi trực tiếp vào cơ sở dữ liệu SQLite hay tự ý phát hành refund. Mọi yêu cầu ghi tiền đều phải đi qua `durability.issue_refund(conn, claim_id, quote, crash_at=crash_at)`.
- **Nguyên tắc truyền Quote đầy đủ**: Khi đơn hàng đã từng được bồi thường một phần ở các claim trước, shape luôn truyền **toàn bộ số tiền entitlement** tính được từ `compute_compensation`. Host sẽ tự động đọc lại lịch sử giao dịch trong cùng transaction và khấu trừ số tiền đã hoàn trước đó, ngăn chặn lỗi khấu trừ hai lần (double subtraction).
- **Handoff Sanitizer (`lab8.handoff`)**: Trong Shape C, orchestrator khởi tạo gói bàn giao bằng `make_handoff`. Gói này chỉ chứa các trường trong allowlist (`contract_version`, `claim_id`, `task`, `facts`, `allowed_tools`) và từ chối mọi trường secret (`parent_secret`, `raw_headers`, token canary). Các investigator chỉ được cấp danh sách công cụ đọc (`READONLY_TOOLS`).
- **Trace Contract v1**: Trace JSON được ghi nhận độc lập theo `run_id` tại mỗi lần chạy. Chỉ các view dữ liệu đã được lọc sạch (`get_claim_view`, `lookup_order` chỉ chứa 7 trường không nhạy cảm) mới được phép đưa vào trace.

### 3.2. Cài đặt chi tiết 3 Shape
1. **Workflow (`src/lab8/shapes/workflow.py`)**:
   - Mở kết nối SQLite và khởi tạo Trace.
   - Gọi `get_claim_view`: Nếu không tìm thấy trả `failed`; nếu thiếu `order_id` trả `needs_info`.
   - Gọi `lookup_order`: Nếu order không thuộc quyền sở hữu hoặc không tồn tại, trả `escalated` mà không rò rỉ thông tin nội bộ.
   - Tính toán bồi thường bằng `compute_compensation`: Nếu quote = 0, trả `denied` (không gọi issue_refund). Nếu quote > 0, gọi `issue_refund` với quote đầy đủ và chuyển tiếp `crash_at`.
2. **Single ReAct Agent (`src/lab8/shapes/single.py`)**:
   - Vận hành vòng lặp `run_react` với hàm `decide(seen)` giới hạn tối đa 8 bước.
   - `decide` chỉ lựa chọn các read tools (`get_claim_view` -> `lookup_order` -> `compute_compensation`) và trả về `final` action.
   - Sau khi kết thúc vòng ReAct, Host shape tiếp quản việc gọi `issue_refund` với quote được trích xuất an toàn.
3. **Orchestrator (`src/lab8/shapes/orchestrator.py`)**:
   - Đóng gói nhiệm vụ vào `make_handoff` và ủy quyền cho `run_readonly_investigators`.
   - Thu thập kết quả từ investigator, trích xuất quote từ order view chính thức trong DB (bỏ qua số ngày chậm trễ do khách hàng tự khai trong ticket) và thực hiện gọi hoàn tiền qua Host.

---

## 4. Kết quả thực nghiệm

### 4.1. Bảng so sánh 4 Shape trên bộ Public Corpus (14 claims × 5 seeds = 70 trials/shape)
Dữ liệu được trích xuất từ [src/reports/benchmark.json](../src/reports/benchmark.json):

| Shape | Pass Rate | Pass^5 | Seed Min - Max | Population Variance | Chi phí / Thành công (VND) | Mean Steps | P95 Steps | Model Calls TB | Tool Calls TB |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Workflow** | **1.000** | **1.000** | **1.000 - 1.000** | **0.000000** | **27.86** | **2.86** | **3.0** | **0.00** | **2.79** |
| **Single** | 1.000 | 1.000 | 1.000 - 1.000 | 0.000000 | 31.49 | 3.07 | 4.0 | 3.79 | 2.79 |
| **Orchestrator** | 1.000 | 1.000 | 1.000 - 1.000 | 0.000000 | 47.36 | 3.79 | 4.0 | 1.00 | 4.64 |
| **Swarm** | 0.986 | 0.929 | 0.929 - 1.000 | 0.000816 | 49.57 | 2.80 | 3.0 | 3.00 | 1.93 |

### 4.2. Kiểm thử độ bền và An toàn khi gặp sự cố (Crash Safety)
Theo kết quả từ [src/reports/crash.json](../src/reports/crash.json):
- Tổng số kịch bản crash: 20
- Số kịch bản vượt qua: 20
- **Chỉ số an toàn (`crash_safety`)**: **`20/20`** (100% Passed).
- Hệ thống xử lý hoàn hảo các điểm crash: `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`, `amount_conflict_on_retry` và `retry_without_approval`. Khi resume sau crash, hệ thống bảo toàn duy nhất 1 dòng ledger và 1 audit event `refund_committed`.

### 4.3. Quyết định kiến trúc (ADR)
- **Shape được lựa chọn**: **`workflow`**.
- **Lý do**: Workflow đạt hiệu suất tối đa tuyệt đối (Pass rate 1.0, Pass^5 1.0, Variance 0), độ tin cậy 100%, đồng thời có chi phí vận hành thấp nhất (27.86 VND/case) và thời gian thực thi nhanh nhất do loại bỏ hoàn toàn các lời gọi mô hình không cần thiết trên quy trình nghiệp vụ xác định.

---

## 5. Khó khăn và cách xử lý

1. **Khấu trừ trần hoàn tiền theo đơn (Per-order Cap)**:
   - *Vấn đề*: Trong ca kiểm thử T14 (đơn đã hoàn ship 30.000 VND, nay hàng hỏng bồi thường 150.000 VND), nếu shape tự lấy `150.000 - 30.000 = 120.000` rồi truyền vào `issue_refund`, Host sẽ tiếp tục trừ thêm 30.000 VND lần nữa dẫn đến số tiền ghi chỉ còn 90.000 VND (fail test).
   - *Cách xử lý*: Tuân thủ nghiêm ngặt quy định nghiệp vụ: Shape luôn truyền quote đầy đủ (150.000 VND); Host tự động thực hiện phép trừ số tiền đã commit trong transaction.
2. **Quản lý ngoại lệ khi tiêm Crash (`InjectedCrash`)**:
   - *Vấn đề*: Nếu shape dùng khối `try ... except Exception` chung mà vô tình bắt nuốt `InjectedCrash`, tiến trình sẽ không dừng lại đúng thời điểm crash giả lập, làm hỏng bài kiểm tra T12 và crash suite.
   - *Cách xử lý*: Chỉ bắt `InjectedCrash` nhằm mục đích duy nhất là xả buffer trace ra đĩa (`trace.write()`), sau đó dùng lệnh `raise` để ngoại lệ tiếp tục lan truyền.
3. **Bảo mật Trace và chống rò rỉ Canary Token**:
   - *Vấn đề*: Khi debug hoặc ghi nhận log, việc ghi toàn bộ bản ghi `orders` hoặc `claims` sẽ làm lộ số điện thoại, địa chỉ và mã `CANARY_SECRET_PARENT_*`, dẫn đến trượt điều kiện Must-Pass.
   - *Cách xử lý*: Chỉ đưa vào trace các đối tượng đã được cho phép thông qua các hàm adapter `get_claim_view` và `lookup_order` với tập trường cố định `ORDER_FIELDS`.

---

## 6. Tổng hợp đóng góp

Nhóm thực hiện chế độ solo (1 thành viên). Toàn bộ khối lượng công việc được triển khai và kiểm định tập trung:
- **Nguyễn Khắc Bào (2A202604072)**: 100% công số thực hiện (Cài đặt 3 shapes, Durability, Trace contract, Crash suite, Benchmark, Custom tests, Báo cáo và ADR).
- Chi tiết khai báo tại [TEAM.md](../../TEAM.md) và báo cáo cá nhân [report/team/2A202604072_NguyenKhacBao.md](2A202604072_NguyenKhacBao.md).

---

## 7. Hạn chế và hướng cải thiện

- **Mô phỏng bằng MockLLM**: Dữ liệu phản hồi được hash cố định theo seed, chưa phản ánh được sự biến động ngữ nghĩa (semantic drift) và độ trễ ngẫu nhiên của các mô hình LLM lớn ngoài thực tế.
- **Tập dữ liệu Public**: Quy mô 14 claims là tập chuẩn để kiểm thử chức năng; khi triển khai sản xuất, hệ thống cần được đánh giá trên tập dữ liệu hàng nghìn ca khiếu nại với nhiều biến thể ngôn ngữ tự nhiên phức tạp hơn.
- **Hướng cải thiện**: Khi mở rộng sang các bài toán bồi thường phức tạp (ví dụ: thẩm định tổn thất dựa trên hình ảnh kiện hàng hư hỏng), có thể tích hợp mô hình Vision-Language vào Shape C (Orchestrator) như một điều tra viên chuyên biệt.

---

## 8. Tài liệu tham khảo

1. Google Research (2026), *Towards a Science of Scaling Agent Systems*.
2. MAST Team (NeurIPS 2025), *Why Do Multi-Agent LLM Systems Fail?*
3. Tài liệu đặc tả kỹ thuật nội bộ LogiX-VN: [docs/business_rules.md](../../docs/business_rules.md), [docs/contracts.md](../../docs/contracts.md), [docs/architecture.md](../../docs/architecture.md).
