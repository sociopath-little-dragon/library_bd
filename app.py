import customtkinter as ctk
from datetime import datetime, date
import db.db_funcs as db
from tkinter import messagebox, ttk
import threading
import sys

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("📚 Библиотечная система")
        self.geometry("900x600")
        self.minsize(900, 700)

        # Создаем сессию для работы с БД
        self.session = db.get_session()
        self.current_user = None  # Текущий авторизованный пользователь
        self.is_running = True  # Флаг для отслеживания состояния приложения

        self.setup_ui()

    def setup_ui(self):
        # Основной фрейм
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(title_frame, text="📚 Библиотечная система",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)

        # Статус авторизации
        self.auth_status_label = ctk.CTkLabel(title_frame,
                                              text="❌ Не авторизован",
                                              text_color="red",
                                              font=ctk.CTkFont(weight="bold"))
        self.auth_status_label.pack(pady=5)

        # Основной контент - два столбца
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Левый столбец - статистика
        left_column = ctk.CTkFrame(content_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Правый столбец - авторизация
        right_column = ctk.CTkFrame(content_frame)
        right_column.pack(side="right", fill="y", padx=(10, 0))

        self.setup_statistics_section(left_column)
        self.setup_auth_section(right_column)

        # Кнопка для перехода к полной версии (будет доступна после авторизации)
        self.full_version_btn = ctk.CTkButton(main_frame,
                                              text="📋 Перейти к полной версии",
                                              command=self.open_full_version,
                                              state="disabled",
                                              fg_color="#7209B7",
                                              hover_color="#560BAD")
        self.full_version_btn.pack(pady=10)

    def setup_statistics_section(self, parent):
        """Настройка секции статистики"""
        # Заголовок статистики
        ctk.CTkLabel(parent, text="📊 Статистика библиотеки",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # Контейнер для статистики
        self.stats_container = ctk.CTkFrame(parent)
        self.stats_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Загрузочный индикатор
        self.loading_label = ctk.CTkLabel(self.stats_container,
                                          text="🔄 Загрузка статистики...",
                                          font=ctk.CTkFont(size=14))
        self.loading_label.pack(pady=50)

        # Загружаем статистику в отдельном потоке
        threading.Thread(target=self.load_statistics, daemon=True).start()

    def setup_auth_section(self, parent):
        """Настройка секции авторизации"""
        ctk.CTkLabel(parent, text="🔐 Вход в систему",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Форма авторизации
        auth_form = ctk.CTkFrame(parent)
        auth_form.pack(fill="x", padx=10, pady=10)

        # Поле email
        ctk.CTkLabel(auth_form, text="Email:").pack(anchor="w", pady=(10, 0))
        self.auth_email = ctk.CTkEntry(auth_form, placeholder_text="example@library.ru")
        self.auth_email.pack(fill="x", padx=10, pady=5)

        # Поле пароля
        ctk.CTkLabel(auth_form, text="Пароль:").pack(anchor="w", pady=(10, 0))
        self.auth_password = ctk.CTkEntry(auth_form, placeholder_text="Пароль", show="•")
        self.auth_password.pack(fill="x", padx=10, pady=5)

        # Кнопка входа
        self.login_btn = ctk.CTkButton(auth_form, text="Войти",
                                       command=self.authenticate_user)
        self.login_btn.pack(pady=15)

        # Привязываем Enter к авторизации
        self.auth_password.bind("<Return>", lambda e: self.authenticate_user())

        # Информация о системе
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=20)

        ctk.CTkLabel(info_frame, text="ℹ️ Информация о системе:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        info_text = """
• Для доступа к функциям системы 
  требуется авторизация
• Доступ имеют только сотрудники 
  библиотеки
• По вопросам доступа обратитесь 
  к администратору
        """
        ctk.CTkLabel(info_frame, text=info_text, justify="left").pack(anchor="w", pady=10)

    def load_statistics(self):
        """Загрузка статистики в отдельном потоке"""
        try:
            # Проверяем, что приложение еще работает
            if not self.is_running:
                return

            # Получаем статистику
            readers_count = db.get_readers_count(self.session)
            books_count = db.get_books_count(self.session)
            active_loans = len(db.get_active_loans(self.session))
            unpaid_fines = len(db.get_unpaid_fines(self.session))

            # Проверяем again, что приложение еще работает
            if self.is_running:
                # Обновляем интерфейс в основном потоке
                self.after(0, self.display_statistics, readers_count, books_count, active_loans, unpaid_fines)

        except Exception as e:
            if self.is_running:
                self.after(0, self.show_error, f"Не удалось загрузить статистику: {e}")

    def display_statistics(self, readers, books, loans, fines):
        """Отображение статистики в интерфейсе"""
        # Проверяем, что окно еще существует
        if not self.is_running:
            return

        # Убираем индикатор загрузки
        self.loading_label.pack_forget()

        # Создаем сетку для статистики
        stats_grid = ctk.CTkFrame(self.stats_container)
        stats_grid.pack(fill="both", expand=True, padx=10, pady=10)

        # Настройка сетки
        for i in range(2):
            stats_grid.columnconfigure(i, weight=1)
        for i in range(2):
            stats_grid.rowconfigure(i, weight=1)

        # Статистические карточки
        stats_data = [
            ("👥 Читатели", readers, "#4CC9F0", "Общее количество зарегистрированных читателей"),
            ("📚 Книги", books, "#4361EE", "Всего книг в каталоге библиотеки"),
            ("📖 Активные выдачи", loans, "#F72585", "Книги на руках у читателей"),
            ("💰 Неоплаченные штрафы", fines, "#7209B7", "Суммарные непогашенные штрафы")
        ]

        for i, (title, count, color, description) in enumerate(stats_data):
            row = i // 2
            col = i % 2

            # Карточка статистики
            card = ctk.CTkFrame(stats_grid, fg_color=color, corner_radius=15)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Число
            count_label = ctk.CTkLabel(card, text=str(count),
                                       font=ctk.CTkFont(size=32, weight="bold"))
            count_label.pack(pady=(20, 5))

            # Заголовок
            title_label = ctk.CTkLabel(card, text=title,
                                       font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=5)

            # Описание
            desc_label = ctk.CTkLabel(card, text=description,
                                      font=ctk.CTkFont(size=12),
                                      wraplength=200)
            desc_label.pack(pady=(5, 20), padx=10)

    def authenticate_user(self):
        """Аутентификация пользователя"""
        email = self.auth_email.get().strip()
        password = self.auth_password.get().strip()

        if not email or not password:
            messagebox.showwarning("Предупреждение", "Введите email и пароль")
            return

        # Показываем индикатор загрузки
        self.login_btn.configure(text="🔄 Вход...", state="disabled")

        # Запускаем аутентификацию в отдельном потоке
        threading.Thread(target=self._authenticate_thread,
                         args=(email, password), daemon=True).start()

    def _authenticate_thread(self, email, password):
        """Поток для аутентификации"""
        try:
            result = db.authenticate_librarian(self.session, email, password)
            if self.is_running:
                self.after(0, self._handle_auth_result, result)
        except Exception as e:
            if self.is_running:
                self.after(0, self._handle_auth_error, e)

    def _handle_auth_result(self, user):
        """Обработка результата аутентификации"""
        if not self.is_running:
            return

        if user:
            self.current_user = user
            self.auth_status_label.configure(text=f"✅ Авторизован: {user.name}",
                                             text_color="green")

            # Активируем кнопку перехода к полной версии
            self.full_version_btn.configure(state="normal")

            # Меняем текст кнопки входа на "Выйти"
            self.login_btn.configure(text="Выйти",
                                     command=self.logout_user,
                                     fg_color="#F72585",
                                     hover_color="#B5179E")

            messagebox.showinfo("Успех", f"Добро пожаловать, {user.name}!")

            # Очищаем поля авторизации
            self.auth_email.delete(0, "end")
            self.auth_password.delete(0, "end")
        else:
            messagebox.showerror("Ошибка", "Неверный email или пароль")
            self.login_btn.configure(text="Войти", state="normal")

    def logout_user(self):
        """Выход пользователя из системы"""
        self.current_user = None
        self.auth_status_label.configure(text="❌ Не авторизован",
                                         text_color="red")

        # Деактивируем кнопку перехода к полной версии
        self.full_version_btn.configure(state="disabled")

        # Возвращаем кнопку входа в исходное состояние
        self.login_btn.configure(text="Войти",
                                 command=self.authenticate_user,
                                 fg_color=["#3B8ED0", "#1F6AA5"],
                                 hover_color=["#36719F", "#144870"])

        messagebox.showinfo("Выход", "Вы вышли из системы")

    def open_full_version(self):
        """Открытие полной версии приложения"""
        if not self.current_user:
            messagebox.showwarning("Ошибка", "Требуется авторизация")
            return

        # Устанавливаем флаг, что приложение закрывается
        self.is_running = False

        # Закрываем сессию БД
        if self.session:
            db.close_session(self.session)

        # Закрываем текущее окно
        self.destroy()

        # Запускаем полную версию
        full_app = FullLibraryApp(self.current_user)
        full_app.mainloop()

    def _handle_auth_error(self, error):
        """Обработка ошибки аутентификации"""
        if not self.is_running:
            return
        messagebox.showerror("Ошибка", f"Ошибка аутентификации: {error}")
        self.login_btn.configure(text="Войти", state="normal")

    def show_error(self, message):
        """Показать сообщение об ошибке"""
        if not self.is_running:
            return
        self.loading_label.configure(text=f"❌ {message}", text_color="red")

    def on_closing(self):
        """Обработчик закрытия окна"""
        self.is_running = False
        if hasattr(self, 'session'):
            db.close_session(self.session)
        self.destroy()


class FullLibraryApp(ctk.CTk):
    """Полная версия приложения с вкладками"""

    def __init__(self, user):
        super().__init__()

        self.current_user = user
        self.session = db.get_session()
        self.is_running = True

        self.title(f"📚 Библиотечная система - {user.name}")
        self.geometry("1200x500")
        self.minsize(1000, 600)

        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()

    def setup_ui(self):
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Добавляем вкладки
        self.tabview.add("Главная")
        self.tabview.add("Читатели")
        self.tabview.add("Книги")
        self.tabview.add("Выдачи")
        self.tabview.add("Штрафы")
        self.tabview.add("Библиотекари")

        # Заголовок с информацией о пользователе
        user_info = ctk.CTkFrame(self.tabview.tab("Главная"))
        user_info.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(user_info, text=f"👤 Вы вошли как: {self.current_user.name}",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")

        ctk.CTkLabel(user_info, text=f"📧 {self.current_user.email}",
                     font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 0))

        if self.current_user.position:
            ctk.CTkLabel(user_info, text=f"💼 {self.current_user.position}",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 0))

        # Кнопка выхода
        ctk.CTkButton(user_info, text="🚪 Выйти",
                      command=self.logout,
                      fg_color="#F72585",
                      hover_color="#B5179E").pack(side="right")

        # Простой контент для каждой вкладки
        for tab_name in ["Читатели", "Книги", "Выдачи", "Штрафы", "Библиотекари"]:
            tab = self.tabview.tab(tab_name)
            ctk.CTkLabel(tab, text=f"Раздел '{tab_name}' - в разработке",
                         font=ctk.CTkFont(size=16)).pack(pady=50)

            ctk.CTkLabel(tab, text="Здесь будет функционал для управления этой частью системы",
                         font=ctk.CTkFont(size=12)).pack(pady=10)

        self.setup_readers_tab()

    def logout(self):
        """Выход и возврат к экрану авторизации"""
        self.is_running = False
        if self.session:
            db.close_session(self.session)
        self.destroy()

        # Запускаем новое окно авторизации
        auth_app = LibraryApp()
        auth_app.mainloop()

    def on_closing(self):
        """Обработчик закрытия окна"""
        self.is_running = False
        if hasattr(self, 'session'):
            db.close_session(self.session)
        self.destroy()
        sys.exit(0)

    def setup_readers_tab(self):
        """Настройка вкладки Читатели"""
        tab = self.tabview.tab("Читатели")

        # Очищаем вкладку от старых элементов
        for widget in tab.winfo_children():
            widget.destroy()

        # Основной контейнер
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая панель - управление
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)

        # Правая панель - список читателей
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, pady=10)

        # === ЛЕВАЯ ПАНЕЛЬ - УПРАВЛЕНИЕ ===
        ctk.CTkLabel(left_panel, text="Управление читателями",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Фильтры
        filter_frame = ctk.CTkFrame(left_panel)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="Фильтр читателей:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.reader_filter = ctk.CTkComboBox(filter_frame,
                                             values=[
                                                 "Все читатели",
                                                 "С книгами на руках",
                                                 "С просрочками",
                                                 "Без активных выдач"
                                             ],
                                             command=self.apply_reader_filter)
        self.reader_filter.set("Все читатели")
        self.reader_filter.pack(fill="x", pady=5)

        # Поиск
        search_frame = ctk.CTkFrame(left_panel)
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Поиск:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.reader_search = ctk.CTkEntry(search_frame, placeholder_text="Имя, email или телефон")
        self.reader_search.pack(fill="x", pady=5)
        self.reader_search.bind("<KeyRelease>", self.search_readers)

        # Кнопки управления
        btn_frame = ctk.CTkFrame(left_panel)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить читателя",
                      command=self.show_add_reader_dialog).pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Изменить выделенного",
                      command=self.show_edit_reader_dialog,
                      fg_color="#4CC9F0").pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Удалить выделенного",
                      command=self.delete_reader,
                      fg_color="#F72585").pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Обновить список",
                      command=self.load_readers).pack(fill="x", pady=5)

        # === ПРАВАЯ ПАНЕЛЬ - СПИСОК ЧИТАТЕЛЕЙ ===
        # Заголовок
        header_frame = ctk.CTkFrame(right_panel)
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header_frame, text="Список читателей",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        self.readers_count_label = ctk.CTkLabel(header_frame, text="Всего: 0")
        self.readers_count_label.pack(side="right")

        # Таблица читателей
        table_frame = ctk.CTkFrame(right_panel)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Создаем Treeview с полосой прокрутки
        self.readers_tree = ttk.Treeview(table_frame,
                                         columns=("ID", "Name", "Email", "Phone", "RegDate", "ActiveLoans", "Overdue"),
                                         show="headings")

        # Настраиваем колонки
        columns_config = [
            ("ID", "ID", 50),
            ("Name", "ФИО", 200),
            ("Email", "Email", 150),
            ("Phone", "Телефон", 120),
            ("RegDate", "Дата регистрации", 120),
            ("ActiveLoans", "Активные выдачи", 120),
            ("Overdue", "Просрочки", 80)
        ]

        for col_id, heading, width in columns_config:
            self.readers_tree.heading(col_id, text=heading)
            self.readers_tree.column(col_id, width=width)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.readers_tree.yview)
        self.readers_tree.configure(yscrollcommand=scrollbar.set)

        self.readers_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Двойной клик для редактирования
        self.readers_tree.bind("<Double-1>", lambda e: self.show_edit_reader_dialog())

        # Загружаем данные
        self.load_readers()

    def apply_reader_filter(self, choice):
        """Применение фильтра к списку читателей"""
        if not hasattr(self, 'all_readers'):
            return

        filtered_readers = []

        if choice == "Все читатели":
            filtered_readers = self.all_readers
        elif choice == "С книгами на руках":
            for reader in self.all_readers:
                if reader.get('active_loans', 0) > 0:
                    filtered_readers.append(reader)
        elif choice == "С просрочками":
            for reader in self.all_readers:
                if reader.get('overdue', 0) > 0:
                    filtered_readers.append(reader)
        elif choice == "Без активных выдач":
            for reader in self.all_readers:
                if reader.get('active_loans', 0) == 0:
                    filtered_readers.append(reader)

        self.display_readers(filtered_readers)

    def search_readers(self, event=None):
        """Поиск читателей"""
        search_term = self.reader_search.get().strip().lower()
        if not search_term:
            self.apply_reader_filter(self.reader_filter.get())
            return

        filtered_readers = []
        for reader in self.all_readers:
            if (search_term in reader['name'].lower() or
                    search_term in reader['email'].lower() or
                    (reader['phone'] and search_term in reader['phone'])):
                filtered_readers.append(reader)

        self.display_readers(filtered_readers)

    def load_readers(self):
        """Загрузка списка читателей"""
        try:
            # Получаем всех читателей
            readers = db.get_all_readers(self.session)

            # Собираем расширенную информацию о каждом читателе
            self.all_readers = []
            for reader in readers:
                # Получаем активные выдачи
                active_loans = db.get_loans_by_reader(self.session, reader.id, active_only=True)

                # Считаем просрочки
                overdue_count = 0
                for loan in active_loans:
                    if loan.return_date < date.today():
                        overdue_count += 1

                self.all_readers.append({
                    'id': reader.id,
                    'name': reader.name,
                    'email': reader.email,
                    'phone': reader.phone_number,
                    'reg_date': reader.registration_date,
                    'active_loans': len(active_loans),
                    'overdue': overdue_count
                })

            # Применяем текущий фильтр
            self.apply_reader_filter(self.reader_filter.get())

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить читателей: {e}")

    def display_readers(self, readers):
        """Отображение читателей в таблице"""
        # Очищаем таблицу
        for item in self.readers_tree.get_children():
            self.readers_tree.delete(item)

        # Заполняем данными
        for reader in readers:
            self.readers_tree.insert("", "end", values=(
                reader['id'],
                reader['name'],
                reader['email'],
                reader['phone'] or "-",
                reader['reg_date'].strftime("%d.%m.%Y"),
                reader['active_loans'],
                reader['overdue']
            ))

        # Обновляем счетчик
        self.readers_count_label.configure(text=f"Всего: {len(readers)}")

    def show_add_reader_dialog(self):
        """Диалог добавления читателя"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить читателя")
        dialog.geometry("450x450")  # Увеличил размер окна
        dialog.minsize(450, 400)  # Минимальный размер
        dialog.transient(self)
        dialog.grab_set()

        # Центрируем окно
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="Добавление нового читателя",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Поля формы
        ctk.CTkLabel(form_frame, text="ФИО:*").pack(anchor="w", pady=(10, 0))
        name_entry = ctk.CTkEntry(form_frame, height=35)
        name_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Email:*").pack(anchor="w", pady=(10, 0))
        email_entry = ctk.CTkEntry(form_frame, height=35)
        email_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Телефон:").pack(anchor="w", pady=(10, 0))
        phone_entry = ctk.CTkEntry(form_frame, height=35)
        phone_entry.pack(fill="x", pady=5)

        def save_reader():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            phone = phone_entry.get().strip() or None

            if not name or not email:
                messagebox.showwarning("Ошибка", "Заполните обязательные поля (ФИО и Email)")
                return

            try:
                result = db.create_reader(self.session, name, email, phone)
                if result:
                    messagebox.showinfo("Успех", f"Читатель {name} успешно добавлен!")
                    dialog.destroy()
                    self.load_readers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить читателя: {e}")

        # Кнопки в отдельном фрейме с правильным размещением
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(btn_frame, text="Отмена",
                      command=dialog.destroy,
                      width=100,
                      fg_color="gray").pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Сохранить",
                      command=save_reader,
                      width=100).pack(side="right")

    def show_edit_reader_dialog(self):
        """Диалог редактирования читателя"""
        selected = self.readers_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите читателя для редактирования")
            return

        item = self.readers_tree.item(selected[0])
        reader_id = item['values'][0]

        try:
            reader = db.get_reader_by_id(self.session, reader_id)
            if not reader:
                messagebox.showerror("Ошибка", "Читатель не найден")
                return

            dialog = ctk.CTkToplevel(self)
            dialog.title("Редактировать читателя")
            dialog.geometry("450x450")
            dialog.minsize(450, 400)
            dialog.transient(self)
            dialog.grab_set()

            # Центрируем окно
            dialog.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
            y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(dialog, text="Редактирование читателя",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

            form_frame = ctk.CTkFrame(dialog)
            form_frame.pack(fill="both", expand=True, padx=20, pady=10)

            # Поля формы
            ctk.CTkLabel(form_frame, text="ФИО:*").pack(anchor="w", pady=(10, 0))
            name_entry = ctk.CTkEntry(form_frame, height=35)
            name_entry.insert(0, reader.name)
            name_entry.pack(fill="x", pady=5)

            ctk.CTkLabel(form_frame, text="Email:*").pack(anchor="w", pady=(10, 0))
            email_entry = ctk.CTkEntry(form_frame, height=35)
            email_entry.insert(0, reader.email)
            email_entry.pack(fill="x", pady=5)

            ctk.CTkLabel(form_frame, text="Телефон:").pack(anchor="w", pady=(10, 0))
            phone_entry = ctk.CTkEntry(form_frame, height=35)
            if reader.phone_number:
                phone_entry.insert(0, reader.phone_number)
            phone_entry.pack(fill="x", pady=5)

            def save_changes():
                name = name_entry.get().strip()
                email = email_entry.get().strip()
                phone = phone_entry.get().strip() or None

                if not name or not email:
                    messagebox.showwarning("Ошибка", "Заполните обязательные поля (ФИО и Email)")
                    return

                try:
                    result = db.update_reader(self.session, reader_id, name=name, email=email, phone_number=phone)
                    if result:
                        messagebox.showinfo("Успех", "Данные читателя обновлены!")
                        dialog.destroy()
                        self.load_readers()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось обновить данные: {e}")

            # Кнопки в отдельном фрейме с правильным размещением
            btn_frame = ctk.CTkFrame(dialog)
            btn_frame.pack(fill="x", padx=20, pady=15)

            ctk.CTkButton(btn_frame, text="Отмена",
                          command=dialog.destroy,
                          width=100,
                          fg_color="gray").pack(side="left", padx=(0, 10))

            ctk.CTkButton(btn_frame, text="Сохранить",
                          command=save_changes,
                          width=100).pack(side="right")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")

    def delete_reader(self):
        """Удаление читателя"""
        selected = self.readers_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите читателя для удаления")
            return

        item = self.readers_tree.item(selected[0])
        reader_id = item['values'][0]
        reader_name = item['values'][1]

        # Проверяем активные выдачи
        try:
            active_loans = db.get_loans_by_reader(self.session, reader_id, active_only=True)
            if active_loans:
                messagebox.showerror("Ошибка",
                                     f"Нельзя удалить читателя {reader_name}!\n"
                                     f"У него есть активные выдачи книг.")
                return
        except:
            pass

        # Подтверждение удаления
        if not messagebox.askyesno("Подтверждение",
                                   f"Вы уверены, что хотите удалить читателя {reader_name}?"):
            return

        try:
            if db.delete_reader(self.session, reader_id):
                messagebox.showinfo("Успех", f"Читатель {reader_name} удален")
                self.load_readers()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить читателя: {e}")


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()