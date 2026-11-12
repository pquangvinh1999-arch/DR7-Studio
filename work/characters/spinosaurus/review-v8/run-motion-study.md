# Spinosaurus run r8 — demo tham khảo chuyển động T-rex

T-rex chỉ là tham khảo nhịp:8pose/40tick,hai marker tiếp đất cách20tick. Spino có12pose mới/42tick,hai marker cách21tick (350ms). Không dùng frame/mask/rig T-rex, chỉ ảnh Spino làm identity input cho imagegen.

| Frame | Tick | Pha quan sát |
|---:|---:|---|
| 0 | 3 | Tiếp cận trong pha bay |
| 1 | 4 | Chân xa chạm đất |
| 2 | 4 | Chân xa chịu lực |
| 3 | 5 | Chân xa đẩy về sau |
| 4 | 4 | Mũi chân xa rời đất |
| 5 | 4 | Bay ngắn, chân gần vươn tới |
| 6 | 3 | Chân gần chạm đất |
| 7 | 3 | Chân gần nén/nhận trọng lượng |
| 8 | 3 | Chân gần trụ qua thân |
| 9 | 3 | Chân gần đẩy về sau |
| 10 | 3 | Mũi chân gần rời đất |
| 11 | 3 | Bay ngắn, chân xa vươn tới rồi nối0 |

Chu kỳ0..11→0. Soát stancepixel Canvas y221..223: chân xa1..4, chân gần6..10 đều tiến từtrướcrasau;khôngđảo/pingpong. Không dùng chỉsố này để nhận naturalness đãduyệt. Toàn bộatlas vẫn DEMO, chờ OwnerHumanTest.
