# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research 2026, Towards a Science of Scaling Agent Systems, Empirical Scaling Benchmark |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Phân rã thêm agent chỉ cải thiện hiệu năng khi subtask có tính độc lập cao; trên task phụ thuộc tuần tự, tăng số tác tử làm tăng chi phí và bề mặt lỗi |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Môi trường hệ thống xử lý claims LogiX-VN với MockLLM, bộ 14 claims có ràng buộc trạng thái SQLite |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Chuyển từ Workflow sang Orchestrator/Swarm không tăng pass rate (1.0 vs 0.986) nhưng làm tăng cost/success ít nhất 70% |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định MockLLM, bộ 14 claims, 5 seeds (11,22,33,44,55), DB state và pricing. Biến thay đổi duy nhất: Topology (Workflow vs Orchestrator vs Swarm) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Swarm trượt claim C-002 ở seed 55 (pass rate giảm còn 0.986, pass^5 = 0.929, variance = 0.000816); cost tăng từ 27.86 lên 47.36 và 49.57 VND |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
- Run id / file report: reports/benchmark.json
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng. Workflow đạt pass rate 1.0, pass^5 1.0, cost/success 27.86 VND. Khi chuyển sang Orchestrator, cost/success tăng 70% lên 47.36 VND mà pass rate không đổi (1.0). Khi chuyển sang Swarm, pass rate giảm xuống 0.986 (fail C-002 seed 55), variance tăng lên 0.000816 và cost/success tăng lên 49.57 VND (+77.9%).
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.
