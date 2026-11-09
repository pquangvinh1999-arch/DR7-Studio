# Vegeta SSJB — hồ sơ phân tích nguồn, chưa xử lý

Ngày phân tích: 2026-11-09. Phạm vi Owner: xem kỹ ảnh, học cấu trúc, viết skill; **không setup, không cắt/key/export**. Đây không phải quy trình được Human Test nghiệm thu.

## 1. Nguồn và cách đọc tọa độ

| Thuộc tính | Kết quả đo |
|---|---|
| File tại root repo | `dcejfvj-b1332eb1-d8da-4942-9daf-593546093f9b.png` |
| SHA-256 | `d44688b654bc60c2175c1f7517b2d8bbdb00401dc680626296e9ad2313c4d82a` |
| Bytes | 328319 |
| PNG / mode | RGBA, 763 × 2287 px |
| Alpha min/max | 255 / 255: không có pixel trong suốt |
| Màu nền chính | RGB `(254,190,22)`, hex `#FEBE16`, alpha 255 |
| Số pixel đúng màu nền | 1026821 / 1744981, khoảng 58.8443% toàn ảnh |
| Số màu RGBA toàn sheet | 5860; có cả UI, chữ, FX, không phải palette riêng nhân vật |
| Metadata | sRGB=0, gamma=0.45455, DPI=(96.012,96.012) |

Ảnh đã mở toàn bộ và 8 dải phóng nearest 2× để đọc chi tiết. Dải tạm nằm ngoài repo, chỉ dùng quan sát. Không thay đổi ảnh nguồn. Không kết luận file có/không nội suy chỉ từ tổng số màu hay kích thước lẻ.

Tọa độ bên dưới thuộc file **763 × 2287**, không thuộc ảnh chat đã thu hiển thị. `Rect(x,y,w,h)` dùng cận phải/dưới loại trừ. Khoảng hàng `[y0,y1)` cũng loại trừ y1. Cửa sổ khảo sát không phải mask ownership hay crop runtime.

## 2. Cấu trúc tổng thể

Đây là sprite sheet trình bày theo nhóm chức năng, khoảng cách và kích thước không đều, không có lưới cố định. Tiêu đề `VEGETA SSJB`; thân nhỏ kiểu pixel sprite nhìn bên/chéo, có pose chính diện, xoay và nằm ngang. Tóc xanh cyan, đồ xanh đậm, găng/giày sáng và giáp có vùng vàng. Intro còn có tóc đen và silhouette xanh; không được ép palette cả ảnh theo trạng thái SSJB.

Tám nhãn chức năng: `INTRO`, `STAND`, `MOVEMENT`, `ATTACKS`, `DAMAGE`, `KI`, `SUPERS`, `ULTIMATES`. Mỗi nhãn có biểu tượng tròn; nhóm từ STAND đến ULTIMATES dùng ngọc với số sao tăng dần 1→7, INTRO dùng biểu tượng xanh có lưới. Nét đen kéo ngang dưới tên nhóm là trang trí, không phải speed-line của nhân vật.

| Vùng | Cửa sổ Y gốc khảo sát | Nội dung |
|---|---|---|
| Header | `[0,74)` | Khung cam/đen, tên cyan và portrait góc phải |
| Intro | `[75,224)` | Nhãn, hai logo góc phải, chuỗi biến hình bên dưới |
| Stand | Nhãn `[229,289)`, pose `[296,347)` | Một hàng 13 pose thân |
| Movement | Nhãn `[355,415)`, hình `[421,475)` | 4 pose thân và các smear/teleport FX |
| Attacks | Nhãn `[483,543)`, hình `[549,748)` | 3 hàng, đa nhóm đánh |
| Damage | Nhãn `[749,809)`, pose `[821,876)` | 7 pose phản ứng/knockdown |
| Ki | Nhãn `[882,942)`, hình khảo sát `[957,1070)` | Aura, pose phát ki, đạn rời |
| Supers | Nhãn bên trái khoảng `[1038,1099)`, hình `[1095,1530)` | 4 hàng bố cục, nhiều nhóm chiêu và FX |
| Ultimates | Nhãn `[1535,1595)`, hình `[1597,1884)` | 2 chuỗi, beam vàng và xanh lục lớn |
| Footer | `[1886,2287)` | Credits, logo, bảng xếp hạng và palette/trang phục |

Các cửa sổ có thể chồng Y: KI có đạn chéo thấp hơn nhãn SUPERS; đuôi đạn SUPER chạm Y của hàng sau. Vì vậy không thể cắt toàn chiều ngang theo ranh giới nhãn.

## 3. INTRO — chuỗi chuyển trạng thái

Quan sát 13 slot có thân/silhouette từ trái sang phải, không phải 13 frame timeline đã chốt:

1. Tóc đen, khoanh tay.
2–4. Tóc đen, các biến đổi tay/thân ở tư thế đứng.
5. Tóc đen, năng lượng cyan thấp cuộn quanh chân.
6. Ngửa đầu, năng lượng tiếp tục cuộn.
7. Thân bị bao bởi dải xoáy xanh-trắng lớn hơn.
8. Quả cầu/aura lớn cyan-trắng, vẫn thấy thân bên trong và hai cụm năng lượng ở chân.
9. Silhouette cyan với các tia sáng cao phía trên.
10–11. Silhouette cyan nhỏ hơn, hình thân/tóc thay đổi.
12. Chi tiết thân/giáp bắt đầu hiện qua silhouette/aura.
13. Thân SSJB đầy đủ trong aura xanh-trắng.

Các khoảng X kiểm kê vùng thấp `[155,224)`: `[18,43)`, `[50,79)`, `[85,114)`, `[118,147)`, `[151,208)`, `[216,283)`, `[292,369)`, sau đó vùng cầu + silhouette `[376,578)`, `[582,609)`, `[614,639)`, `[644,673)`, `[681,755)`. Vùng `[376,578)` chứa **hai slot**, bị hợp bởi phép chiếu X; phải tách bằng quan sát 2D, không coi là một frame. Phần FX cao hơn Y=155 cần được giữ khi lập mask thực tế.

Không dùng silhouette cyan hoặc thân bạc/trắng trong hiệu ứng như bằng chứng nhân vật thiếu màu. Đây là các hình nguồn cần bảo toàn.

## 4. STAND — 13 pose, chưa phải một idle loop

Hàng Y=`[296,347)`. Các khoảng X foreground tách được, trái→phải:

| Slot | Khoảng X | Quan sát |
|---|---|---|
| S01 | `[20,45)` | Đứng chính diện |
| S02 | `[49,74)` | Đứng quay lưng |
| S03 | `[77,102)` | Thân chéo, tay đưa ngang |
| S04 | `[105,130)` | Biến thể pose chéo kế tiếp |
| S05 | `[133,156)` | Đứng tay hạ |
| S06 | `[160,184)` | Đứng, tay co/đổi vị trí |
| S07 | `[188,211)` | Khoanh tay/guard tĩnh |
| S08 | `[216,243)` | Tay trước đưa ra |
| S09 | `[244,268)` | Tay/nắm đấm đổi vị trí |
| S10 | `[273,300)` | Tay trước, thân chéo |
| S11 | `[302,336)` | Hạ trọng tâm, chân mở |
| S12 | `[339,378)` | Hạ trọng tâm rộng hơn, tay trước mở |
| S13 | `[381,406)` | Trở lại thân đứng chéo |

Không mặc nhiên dùng cả 13 pose làm một idle; có hướng nhìn và nhóm tư thế khác nhau. S01 đo foreground bbox `Rect(20,296,25,51)`, 811 pixel khác màu nền. S13 đo `Rect(381,298,25,49)`, 809 pixel khác nền. Đây là kích thước nguồn ở hai pose, chưa phải body metric của bundle xuất.

Ở giả định đo lường 64 PPU, 25×51 px tương ứng 0.390625×0.796875 đơn vị thế giới và 0.78125×1.59375 ô 32 px. Đây là quy đổi, không phải tỷ lệ world đã được Owner chọn.

## 5. MOVEMENT — thân và smear phải phân biệt

Hàng Y=`[421,475)`:

- M01 X=`[17,48)`: thân co chân, dáng di chuyển.
- M02 `[54,96)`: thân nghiêng, chân sau kéo ra.
- M03 `[105,138)`: nâng gối, thân chéo.
- M04 `[148,175)`: hai tay nâng cao trên đầu.
- FX-H01 `[182,233)` và FX-H02 `[239,290)`: hai cụm smear nằm ngang cyan/trắng/xanh đậm, không có thân đầy đủ.
- FX-V01 `[302,323)`, V02 `[337,362)`, V03 `[373,400)`, V04 `[413,440)`: các vệt dọc độ đầy khác nhau, có nhiều island rời.

Các pose không đủ chứng minh một walk/run cycle liên tục; các vệt gợi ý dịch chuyển nhanh nhưng tên `teleport`, `dash` và thứ tự pha còn là ứng viên.

Khoảng trống còn có pixel khác nền: `(475,376)` RGBA `(252,215,88,255)`; cụm 3 pixel trong `Rect(474,379,2,2)`; `(475,387)` cùng màu. Chúng ở trên vùng hình movement, phải được ghi vào inventory, không tự quy thành FX hoặc xóa khi mới phân tích.

## 6. ATTACKS — 3 hàng, 44 pose thân quan sát

44 là tổng **16 + 16 + 12 pose có thân**, không bao gồm FX dọc độc lập và không phải 44 frame của một clip. Phân nhóm gameplay dưới đây chỉ mô tả hình dáng.

### ATK-R1 — Y `[549,599)`, 16 pose

Khoảng X slot lần lượt: `21–54`, `54–112`, `116–156`, `162–198`, `201–261`, `263–306`, `314–351`, `354–403`, `406–452`, `456–491`, `503–531`, `536–581`, `584–628`, `640–676`, `683–718`, `725–757` (cận phải loại trừ; cửa sổ, chưa phải mask).

- P01–P06: đổi thủ/đấm ngang, có vệt đấm kéo dài và vòng đầu đấm sáng.
- P07–P10: hạ thân, quét/vung tay với cung cyan-vàng; các cung vươn xa thân.
- P11–P13: nâng chân, đá chéo rồi đá ngang.
- P14–P16: xoay người/đá và cung lớn quanh phần trên thân, kết thúc pose co người.

Pixel rời tại X=`[51,52)` cùng hàng không được bỏ chỉ vì không liền thân. Phân tách những pose sát nhau cần ownership 2D; thứ tự nguồn không chứng minh tất cả là cùng combo.

### ATK-R2 — Y `[603,662)`, 16 pose

Khoảng X slot: `19–62`, `65–120`, `124–166`, `176–205`, `210–256`, `259–302`, `306–348`, `353–389`, `393–439`, `450–482`, `488–547`, `549–595`, `604–643`, `648–678`, `687–723`, `731–754`.

- P01–P03: thân gập gần nằm ngang, chân đá dựng lên kèm cung rồi chuyển pha.
- P04–P07: thân hạ thấp, chuyển chân/đá xoay/vươn ngang.
- P08–P09: hai pose thân xoay/lộn nằm ngang.
- P10–P12: chuyển lên cao, đá chéo có vệt trắng dài rồi duỗi chân.
- P13–P16: thân nghiêng, vung/đá với cung quanh thân rồi co chân hồi thế.

Phần `[110,120)` là island theo phép chiếu X của slot P02, không phải pose thứ 17.

### ATK-R3 — Y `[669,748)`, 12 pose + 1 cụm FX độc lập

- P01 `[18,97)`: thân hạ thấp trong các tia sáng vàng/trắng.
- P02 `[102,176)`, P03 `[184,256)`: hai aura xanh-trắng có thân.
- P04 `[265,301)`, P05 `[304,335)`, P06 `[339,385)`: thân hạ thấp rồi vươn nhanh sang phải.
- FX `[399,424)`: nhiều vệt đứng rời; chưa gán chắc chắn vào clip nào.
- P07 `[440,474)`, P08–P11 trong `[482,638)`, P12 `[646,683)`: 6 pose nhóm bên phải, chân co/nâng, thay đổi tay và hướng thân.
- Một **vạch trắng dưới nhóm giữa bên phải** nối khoảng X giữa các pose. Nó làm phép chiếu X hợp P08–P11 thành một vùng lớn. Ghi loại trừ vạch sau khi đo mask cụ thể; không coi vạch là mặt đất hoặc hiệu ứng của nhân vật.

## 7. DAMAGE — 7 pose phản ứng

Y=`[821,876)`, X slot: `[24,51)`, `[58,100)`, `[106,143)`, `[148,189)`, `[195,234)`, `[241,268)`, `[273,325)`.

Trái→phải: thân phản ứng đứng; nghiêng/co người; thân hất ra sau; ngửa đầu và tay buông; thân lùi/đổi chân; pose đứng chéo; cuối cùng thân nằm ngang sát mặt đất. Đây là ứng viên hit/knockback/knockdown, chưa chứng minh đủ chuỗi KO, nằm chờ và đứng dậy.

## 8. KI — 11 pose có thân và 4 FX rời quan sát

- K01 `[18,95)`: thân tương phản đen/trắng, tóc vẫn có sắc cyan và năng lượng xanh ở chân; không tự đổi về màu da/giáp thông thường.
- K02 `[102,176)`, K03 `[184,256)`, K04 `[261,333)`: ba pose có aura cao, tay khác nhau.
- K05–K07 trong X=`[349,457)`: nâng tay lên đầu, chuyển tay, vươn tay phát ki.
- Hai đạn chéo riêng ở khoảng X=`[462,565)`, Y khoảng `1025–1070`, nằm thấp hơn hàng thân, vươn xuống cùng Y nhãn SUPERS.
- K08–K11 trong X=`[520,673)`: bốn pose co chân/phát ki; một pose có quả cầu nhỏ gần tay.
- FX riêng `[679,701)`: chớp/cung đứng sáng.
- FX riêng `[705,749)`: đạn ngang có đuôi dài hướng sang phải.

Không đếm quả cầu đang gắn tay thành thân mới, không ghép hai projectile chéo theo thứ tự X nếu chưa có mapping hướng bắn. Bốn FX rời là hai đạn chéo, một burst đứng và một đạn ngang; các pixel rời trong đuôi là một phần FX tương ứng.

## 9. SUPERS — 4 hàng bố cục

### SUP-R1 — khảo sát Y `[1095,1189)`

5 slot có thân: hai pose chuẩn bị bên trái; pose trong bùng sáng tím hình sao; pose đưa tay; cuối cùng thân nằm trong cầu/burst tím, nối với một tia tím kéo dài sang phải và đầu tròn lớn. Toàn vùng cuối khảo sát `Rect(220,1095,271,94)` có foreground trong `[220,1095,490,1189)`.

Không gọi tên chiêu cụ thể khi sheet chỉ ghi SUPERS. Phần tím có thân và beam nối nhau: không tách xóa thân phủ sáng, không key tím vì nó là nội dung.

### SUP-R2 — khảo sát Y `[1195,1318)`

4 pose có thân: ba pose bên trái đổi tay/chuẩn bị, một pose vươn tay sau quả cầu nhỏ. Có 4 hình năng lượng độc lập: một cầu nhỏ giữa các pose và ba cầu lớn kế tiếp ở phía phải. Ba cầu lớn khác nhau ở vòng ngoài, vòng đứt và tia chéo; không coi là ba bản sao hoàn toàn.

Cầu nhỏ nằm khoảng X=`[125,168)`, ba cầu lớn trong `[219,331)`, `[354,480)`, `[514,626)`. Các vòng ngoài đứt rời phải được sở hữu cùng cầu; largest-component sẽ làm mất vòng.

### SUP-R3 — khảo sát Y `[1318,1451)`

8 slot có thân quan sát: pose co chân bên trái; dash có aura và vệt cong dài; thân lộn ngang; thân hạ thấp; bốn pose đứng/đổi tay tiếp theo, pose cuối có cầu ki tại tay. Hai FX rời ở cuối: một cầu gai nhỏ và một đạn chéo kéo đuôi dài xuống phải.

Các vùng X kiểm kê: thân đầu `[21,51)`, dash `[56,167)`, lộn `[175,229)`, hạ thấp `[237,275)`, bốn thân trong `[282,410)`; cầu rời khoảng `[414,451)`, đạn chéo `[456,515)`.

Đuôi đạn còn có pixel RGBA `(9,88,208,255)` tại `(492,1450)`, `(496,1450)`, `(505,1450)`. Chúng thuộc rìa khảo sát đạn của hàng trên, không phải bằng chứng có ba đốm rác ở hàng dưới. Phải kiểm tra ownership trước khi loại trừ.

### SUP-R4 — khảo sát Y `[1450,1530)`

9 slot có thân quan sát: pose chính diện hai tay dang bên trái; tiếp theo là **bong bóng thoại có chữ `ビンゴ!!!`**; sau chữ là tám pose nhấc gối/đổi tay/đứng chính diện/ngửa đầu, pose cuối bao aura. Chữ là annotation riêng, không phải vùng thiếu của tóc hay FX cần ghép.

Thân bên trái nằm trong khoảng X=`[19,65)`; bong bóng thoại khoảng `[65,113)`; 8 thân tiếp theo trong `[119,460)`. Có thể là nhóm diễn xuất/taunt, nhưng nhãn hành động và timing cần Owner xác nhận. Không tự đặt nó thành win hoặc dance đã chốt.

## 10. ULTIMATES — 2 chuỗi beam lớn

### ULT-R1 — Y `[1597,1734)`

7 slot có thân quan sát: chuẩn bị có tia vàng thấp; hai aura rất lớn với tay dang; hai pose tay co/chuyển; pose tay phát cầu vàng; pose cuối có aura xanh và beam vàng-trắng khổng lồ hướng phải. Đầu beam có nhiều lớp vàng và lõi rất sáng, đuôi tỏa tia tại tay phát.

Trong cửa sổ `Rect(427,1597,333,137)`, foreground bbox đo được `Rect(427,1603,332,131)`. Đây là bbox trong cửa sổ, **chưa xác nhận là full-FX bbox** của slot cuối vì cần mask ownership riêng phía trái. Không dùng nó làm chuẩn canvas cuối cùng.

### ULT-R2 — Y `[1753,1884)`

9 slot có thân quan sát: lao chéo; lao ngang có điện/vệt cyan; đá ngang; hạ thấp/co thân; đứng thủ; phát sáng xanh lục quanh thân; đứng chuyển tay; đưa hai tay; cuối cùng aura xanh-trắng và beam xanh lục lớn hướng phải, lõi xanh rất nhạt.

Trong cửa sổ `Rect(416,1753,344,131)`, foreground bbox đo được `Rect(418,1753,341,131)`. Cũng là bbox cửa sổ, không phải full-FX bbox đã phê duyệt.

Hai beam không cùng màu hay hình dạng, không tái sử dụng bằng tint một cách mặc định. Dù gợi liên tưởng tên chiêu quen thuộc, sheet không ghi tên nên giữ ID trung tính. Không phát beam riêng như một frame làm thân biến mất, không neo theo đầu beam. Chiều dài FX cho thấy không được mặc định canvas Trunks `[320,256]` sẽ chứa đủ ở tỷ lệ nguồn.

## 11. Header, footer và dữ liệu không thuộc animation combat

- Portrait SSJB góc phải header là ảnh chân dung cắt, không phải pose đứng.
- Logo `DRAGON BALL SUPER` và logo chữ phong cách `LSW ...` góc phải INTRO là đồ trình bày. Phần chữ cách điệu còn lại không được dùng làm tên bộ công cụ/chiêu nếu chưa đọc chắc chắn.
- Footer bắt đầu bằng khung đen/cắt góc, dòng `Give Credits to:`. Các tên đọc được: `thekrillmaster`, `MajinVegeta95`, `Luka`, `Angryboy`, `Que`, `Extreme Butoden`, `DB Fighterz`.
- Logo `VORTEX`, chữ Nhật nhỏ phía trên; logo `DEVIANT ART` và dòng `thekrillmaster.deviantart.com`. Giữ nguyên credit nguồn trong hồ sơ, không tự khẳng định đây là giấy phép sử dụng.
- Bảng thống kê: `power SS`, `speed S`, `reach B` (glyph B cách điệu), `tech A`, `energy S`; dòng `Race / Classification: SAIYAN`. Đây là thông tin trình bày trên sheet, chưa phải thông số gameplay dự án.
- Góc dưới phải: tiêu đề `別の衣装`, `ALT Costumes/Palettes`, 12 mẫu đứng. Thứ tự quan sát: tóc đen/giáp xanh; tóc vàng/giáp xanh; tóc hồng-đỏ/giáp xanh; tóc xanh/giáp xanh; tóc đen/đồ xám; tóc cyan/đồ xám; tóc đen/thân trần; tóc xanh/thân trần; tóc vàng có điện hồng; tóc đen/áo xanh không giáp sáng; tóc đen/giáp tối; toàn thân tím-hồng. Đây là mô tả màu nhìn thấy, không tự gán tên biến hình/trang phục chính thức.
- 12 mẫu không chứng minh có đủ 12 bộ animation; không suy ra palette mapping chỉ từ tóc. Không đưa chúng vào roster như 12 nhân vật hoàn thiện.

## 12. Rủi ro xử lý đã nhận diện, chưa phải kết quả QA

1. **Key nền vàng:** giáp và tia vàng có sắc gần nền. Không dùng ngưỡng vàng rộng hoặc xóa mọi màu gần key toàn sheet. Đo pocket/edge trên từng nhóm trước khi chọn profile; màu nền trùng tuyệt đối foreground nếu có thì không thể suy ra chỉ bằng chroma.
2. **Ownership tự do:** nhiều pose sát nhau 1–3 px; có pixel lẻ, cung, vòng và đuôi đạn tách khỏi thân. Không grid-slice, không largest-component, không coi projection X là frame detector.
3. **Annotations:** nhãn đầu nhóm, gạch chân ATTACKS, thoại SUP-R4, logos/portrait/credits/ratings/variants cần inventory riêng. Không lọc trắng/đen toàn cục vì thân, outline và beam cũng dùng các màu đó.
4. **Khung động:** thân đứng mẫu 25×51 px, beam cuối dài hàng trăm px. Đo envelope với body anchor và cả hướng flip trước khi chọn canvas; không thu nhỏ tất cả chỉ để vừa khuôn cũ.
5. **Timeline:** sheet không có FPS, tick duration, event hit, số lần lặp, marker chia combo hoặc clip ID chính thức. Các hàng và số slot ở trên không xác nhận các thông số đó.
6. **Độ hoàn chỉnh:** chưa khẳng định đủ `idle/walk/run/jump/guard/attack_light/attack_heavy/power_up/aura_loop/hit/ko/win`. MOVEMENT không chứng minh đủ walk/run, DAMAGE chưa chứng minh full KO/recovery, taunt chưa chắc là win. Không tạo frame giả để lấp chỗ trống.
7. **Chất lượng:** chưa key hay xuất ảnh nên chưa có số `opaque_key_px`, pockets, spill, alpha-hardness sau xử lý; alpha=255 ở nguồn không phải chứng nhận tách nền đạt chuẩn. Chưa có filmstrip runtime hay Human Test.

## 13. Mốc đánh giá kiến trúc và bước tiếp theo

Owner xác nhận giữ mốc đánh giá lại sau khi asset, scene và UI hoàn thành để test thực tế. Rust và Godot là định hướng ứng viên, không phải quyết định cuối cùng. Phân tích này không chọn engine, không đổi backend hoặc setup pipeline.

Khi Owner yêu cầu thực thi, cần xác nhận phạm vi nhân vật/trạng thái (intro tóc đen có dùng không), nhóm clip mong muốn, timing và cách ghép projectile/beam, tỷ lệ hiển thị và bố cục scene. Chỉ hỏi những lựa chọn thực sự cần cho bước Owner yêu cầu; không yêu cầu chốt mọi thứ ngay ở giai đoạn đọc sheet.

Hồ sơ này là kiểm kê quan sát và đo nguồn. Chưa có per-pose ownership mask đầy đủ, chưa đếm frame runtime, chưa chứng minh thứ tự thời gian. Những giới hạn đó phải được giữ khi chuyển giao sang phiên khác.
