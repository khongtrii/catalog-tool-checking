# Catalog Price Checker

Webapp nhỏ để đối chiếu giá trong các file catalogue với file query giá theo một ngày chỉ định.

## Chạy ứng dụng

```powershell
uv sync
uv run streamlit run app.py
```

## Luồng sử dụng

1. Upload một file query giá `.xlsx`.
2. Chọn ngày cần kiểm tra.
3. Upload nhiều file catalogue `.xlsx`.
4. Chủ động chọn một hoặc nhiều sheet/REGION cần xử lý trong từng file. App không tự động chọn toàn bộ sheet.
5. Nhập `SUGGEST SITE` cho từng REGION.
6. Bấm **Xử lý và tạo file kết quả** rồi tải file ZIP kết quả.

Mỗi file catalogue tạo một sheet output. Các REGION được chọn trong cùng file được nối vào cùng sheet và giữ cột `REGION`.

File ZIP được chia thành `NON FOOD`, `FMCG`, `FRESH` và `OTHERS`. Kết quả catalogue được phân nhóm theo `DEPARTMENT` và fallback sang `DIVISION` khi cần. Giao diện có năm ô upload file bổ sung và tất cả đều không bắt buộc. Chỉ file được upload mới được xử lý: `6922_Vynamic` dùng `DEPT`, các file còn lại dùng `DIVISION`.

Giá query chỉ được chọn khi ngày kiểm tra nằm trong period tương ứng. Nếu cả giá KM và giá thường cùng hiệu lực thì giá KM được ưu tiên. Các KEY không có giá query hợp lệ bị loại. `MDT NOTE` là `đúng giá` khi giá catalogue bằng giá query, ngược lại là `lệch giá`.
