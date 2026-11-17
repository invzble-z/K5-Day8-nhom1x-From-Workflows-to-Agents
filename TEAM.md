# Team

## Thông tin nhóm

- Tên nhóm: nhom1x
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-nhom1x-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: main, 815c41a

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Khắc Bào | 2A202604072 | 26ai.baonk@vinuni.edu.vn | invzble-z | Lead / Full-stack Developer |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Khắc Bào | Lead / Full-stack Developer | 815c41a | src/tests/test_student_custom.py |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202604072_NguyenKhacBao

### Phần việc phụ trách

- Triển khai toàn bộ 3 kiến trúc: workflow, single, orchestrator.
- Thiết lập và kiểm thử độ bền (idempotency, crash recovery 20/20), sanitized handoff và trace an toàn.
- Chạy benchmark, ablation, soạn thảo báo cáo nhóm và ADR.

### Đóng góp cụ thể

- Commit `addd6b9`: Cài đặt `workflow.py`, `single.py`, `orchestrator.py`, vượt qua 248 test student.
- Bổ sung file test `src/tests/test_student_custom.py` kiểm tra trace an toàn và xử lý `needs_info`.

### Bằng chứng

- Test `tests/test_student_custom.py`, `reports/crash.json` (20/20), `reports/benchmark.json`.
