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
        self.setup_books_tab()

    def setup_books_tab(self):
        """Настройка вкладки Книги с двумя режимами"""
        tab = self.tabview.tab("Книги")

        # Основной контейнер
        main_frame = ctk.CTkFrame(tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Переключатель режимов
        mode_frame = ctk.CTkFrame(main_frame)
        mode_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mode_frame, text="Режим просмотра:",
                     font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))

        self.books_mode = ctk.StringVar(value="books")
        ctk.CTkRadioButton(mode_frame, text="📚 Обзор книг",
                           variable=self.books_mode, value="books",
                           command=self.switch_books_mode).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_frame, text="📖 Управление экземплярами",
                           variable=self.books_mode, value="copies",
                           command=self.switch_books_mode).pack(side="left")

        # Контейнер для контента (будет меняться в зависимости от режима)
        self.books_content_frame = ctk.CTkFrame(main_frame)
        self.books_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Инициализируем оба режима, но показываем только первый
        self.setup_books_mode()
        self.setup_copies_mode()

        # Показываем начальный режим
        self.switch_books_mode()

    def setup_books_mode(self):
        """Режим обзора книг"""
        self.books_frame = ctk.CTkFrame(self.books_content_frame)

        # Левая панель - управление
        left_panel = ctk.CTkFrame(self.books_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)

        # Правая панель - список книг
        right_panel = ctk.CTkFrame(self.books_frame)
        right_panel.pack(side="right", fill="both", expand=True, pady=10)

        # === ЛЕВАЯ ПАНЕЛЬ - УПРАВЛЕНИЕ ===
        ctk.CTkLabel(left_panel, text="Управление книгами",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Фильтры
        filter_frame = ctk.CTkFrame(left_panel)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="Фильтр по наличию:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.books_filter = ctk.CTkComboBox(filter_frame,
                                            values=[
                                                "Все книги",
                                                "Есть в наличии",
                                                "Нет в наличии",
                                                "Мало экземпляров (1-2)"
                                            ],
                                            command=self.apply_books_filter)
        self.books_filter.set("Все книги")
        self.books_filter.pack(fill="x", pady=5)

        # Поиск
        search_frame = ctk.CTkFrame(left_panel)
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Поиск:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.books_search = ctk.CTkEntry(search_frame, placeholder_text="Название, автор, ISBN")
        self.books_search.pack(fill="x", pady=5)
        self.books_search.bind("<KeyRelease>", self.search_books)

        # Кнопки управления
        btn_frame = ctk.CTkFrame(left_panel)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить книгу",
                      command=self.show_add_book_dialog).pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Добавить экземпляр",
                      command=self.show_add_copy_dialog,
                      fg_color="#4CC9F0").pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Изменить книгу",
                      command=self.show_edit_book_dialog).pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Удалить книгу",
                      command=self.delete_book).pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Обновить список",
                      command=self.load_books).pack(fill="x", pady=5)


        # === ПРАВАЯ ПАНЕЛЬ - СПИСОК КНИГ ===
        header_frame = ctk.CTkFrame(right_panel)
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header_frame, text="Список книг",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        self.books_count_label = ctk.CTkLabel(header_frame, text="Всего: 0")
        self.books_count_label.pack(side="right")

        # Таблица книг
        table_frame = ctk.CTkFrame(right_panel)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.books_tree = ttk.Treeview(table_frame,
                                       columns=("ID", "Title", "Author", "ISBN", "Year",
                                                "TotalCopies", "AvailableCopies", "Genre"),
                                       show="headings")

        columns_config = [
            ("ID", "ID", 50),
            ("Title", "Название", 200),
            ("Author", "Автор", 150),
            ("ISBN", "ISBN", 120),
            ("Year", "Год", 80),
            ("TotalCopies", "Всего экз.", 100),
            ("AvailableCopies", "В наличии", 100),
            ("Genre", "Жанр", 120)
        ]

        for col_id, heading, width in columns_config:
            self.books_tree.heading(col_id, text=heading)
            self.books_tree.column(col_id, width=width)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=scrollbar.set)

        self.books_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Двойной клик для редактирования
        self.books_tree.bind("<Double-1>", lambda e: self.show_edit_book_dialog())

    def setup_copies_mode(self):
        """Режим управления экземплярами"""
        self.copies_frame = ctk.CTkFrame(self.books_content_frame)

        # Левая панель - управление
        left_panel = ctk.CTkFrame(self.copies_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)

        # Правая панель - список экземпляров
        right_panel = ctk.CTkFrame(self.copies_frame)
        right_panel.pack(side="right", fill="both", expand=True, pady=10)

        # === ЛЕВАЯ ПАНЕЛЬ - УПРАВЛЕНИЕ ===
        ctk.CTkLabel(left_panel, text="Управление экземплярами",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Фильтры статуса
        filter_frame = ctk.CTkFrame(left_panel)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="Фильтр по статусу:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.copies_filter = ctk.CTkComboBox(filter_frame,
                                             values=[
                                                 "Все экземпляры",
                                                 "В наличии",
                                                 "На руках",
                                                 "Просрочены",
                                                 "Списаны"
                                             ],
                                             command=self.apply_copies_filter)
        self.copies_filter.set("Все экземпляры")
        self.copies_filter.pack(fill="x", pady=5)

        # Поиск
        search_frame = ctk.CTkFrame(left_panel)
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Поиск:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))

        self.copies_search = ctk.CTkEntry(search_frame, placeholder_text="Название, инвентарный номер")
        self.copies_search.pack(fill="x", pady=5)
        self.copies_search.bind("<KeyRelease>", self.search_copies)

        # Кнопки управления
        btn_frame = ctk.CTkFrame(left_panel)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить экземпляр",
                      command=self.show_add_copy_dialog).pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Изменить статус",
                      command=self.show_change_copy_status_dialog,
                      fg_color="#4CC9F0").pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Списать экземпляр",
                      command=self.write_off_copy,
                      fg_color="#F72585").pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Обновить список",
                      command=self.load_book_copies).pack(fill="x", pady=5)

        # === ПРАВАЯ ПАНЕЛЬ - СПИСОК ЭКЗЕМПЛЯРОВ ===
        header_frame = ctk.CTkFrame(right_panel)
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header_frame, text="Список экземпляров",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        self.copies_count_label = ctk.CTkLabel(header_frame, text="Всего: 0")
        self.copies_count_label.pack(side="right")

        # Таблица экземпляров
        table_frame = ctk.CTkFrame(right_panel)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.copies_tree = ttk.Treeview(table_frame,
                                        columns=("ID", "InvNumber", "BookTitle", "Author",
                                                 "Status", "DueDate", "Reader", "Condition"),
                                        show="headings")

        columns_config = [
            ("ID", "ID", 50),
            ("InvNumber", "Инв. номер", 120),
            ("BookTitle", "Название книги", 200),
            ("Author", "Автор", 150),
            ("Status", "Статус", 120),
            ("DueDate", "Срок возврата", 120),
            ("Reader", "Читатель", 150),
            ("Condition", "Состояние", 100)
        ]

        for col_id, heading, width in columns_config:
            self.copies_tree.heading(col_id, text=heading)
            self.copies_tree.column(col_id, width=width)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.copies_tree.yview)
        self.copies_tree.configure(yscrollcommand=scrollbar.set)

        self.copies_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def switch_books_mode(self):
        """Переключение между режимами книг и экземпляров"""
        mode = self.books_mode.get()

        # Скрываем все фреймы
        self.books_frame.pack_forget()
        self.copies_frame.pack_forget()

        # Показываем нужный фрейм
        if mode == "books":
            self.books_frame.pack(fill="both", expand=True)
            self.load_books()
        else:
            self.copies_frame.pack(fill="both", expand=True)
            self.load_book_copies()

    def load_books(self):
        """Загрузка списка книг с информацией об экземплярах"""
        try:
            books = db.get_all_books(self.session)
            self.all_books = []

            for book in books:
                # Получаем информацию об экземплярах
                copies = db.get_copies_by_book(self.session, book.id)
                total_copies = len(copies)
                available_copies = len(
                    [c for c in copies if c.available == True])  # Используем поле available вместо status

                # Получаем жанры книги
                genres = book.genres
                genre_names = [genre.name for genre in genres] if genres else []
                genre_display = ", ".join(genre_names) if genre_names else "Не указан"

                self.all_books.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'year': book.publish_year,
                    'genre': genre_display,  # Теперь это строка с названиями жанров
                    'total_copies': total_copies,
                    'available_copies': available_copies
                })

            self.apply_books_filter(self.books_filter.get())

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить книги: {e}")

    def apply_books_filter(self, choice):
        """Применение фильтра к списку книг"""
        if not hasattr(self, 'all_books'):
            return

        filtered_books = []

        if choice == "Все книги":
            filtered_books = self.all_books
        elif choice == "Есть в наличии":
            filtered_books = [b for b in self.all_books if b['available_copies'] > 0]
        elif choice == "Нет в наличии":
            filtered_books = [b for b in self.all_books if b['available_copies'] == 0]
        elif choice == "Мало экземпляров (1-2)":
            filtered_books = [b for b in self.all_books if 1 <= b['available_copies'] <= 2]

        self.display_books(filtered_books)

    def search_books(self, event=None):
        """Поиск книг"""
        search_term = self.books_search.get().strip().lower()
        if not search_term:
            self.apply_books_filter(self.books_filter.get())
            return

        filtered_books = []
        for book in self.all_books:
            if (search_term in book['title'].lower() or
                    search_term in book['author'].lower() or
                    (book['isbn'] and search_term in book['isbn'].lower()) or
                    (book['genre'] and search_term in book['genre'].lower())):
                filtered_books.append(book)

        self.display_books(filtered_books)

    def display_books(self, books):
        """Отображение книг в таблице"""
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)

        for book in books:
            self.books_tree.insert("", "end", values=(
                book['id'],
                book['title'],
                book['author'],
                book['isbn'] or "-",
                book['year'] or "-",
                book['total_copies'],
                book['available_copies'],
                book['genre'] or "-"
            ))

        self.books_count_label.configure(text=f"Всего: {len(books)}")

    def load_book_copies(self):
        """Загрузка списка экземпляров книг"""
        try:
            copies = db.get_all_book_copies(self.session)
            self.all_copies = []

            for copy in copies:
                book = db.get_book_by_id(self.session, copy.book_id)
                reader_name = "-"
                due_date = "-"

                # Если книга выдана, получаем информацию о читателе
                if not copy.available:  # Используем поле available
                    loan = db.get_active_loan_by_copy(self.session, copy.id)
                    if loan:
                        reader = db.get_reader_by_id(self.session, loan.reader_id)
                        reader_name = reader.name if reader else "-"
                        due_date = loan.return_date.strftime("%d.%m.%Y") if loan.return_date else "-"

                # Определяем статус текстом
                if copy.available:
                    status_text = "В наличии"
                else:
                    # Проверяем просрочку
                    loan = db.get_active_loan_by_copy(self.session, copy.id)
                    if loan and loan.return_date and loan.return_date < date.today():
                        status_text = "Просрочена"
                    else:
                        status_text = "На руках"

                self.all_copies.append({
                    'id': copy.id,
                    'inventory_number': copy.inventory_number,
                    'book_title': book.title if book else "Неизвестно",
                    'author': book.author if book else "Неизвестно",
                    'status': status_text,
                    'due_date': due_date,
                    'reader': reader_name,
                    'condition': copy.condition,
                    'copy_obj': copy
                })

            self.apply_copies_filter(self.copies_filter.get())

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить экземпляры: {e}")

    def get_copy_status_text(self, status):
        """Получение читаемого текста статуса"""
        status_map = {
            'available': 'В наличии',
            'borrowed': 'На руках',
            'overdue': 'Просрочена',
            'written_off': 'Списана',
            'repair': 'На ремонте'
        }
        return status_map.get(status, status)

    def apply_copies_filter(self, choice):
        """Применение фильтра к списку экземпляров"""
        if not hasattr(self, 'all_copies'):
            return

        filtered_copies = []

        if choice == "Все экземпляры":
            filtered_copies = self.all_copies
        elif choice == "В наличии":
            filtered_copies = [c for c in self.all_copies if c['copy_obj'].status == 'available']
        elif choice == "На руках":
            filtered_copies = [c for c in self.all_copies if c['copy_obj'].status == 'borrowed']
        elif choice == "Просрочены":
            filtered_copies = [c for c in self.all_copies if c['copy_obj'].status == 'overdue']
        elif choice == "Списаны":
            filtered_copies = [c for c in self.all_copies if c['copy_obj'].status == 'written_off']

        self.display_copies(filtered_copies)

    def search_copies(self, event=None):
        """Поиск экземпляров"""
        search_term = self.copies_search.get().strip().lower()
        if not search_term:
            self.apply_copies_filter(self.copies_filter.get())
            return

        filtered_copies = []
        for copy in self.all_copies:
            if (search_term in copy['book_title'].lower() or
                    search_term in copy['inventory_number'].lower()):
                filtered_copies.append(copy)

        self.display_copies(filtered_copies)

    def display_copies(self, copies):
        """Отображение экземпляров в таблице"""
        for item in self.copies_tree.get_children():
            self.copies_tree.delete(item)

        for copy in copies:
            self.copies_tree.insert("", "end", values=(
                copy['id'],
                copy['inventory_number'],
                copy['book_title'],
                copy['author'],
                copy['status'],
                copy['due_date'],
                copy['reader'],
                copy['condition']
            ))

        self.copies_count_label.configure(text=f"Всего: {len(copies)}")


    def show_add_book_dialog(self):
        """Диалог добавления книги"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить книгу")
        dialog.geometry("500x650")
        dialog.minsize(500, 700)
        dialog.transient(self)
        dialog.grab_set()

        # Центрируем окно
        self.center_dialog(dialog)

        # Главный контейнер с вертикальным распределением
        main_container = ctk.CTkFrame(dialog)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # Заголовок
        ctk.CTkLabel(main_container, text="Добавление новой книги",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # Прокручиваемая область для формы
        form_scrollable = ctk.CTkScrollableFrame(main_container)
        form_scrollable.pack(fill="both", expand=True)

        # Поля формы
        fields = [
            ("Название:*", "title"),
            ("Автор:*", "author"),
            ("ISBN:", "isbn"),
            ("Год издания:", "year"),
            ("Описание:", "description")
        ]

        entries = {}
        for label, key in fields:
            ctk.CTkLabel(form_scrollable, text=label).pack(anchor="w", pady=(10, 0))
            if key == "description":
                entry = ctk.CTkTextbox(form_scrollable, height=80)
                entry.pack(fill="x", pady=5)
            else:
                entry = ctk.CTkEntry(form_scrollable, height=35)
                entry.pack(fill="x", pady=5)
            entries[key] = entry

        # Поле для выбора жанров (несколько)
        ctk.CTkLabel(form_scrollable, text="Жанры:").pack(anchor="w", pady=(10, 0))

        # Создаем скроллируемый фрейм для чекбоксов
        genres_scrollable = ctk.CTkScrollableFrame(
            form_scrollable,
            height=120,
            fg_color=("gray80", "gray20")
        )
        genres_scrollable.pack(fill="x", pady=5)

        # Получаем список жанров из базы данных
        genres = db.get_all_genres(self.session)
        genre_vars = {}

        # Создаем чекбоксы для каждого жанра
        for genre in genres:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(
                genres_scrollable,
                text=genre.name,
                variable=var
            )
            chk.pack(anchor="w", pady=2)
            genre_vars[genre.id] = var

        entries['genres'] = genre_vars

        # Функция сохранения книги
        def save_book():
            try:
                title = entries['title'].get().strip()
                author = entries['author'].get().strip()

                if not title or not author:
                    messagebox.showwarning("Ошибка", "Заполните обязательные поля (Название и Автор)")
                    return

                # Создаем книгу
                book_data = {
                    'title': title,
                    'author': author,
                    'isbn': entries['isbn'].get().strip() or None,
                    'publication_year': int(entries['year'].get()) if entries['year'].get().strip() else None,
                    'description': entries['description'].get("1.0", "end-1c").strip() or None
                }

                result = db.create_book(self.session, **book_data)
                if result:
                    # Добавляем выбранные жанры к книге
                    selected_genre_vars = entries['genres']
                    added_genres_count = 0

                    for genre_id, var in selected_genre_vars.items():
                        if var.get():
                            success = db.add_genre_to_book(self.session, result.id, genre_id)
                            if success:
                                added_genres_count += 1

                    success_message = f"Книга '{title}' успешно добавлена!"
                    if added_genres_count > 0:
                        success_message += f"\nДобавлено жанров: {added_genres_count}"

                    messagebox.showinfo("Успех", success_message)
                    dialog.destroy()
                    self.load_books()

            except ValueError as e:
                if "year" in str(e).lower():
                    messagebox.showerror("Ошибка", "Год издания должен быть числом")
                else:
                    messagebox.showerror("Ошибка", f"Ошибка в данных: {e}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить книгу: {e}")

        # Фрейм для кнопок (вне прокручиваемой области)
        btn_frame = ctk.CTkFrame(main_container)
        btn_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkButton(btn_frame, text="Отмена",
                      command=dialog.destroy,
                      width=100,
                      fg_color="gray").pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Сохранить",
                      command=save_book,
                      width=100).pack(side="right")

    def show_add_copy_dialog(self):
        """Диалог добавления экземпляра"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить экземпляр")
        dialog.geometry("450x500")  # Увеличил высоту для лучшего отображения
        dialog.minsize(450, 500)
        dialog.transient(self)
        dialog.grab_set()

        self.center_dialog(dialog)

        # Главный контейнер
        main_container = ctk.CTkFrame(dialog)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(main_container, text="Добавление экземпляра книги",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # Прокручиваемая область для формы
        form_scrollable = ctk.CTkScrollableFrame(main_container)
        form_scrollable.pack(fill="both", expand=True)

        # Выбор книги
        ctk.CTkLabel(form_scrollable, text="Книга:*").pack(anchor="w", pady=(10, 0))

        # Получаем список книг для выбора
        books = db.get_all_books(self.session)
        book_options = [f"{book.title} ({book.author})" for book in books]
        book_ids = [book.id for book in books]

        # Создаем словарь для быстрого поиска ID по отображаемому тексту
        book_mapping = {f"{book.title} ({book.author})": book.id for book in books}

        book_combo = ctk.CTkComboBox(form_scrollable, values=book_options)
        book_combo.pack(fill="x", pady=5)

        ctk.CTkLabel(form_scrollable, text="Инвентарный номер:*").pack(anchor="w", pady=(10, 0))
        inv_entry = ctk.CTkEntry(form_scrollable, height=35)
        inv_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form_scrollable, text="Состояние:*").pack(anchor="w", pady=(10, 0))
        condition_combo = ctk.CTkComboBox(form_scrollable,
                                          values=["Отличное", "Хорошее", "Удовлетворительное", "Плохое"])
        condition_combo.set("Хорошее")
        condition_combo.pack(fill="x", pady=5)

        ctk.CTkLabel(form_scrollable, text="Место хранения:").pack(anchor="w", pady=(10, 0))
        location_entry = ctk.CTkEntry(form_scrollable, height=35, placeholder_text="Стеллаж, полка")
        location_entry.pack(fill="x", pady=5)

        def save_copy():
            try:
                selected_book_text = book_combo.get().strip()
                if not selected_book_text:
                    messagebox.showwarning("Ошибка", "Выберите книгу")
                    return

                # Получаем ID книги из словаря
                book_id = book_mapping.get(selected_book_text)
                if book_id is None:
                    messagebox.showwarning("Ошибка", "Выберите книгу из списка")
                    return

                inventory_number = inv_entry.get().strip()
                condition = condition_combo.get()
                location = location_entry.get().strip() or None

                if not inventory_number:
                    messagebox.showwarning("Ошибка", "Введите инвентарный номер")
                    return

                result = db.create_book_copy(self.session, book_id, inventory_number, condition, location)
                if result:
                    messagebox.showinfo("Успех", "Экземпляр успешно добавлен!")
                    dialog.destroy()
                    # Обновляем оба списка
                    self.load_books()
                    self.load_book_copies()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить экземпляр: {e}")

        # Фрейм для кнопок (вне прокручиваемой области)
        btn_frame = ctk.CTkFrame(main_container)
        btn_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkButton(btn_frame, text="Отмена",
                      command=dialog.destroy,
                      width=100,
                      fg_color="gray").pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Сохранить",
                      command=save_copy,
                      width=100).pack(side="right")

    def show_edit_book_dialog(self):
        """Диалог редактирования книги"""
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите книгу для редактирования")
            return

        # Получаем ID выбранной книги
        book_id = self.books_tree.item(selected[0])['values'][0]
        book = db.get_book_by_id(self.session, book_id)

        if not book:
            messagebox.showerror("Ошибка", "Книга не найдена")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактирование книги")
        dialog.geometry("500x650")
        dialog.minsize(500, 650)
        dialog.transient(self)
        dialog.grab_set()

        self.center_dialog(dialog)

        # Главный контейнер
        main_container = ctk.CTkFrame(dialog)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(main_container, text=f"Редактирование: {book.title}",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # Прокручиваемая область для формы
        form_scrollable = ctk.CTkScrollableFrame(main_container)
        form_scrollable.pack(fill="both", expand=True)

        # Поля формы
        fields = [
            ("Название:*", "title"),
            ("Автор:*", "author"),
            ("ISBN:", "isbn"),
            ("Год издания:", "publish_year"),
            ("Описание:", "description")
        ]

        entries = {}
        for label, key in fields:
            ctk.CTkLabel(form_scrollable, text=label).pack(anchor="w", pady=(10, 0))
            if key == "description":
                entry = ctk.CTkTextbox(form_scrollable, height=80)
                # Заполняем текущими данными
                if getattr(book, key, None):
                    entry.insert("1.0", getattr(book, key))
                entry.pack(fill="x", pady=5)
            else:
                entry = ctk.CTkEntry(form_scrollable, height=35)
                # Заполняем текущими данными
                current_value = getattr(book, key, "")
                entry.insert(0, str(current_value) if current_value is not None else "")
                entry.pack(fill="x", pady=5)
            entries[key] = entry

        # Поле для доступности
        ctk.CTkLabel(form_scrollable, text="Доступность:").pack(anchor="w", pady=(10, 0))
        available_var = ctk.BooleanVar(value=book.available)
        available_check = ctk.CTkCheckBox(form_scrollable, text="Книга доступна", variable=available_var)
        available_check.pack(anchor="w", pady=5)

        # Поле для выбора жанров (несколько)
        ctk.CTkLabel(form_scrollable, text="Жанры:").pack(anchor="w", pady=(10, 0))

        # Создаем скроллируемый фрейм для чекбоксов
        genres_scrollable = ctk.CTkScrollableFrame(
            form_scrollable,
            height=120,
            fg_color=("gray80", "gray20")
        )
        genres_scrollable.pack(fill="x", pady=5)

        # Получаем список всех жанров из базы данных
        all_genres = db.get_all_genres(self.session)
        genre_vars = {}  # Словарь для хранения переменных чекбоксов

        # Получаем текущие жанры книги
        current_genre_ids = [genre.id for genre in book.genres] if book.genres else []

        # Создаем чекбоксы для каждого жанра
        for genre in all_genres:
            var = ctk.BooleanVar(value=(genre.id in current_genre_ids))
            chk = ctk.CTkCheckBox(
                genres_scrollable,
                text=genre.name,
                variable=var
            )
            chk.pack(anchor="w", pady=2)
            genre_vars[genre.id] = var

        def save_changes():
            try:
                title = entries['title'].get().strip()
                author = entries['author'].get().strip()

                if not title or not author:
                    messagebox.showwarning("Ошибка", "Заполните обязательные поля (Название и Автор)")
                    return

                # Подготавливаем данные для обновления
                update_data = {
                    'title': title,
                    'author': author,
                    'isbn': entries['isbn'].get().strip() or None,
                    'description': entries['description'].get("1.0", "end-1c").strip() or None,
                    'available': available_var.get()
                }

                # Обрабатываем год издания
                year_str = entries['publish_year'].get().strip()
                if year_str:
                    try:
                        update_data['publish_year'] = int(year_str)
                    except ValueError:
                        messagebox.showerror("Ошибка", "Год издания должен быть числом")
                        return
                else:
                    update_data['publish_year'] = None

                # Обновляем данные книги
                result = db.update_book(self.session, book_id, **update_data)
                if not result:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные книги")
                    return

                # Обновляем жанры
                selected_genre_ids = []
                for genre_id, var in genre_vars.items():
                    if var.get():
                        selected_genre_ids.append(genre_id)

                # Устанавливаем новые жанры
                genre_result = db.set_book_genres(self.session, book_id, selected_genre_ids)

                if genre_result:
                    messagebox.showinfo("Успех", f"Книга '{title}' успешно обновлена!")
                    dialog.destroy()
                    self.load_books()
                else:
                    messagebox.showwarning("Предупреждение",
                                           "Основные данные книги обновлены, но возникла проблема с жанрами")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить книгу: {e}")

        # Фрейм для кнопок (вне прокручиваемой области)
        btn_frame = ctk.CTkFrame(main_container)
        btn_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkButton(btn_frame, text="Отмена",
                      command=dialog.destroy,
                      width=100,
                      fg_color="gray").pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Сохранить",
                      command=save_changes,
                      width=100).pack(side="right")

        # Фокусируем на первом поле
        entries['title'].focus_set()

    def delete_book(self):
        """Удаление выбранной книги"""
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите книгу для удаления")
            return

        # Получаем ID и данные выбранной книги
        book_id = self.books_tree.item(selected[0])['values'][0]
        book_title = self.books_tree.item(selected[0])['values'][1]
        book_author = self.books_tree.item(selected[0])['values'][2]

        # Проверяем, есть ли связанные экземпляры книги
        copies = db.get_copies_by_book(self.session, book_id)
        if copies:
            messagebox.showwarning(
                "Невозможно удалить",
                f"Невозможно удалить книгу '{book_title}'\n\n"
                f"Существуют экземпляры этой книги ({len(copies)} шт.).\n"
                f"Сначала удалите все экземпляры книги."
            )
            return

        # Запрашиваем подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить книгу?\n\n"
            f"Название: {book_title}\n"
            f"Автор: {book_author}\n\n"
            f"Это действие нельзя отменить!",
            icon='warning'
        )

        if not confirm:
            return

        try:
            # Выполняем удаление
            success = db.delete_book(self.session, book_id)
            if success:
                messagebox.showinfo("Успех", f"Книга '{book_title}' успешно удалена!")
                self.load_books()  # Обновляем список книг
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить книгу")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении книги: {e}")

    def show_change_copy_status_dialog(self):
        """Диалог изменения статуса экземпляра книги"""
        selected = self.copies_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите экземпляр для изменения статуса")
            return

        # Получаем ID и данные выбранного экземпляра
        copy_id = self.copies_tree.item(selected[0])['values'][0]
        inventory_number = self.copies_tree.item(selected[0])['values'][1]
        book_title = self.copies_tree.item(selected[0])['values'][2]
        current_status = self.copies_tree.item(selected[0])['values'][4]
        current_condition = self.copies_tree.item(selected[0])['values'][5]

        # Получаем полную информацию об экземпляре
        copy = db.get_copy_by_id(self.session, copy_id)
        if not copy:
            messagebox.showerror("Ошибка", "Экземпляр не найден")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Изменение статуса экземпляра")
        dialog.geometry("500x400")
        dialog.minsize(500, 400)
        dialog.transient(self)
        dialog.grab_set()

        self.center_dialog(dialog)

        # Главный контейнер
        main_container = ctk.CTkFrame(dialog)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(main_container, text="Изменение статуса экземпляра",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # Информация об экземпляре
        info_frame = ctk.CTkFrame(main_container)
        info_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(info_frame, text="Информация об экземпляре:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(info_frame, text=f"📖 Книга: {book_title}").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_frame, text=f"🔢 Инвентарный номер: {inventory_number}").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_frame, text=f"📊 Текущий статус: {current_status}").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_frame, text=f"🏷️ Текущее состояние: {current_condition}").pack(anchor="w", pady=2)

        # Поле для выбора нового статуса
        ctk.CTkLabel(main_container, text="Новый статус:*",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 0))

        status_combo = ctk.CTkComboBox(main_container,
                                       values=["Доступен", "Выдан", "В ремонте", "Утерян"])
        status_combo.set(current_status)  # Устанавливаем текущий статус
        status_combo.pack(fill="x", pady=5)

        # Поле для выбора состояния
        ctk.CTkLabel(main_container, text="Состояние:*",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 0))

        condition_combo = ctk.CTkComboBox(main_container,
                                          values=["Отличное", "Хорошее", "Удовлетворительное", "Плохое"])
        condition_combo.set(current_condition)  # Устанавливаем текущее состояние
        condition_combo.pack(fill="x", pady=5)

        # Поле для примечания (опционально)
        ctk.CTkLabel(main_container, text="Примечание:").pack(anchor="w", pady=(10, 0))
        note_entry = ctk.CTkEntry(main_container, height=35, placeholder_text="Дополнительная информация...")
        note_entry.pack(fill="x", pady=5)

        def save_status():
            try:
                new_status = status_combo.get()
                new_condition = condition_combo.get()
                note = note_entry.get().strip() or None

                if not new_status or not new_condition:
                    messagebox.showwarning("Ошибка", "Заполните все обязательные поля")
                    return

                # Маппинг статусов на булево значение available
                status_to_available = {
                    "Доступен": True,
                    "Выдан": False,
                    "В ремонте": False,
                    "Утерян": False,
                }

                # Подготавливаем данные для обновления
                update_data = {
                    'available': status_to_available.get(new_status, False),
                    'condition': new_condition
                }

                # Если нужно, можно добавить поле для примечания в базу данных
                # if note:
                #     update_data['note'] = note

                # Обновляем экземпляр
                result = db.update_copy(self.session, copy_id, **update_data)
                if result:
                    messagebox.showinfo("Успех", f"Статус экземпляра успешно изменен на '{new_status}'")
                    dialog.destroy()
                    self.load_book_copies()  # Обновляем список экземпляров

                    # Логируем изменение
                    print(f"Статус экземпляра {inventory_number} изменен: {current_status} -> {new_status}")
                    if note:
                        print(f"Примечание: {note}")

                else:
                    messagebox.showerror("Ошибка", "Не удалось изменить статус экземпляра")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при изменении статуса: {e}")

        # Фрейм для кнопок
        btn_frame = ctk.CTkFrame(main_container)
        btn_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(btn_frame, text="Отмена",
                      command=dialog.destroy,
                      width=100,
                      fg_color="gray").pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Сохранить",
                      command=save_status,
                      width=100).pack(side="right")

        # Фокусируем на комбобоксе статуса
        status_combo.focus_set()


    def write_off_copy(self):
        """Списание экземпляра"""
        selected = self.copies_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите экземпляр для списания")
            return

        item = self.copies_tree.item(selected[0])
        copy_id = item['values'][0]
        inv_number = item['values'][1]
        book_title = item['values'][2]

        if not messagebox.askyesno("Подтверждение",
                                   f"Вы уверены, что хотите списать экземпляр {inv_number}?\n"
                                   f"Книга: {book_title}"):
            return

        try:
            db.delete_copy(self.session, copy_id)
            messagebox.showinfo("Успех", f"Экземпляр {inv_number} списан")
            self.load_book_copies()
            self.load_books()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось списать экземпляр: {e}")

    def center_dialog(self, dialog):
        """Центрирование диалогового окна"""
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

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