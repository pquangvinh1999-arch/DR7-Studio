# Sarcosuchus — master demo, chưa nghiệm thu

Ảnh gameplay: master-gameplay-v1.png. Bbox CanvasRect(89,190,157,34),canvas384×256,anchor[176,224],Nearest,alpha thân100%. Chiều ngang157px bằngSpinosaurus theo mốc đo đãOwnerchốt trong các task trước; không kéo giãn chiều cao thành74px. Góc3/4 nhìnphải, màuolive/xámthan là lựa chọn mỹ thuật.

Ảnh nguồn concept-v1.png do built-inimagegen sinh ở1536×1024,alpha0..254. Chuẩn bị kỹ thuật bằng prepare_master.py:alpha nguồn>=128thành255, bỏalpha còn lại; crop/nguyênpose/Nearest một scale, cănmedianthân tối trongcác cộtdày; khôngcắtchi,khôngvẽlạiRGB,khôngpalette/LUT/sharpen. Nativeoutput157×34,visible2943px,RGB2651,Sobel254.471 đo đúngCLI dựán. Sobel không phải verdict thẩm mỹ hay dung sai so245.516.

Đã mởcomparison-light/dark/checker.png tại1x và2xNearest. Chỉ mastertĩnh đểOwnerduyệt dáng/nhận diện/nét trước chọn độngtác. Chưa có clip/atlas/bundle/roster mới hoặc nghiệmthuengine choSarcosuchus;4charhiện hành giữ nguyên.

Cơ sở nhận diện tham khảo: https://australian.museum/about/organisation/media-centre/supercroc-unleashed/ và https://pubmed.ncbi.nlm.nih.gov/11679634/. Không dùng màuart hoặc tưthếđềxuất làm kếtluận khoahọc.
