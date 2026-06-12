def _build_hastad_tab(self):
        top = self._card(
            self.tab_hastad,
            "Håstad Broadcast Attack: cùng bản rõ gửi cho nhiều người",
            "Bạn nhập thông điệp dạng chữ. Chương trình tự chuyển sang số m, gửi cho e người nhận, rồi dùng CRT để tấn công.",
        )
        top.pack(fill="x", pady=8)