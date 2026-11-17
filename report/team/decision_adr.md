# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 815c41a
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.0 / 1.0 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Qua thử nghiệm benchmark trên 14 claims và 5 seeds (tổng cộng 70 trials mỗi shape), `workflow` đạt hiệu quả tuyệt đối: pass rate 100% (1.000), pass^5 100% (1.000), độ dao động giữa các seed bằng 0 (variance 0.000000), và chi phí trung bình trên mỗi ca thành công thấp nhất (27.86 VND/success so với 31.49 VND của Single, 47.36 VND của Orchestrator và 49.57 VND của Swarm). Logic bồi thường claim tuân theo các quy tắc nghiệp vụ rõ ràng, tuần tự và xác định, do đó kiến trúc workflow bằng code thuần giải quyết chính xác bài toán mà không phát sinh độ trễ hay rủi ro ảo giác từ LLM.

## Có đáng đổi lấy multi-agent không

Không đáng đổi. Kiến trúc multi-agent (Swarm / Orchestrator) trong bài toán này không nâng cao được độ chính xác (pass rate của Swarm chỉ đạt 0.986 và pass^5 là 0.929 do lỗi suy diễn sai tại seed 55), nhưng chi phí lại tăng gần gấp đôi (49.57 VND vs 27.86 VND) và tăng số lượng message/tool calls. Quyết định chỉ đảo lại khi bài toán xuất hiện các yếu tố: dữ liệu phi cấu trúc phức tạp đòi hỏi nhiều góc nhìn phản biện, chính sách thay đổi liên tục không thể mã hóa trước, hoặc cần sự cộng tác động giữa các tác tử chuyên biệt ở quy mô lớn.

## Trace và bằng chứng

Trace của nhóm ghi nhận các event đã qua allowlist: `claim` (claim_id, principal_id), `lookup_order` (order_id, visible), `quote` (amount_vnd, reason, clause_ids) và `decision` / `crash`. Nhóm cố ý **không** ghi `parent_secret`, `raw_headers`, số điện thoại, địa chỉ khách hàng hay nội dung ghi chú nội bộ để tuân thủ Trace contract v1 và bảo vệ PII. Nếu trace nằm ngoài vùng scanner tự động, đội security chứng minh bằng cách kiểm tra mã nguồn (chỉ sử dụng view đã sanitize, không truyền context thô vào trace/stdout) và chạy kiểm thử rà soát chuỗi ký tự cấm (`forbid_substrings`) trên toàn bộ artifact và stdout sinh ra.

## Giới hạn

MockLLM là mock model theo seed, không phản ánh độ trễ thực tế (`latency: unavailable`) và sự biến thiên ngữ nghĩa phức tạp của LLM thương mại. Quy mô tập claim public (14 claims) là tập đại diện, số liệu benchmark là giả lập theo bảng giá cố định của phòng lab.
