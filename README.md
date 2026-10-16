# Catalog Price Checker

Webapp nhỏ để đối chiếu giá trong các file catalogue với file query giá theo một ngày chỉ định.

Ứng dụng có thể chạy trực tiếp bằng Python hoặc được đóng gói thành ứng dụng Windows local. Khi chạy bản Windows, dữ liệu Excel chỉ được xử lý trong bộ nhớ trên máy người dùng và không được gửi lên Streamlit Cloud hay API bên ngoài.

## Chạy ứng dụng

```powershell
uv sync
uv run streamlit run app.py
```

## Đóng gói ứng dụng Windows

Yêu cầu máy build là Windows 64-bit và đã cài `uv`. Chạy:

```powershell
.\scripts\build_windows.ps1
```

File chạy được tạo tại:

```text
dist\CatalogPriceChecker\CatalogPriceChecker.exe
```

PyInstaller tạo bản `onedir`. Script build tự tạo gói phân phối:

```text
dist\CatalogPriceChecker-windows-x64.zip
```

Gửi file ZIP này cho người dùng, không gửi riêng file `.exe` vì ứng dụng cần các DLL/runtime trong thư mục `_internal`.

## Sử dụng bản Windows

1. Giải nén thư mục được nhận.
2. Double-click `CatalogPriceChecker.exe`.
3. Ứng dụng tự chọn một cổng trống từ `8501` đến `8599` và mở trình duyệt tại `http://127.0.0.1:<port>`.
4. Giữ cửa sổ console trong khi sử dụng. Đóng cửa sổ này để dừng ứng dụng và giải phóng cổng.

Ứng dụng chỉ lắng nghe trên địa chỉ loopback `127.0.0.1`, vì vậy máy khác trong mạng không thể truy cập. App không cần internet sau khi đã được đóng gói. Mỗi file upload được giới hạn ở 20 MB và phải là workbook XLSX hợp lệ.

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
