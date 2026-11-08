# 🌸 Hướng dẫn Đóng góp (Contributing Guidelines)

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án **SakuraBot**! Mọi sự đóng góp của bạn, dù là báo lỗi, đề xuất tính năng mới hay gửi Pull Request, đều rất được hoan nghênh.

---

## 🛠️ Quy trình Đóng góp

### 1. Báo cáo lỗi (Bug Reports)
Nếu bạn phát hiện lỗi trong quá trình sử dụng:
1. Kiểm tra mục **Issues** trên GitHub để xem lỗi đã được báo cáo chưa.
2. Nếu chưa, tạo một **New Issue** với tiêu đề rõ ràng.
3. Cung cấp:
   - Mô tả chi tiết về lỗi gặp phải.
   - Các bước để tái hiện lỗi.
   - Ảnh chụp màn hình hoặc log lỗi trong terminal (lưu ý che token/thông tin cá nhân).
   - Phiên bản Python và hệ điều hành bạn đang sử dụng.

### 2. Đề xuất tính năng mới (Feature Requests)
Bạn có ý tưởng hay để SakuraBot thông minh và phong phú hơn?
- Hãy mở một **Issue** với nhãn `enhancement`.
- Trình bày rõ tính năng cần thêm và lợi ích mang lại cho người dùng.

### 3. Gửi Pull Request (PR)
1. **Fork** repository này về tài khoản GitHub của bạn.
2. Tạo branch mới cho tính năng của bạn:
   ```bash
   git checkout -b feature/ten-tinh-nang
   ```
3. Thực hiện thay đổi, tuân thủ phong cách code:
   - Đặt tên biến và hàm có ý nghĩa, dễ đọc.
   - Giữ lại hoặc bổ sung các chú thích (docstring/comments) khi cần.
   - Không commit các file chứa token cá nhân, file `.env`, database `.db`.
4. Commit thay đổi:
   ```bash
   git commit -m "feat: thêm tính năng mới cho SakuraBot"
   ```
5. Đẩy lên repository của bạn:
   ```bash
   git push origin feature/ten-tinh-nang
   ```
6. Mở **Pull Request** về nhánh `main` của repository chính và mô tả ngắn gọn nội dung đã làm.

---

🌸 Chúc bạn có trải nghiệm tuyệt vời khi phát triển cùng cộng đồng **SakuraBot**!
