# Run revision7 — đối chiếu frame cũ/mới

Thêm nguyên pose chạm đất vào ba khoảng Owner chỉ rõ; giữ nguyên pixel của8posecũ.

| Frame mới | Nguồn | Tick60Hz |
|---:|---|---:|
| 0 | run r6 #0 | 5 |
| 1 | run r6 #1 | 5 |
| 2 | run r6 #2 | 5 |
| 3 | Pose chạm đất mới tại khoảng old2→3 | 3 |
| 4 | run r6 #3 | 2 |
| 5 | Pose chạm đất mới tại khoảng old3→4 | 3 |
| 6 | run r6 #4 | 5 |
| 7 | run r6 #5 | 5 |
| 8 | run r6 #6 | 5 |
| 9 | run r6 #7 | 2 |
| 10 | Pose chạm đất mới tại khoảng old7→0 | 3 |

Chu kỳ mới:0→1→…→10→0. Tổng43tick≈717ms. Phần old0–2/old4–6 giữ5tick mỗi pose; hai pose bay old3/7 giữ2tick, ba contact mới3tick (50ms) mỗi pose.

Mốc chân mới:Canvas y223. Đây là kiểm chứng pose có điểm tiếp đất, không phải nghiệm thu độ tự nhiên. Owner Human Test vẫn đang chờ.
