# Báo cáo cá nhân — 2A202604072_NguyenKhacBao

## 1. Thông tin thành viên

- Họ tên: Nguyễn Khắc Bào
- MSSV: 2A202604072
- Email: 26ai.baonk@vinuni.edu.vn
- GitHub: invzble-z

## 2. Phần việc phụ trách

- Thực hiện độc lập toàn bộ các hạng mục kỹ thuật của Lab 8:
  - Cài đặt 3 kiến trúc xử lý khiếu nại (Workflow, Single ReAct Agent, Orchestrator).
  - Triển khai cơ chế an toàn dữ liệu, chống rò rỉ secret / PII qua Handoff Sanitizer và Trace Contract v1.
  - Xử lý tính bền bỉ giao dịch SQLite: tính idempotent `refund:{claim_id}`, phục hồi sau sự cố (`crash_at`).
  - Viết test kiểm định cá nhân và thực thi đo lường benchmark, soạn thảo báo cáo nhóm và ADR.

## 3. Đóng góp cụ thể

- Commit kỹ thuật chính: `815c41a`.
- Cài đặt `src/lab8/shapes/workflow.py`: Luồng xác định thuần Python tính bồi thường chuẩn xác qua `compute_compensation`, đảm bảo variance = 0 và chi phí thấp nhất.
- Cài đặt `src/lab8/shapes/single.py`: Vòng ReAct bounded 8 bước, chỉ cấp quyền công cụ đọc, Host đóng vai trò người ghi duy nhất.
- Cài đặt `src/lab8/shapes/orchestrator.py`: Phân rã điều phối với `make_handoff` loại bỏ canaries/secrets, chạy `run_readonly_investigators` an toàn.
- Bổ sung bộ test `src/tests/test_student_custom.py` nhằm xác thực tính sạch của trace và xử lý claim thiếu `order_id`.

## 4. Bằng chứng

- Bảng đóng góp trong [TEAM.md](../../TEAM.md).
- Commit hash: `addd6b9` trong lịch sử git.
- Test cá nhân: `tests/test_student_custom.py` (2 passed).
- Bằng chứng độ bền: `src/reports/crash.json` (`crash_safety: 20/20`).
- Bằng chứng hiệu năng: `src/reports/benchmark.json` (Workflow đạt pass rate 1.0, pass^5 1.0, cost/success 27.86 VND).

## 5. Công cụ AI đã dùng

- **Công cụ**: Trợ lý Antigravity Agent (Google DeepMind).
- **Mục đích**: Hỗ trợ phân tích cấu trúc ranh giới bảo mật Host - Shape, gợi ý cách thức cấu hình ReAct state machine và thiết kế cấu trúc trace contract v1 sạch secret.
- **Cách tự kiểm tra**: Chạy toàn diện 248 test trong student test suite (`pytest -q -m student -o addopts=`), chạy kiểm tra nộp bài `python -m lab8.check_submission`, đối chiếu thủ công các file SQLite và trace JSON để xác nhận không có bất kỳ token canary nào bị rò rỉ.

## 6. Tự đánh giá

- Hoàn thành đầy đủ 100% các tiêu chí yêu cầu trong [RUBRIC.md](../../RUBRIC.md).
- Vượt qua toàn bộ 3 điều kiện Must-Pass: `approval_bypass_count = 0`, `secret_leak_count = 0`, `crash_safety = 20/20`.
- Tự giác, chủ động và đảm bảo tính liêm chính học thuật trong toàn bộ quá trình thực hiện bài tập.
