import bcrypt
from sqlalchemy import create_engine, and_, or_, text, inspect, func
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

from .models import Base, Reader, Book, BookCopy, Genre, Librarian, Loan, Fine
from .db_config import DB_HOST, DB_NAME, DB_USER, DB_PORT, DB_PASS


def init_db():
    """
    Инициализация базы данных - создание всех таблиц
    """
    try:
        database_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        print("База данных успешно инициализирована")
        return Session
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        return None


def get_session():
    """
    Получение сессии для работы с базой данных
    """
    try:
        database_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        print(f"Ошибка при создании сессии: {e}")
        return None


def close_session(session):
    """
    Закрытие сессии
    """
    try:
        if session:
            session.close()
            print("Сессия закрыта")
    except Exception as e:
        print(f"Ошибка при закрытии сессии: {e}")


def check_db_connection():
    """
    Проверка подключения к базе данных
    """
    try:
        session = get_session()
        if session:
            _ = session.execute(text("SELECT 1"))
            session.close()
            print("Подключение к базе данных установлено")
            return True
        return False
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return False


def get_table_names():
    """
    Получение списка всех таблиц в базе данных
    """
    try:
        database_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Таблицы в базе данных:")
        for table in tables:
            print(f"  - {table}")
        return tables
    except Exception as e:
        print(f"Ошибка при получении списка таблиц: {e}")
        return []


def get_table_info(table_name):
    """
    Получение информации о структуре таблицы
    """
    try:
        database_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(database_url)
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        print(f"Структура таблицы '{table_name}':")
        for column in columns:
            print(f"  - {column['name']}: {column['type']} {'(nullable)' if column['nullable'] else '(not null)'}")
        return columns
    except Exception as e:
        print(f"Ошибка при получении информации о таблице: {e}")
        return []


def drop_all_tables():
    """
    Удаление всех таблиц из базы данных (ОПАСНО!)
    """
    try:
        database_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(database_url)

        confirm = input("⚠Вы уверены, что хотите удалить ВСЕ таблицы? (yes/no): ")
        if confirm.lower() == 'yes':
            Base.metadata.drop_all(engine)
            print("Все таблицы удалены")
        else:
            print("Операция отменена")
    except Exception as e:
        print(f"Ошибка при удалении таблиц: {e}")


def execute_raw_sql(query, params=None):
    """
    Выполнение произвольного SQL-запроса
    """
    session = get_session()
    try:
        if query.strip().upper().startswith('SELECT'):
            result = session.execute(text(query), params or {})
            rows = result.fetchall()
            print(f"Запрос выполнен, найдено {len(rows)} записей")
            return rows
        else:
            result = session.execute(text(query), params or {})
            session.commit()
            print("Запрос выполнен успешно")
            return result.rowcount
    except Exception as e:
        session.rollback()
        print(f"Ошибка при выполнении SQL-запроса: {e}")
        return None
    finally:
        close_session(session)


def get_database_stats():
    """
    Получение общей статистики базы данных
    """
    try:
        session = get_session()

        # Количество таблиц
        tables_count = session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).scalar()

        # Размер базы данных
        db_size = session.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)).scalar()

        print("Статистика базы данных:")
        print(f"  - Количество таблиц: {tables_count}")
        print(f"  - Размер базы данных: {db_size}")

        session.close()
        return {
            'tables_count': tables_count,
            'database_size': db_size
        }
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {}


# Утилиты для работы с транзакциями
def safe_commit(session, operation_name=""):
    """
    Безопасное подтверждение транзакции с обработкой ошибок
    """
    try:
        session.commit()
        if operation_name:
            print(f"{operation_name} выполнено успешно")
        return True
    except Exception as e:
        session.rollback()
        if operation_name:
            print(f"Ошибка при {operation_name}: {e}")
        else:
            print(f"Ошибка при выполнении операции: {e}")
        return False


def with_session(func):
    """
    Декоратор для автоматического управления сессией
    """

    def wrapper(*args, **kwargs):
        session = get_session()
        try:
            result = func(session, *args, **kwargs)
            return result
        except Exception as e:
            print(f"Ошибка в функции {func.__name__}: {e}")
            return None
        finally:
            close_session(session)

    return wrapper


def create_reader(session, name, email, phone_number=None):
    """
    Создание нового читателя
    """
    try:
        # Проверяем, нет ли уже читателя с таким email
        existing_reader = session.query(Reader).filter(Reader.email == email).first()
        if existing_reader:
            print(f"Ошибка: Читатель с email '{email}' уже существует")
            return None

        reader = Reader(
            name=name,
            email=email,
            phone_number=phone_number
        )

        session.add(reader)
        session.commit()
        print(f"Читатель '{name}' успешно создан (ID: {reader.id})")
        return reader

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании читателя: {e}")
        return None


def get_reader_by_id(session, reader_id):
    """
    Получение читателя по ID
    """
    try:
        reader = session.query(Reader).filter(Reader.id == reader_id).first()
        if reader:
            return reader
        else:
            print(f"Читатель с ID {reader_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске читателя: {e}")
        return None


def get_reader_by_email(session, email):
    """
    Получение читателя по email
    """
    try:
        reader = session.query(Reader).filter(Reader.email == email).first()
        if reader:
            return reader
        else:
            print(f"Читатель с email '{email}' не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске читателя по email: {e}")
        return None


def get_all_readers(session, limit=None, offset=None):
    """
    Получение всех читателейс разбиением на страницы
    """
    try:
        query = session.query(Reader).order_by(Reader.id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        readers = query.all()
        print(f"Найдено {len(readers)} читателей")
        return readers
    except Exception as e:
        print(f"Ошибка при получении списка читателей: {e}")
        return []


def search_readers(session, search_term):
    """
    Поиск читателей по имени или email
    """
    try:
        readers = session.query(Reader).filter(
            or_(
                Reader.name.ilike(f"%{search_term}%"),
                Reader.email.ilike(f"%{search_term}%")
            )
        ).all()

        print(f"По запросу '{search_term}' найдено {len(readers)} читателей")
        return readers
    except Exception as e:
        print(f"Ошибка при поиске читателей: {e}")
        return []


def update_reader(session, reader_id, **kwargs):
    """
    Обновление данных читателя с помощью id и словаря новых значений
    """
    try:
        reader = get_reader_by_id(session, reader_id)
        if not reader:
            return None

        valid_fields = ['name', 'email', 'phone_number']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                # Проверяем уникальность email при обновлении
                if field == 'email' and value != reader.email:
                    existing = get_reader_by_email(session, value)
                    if existing:
                        print(f"Ошибка: Читатель с email '{value}' уже существует")
                        return None

                setattr(reader, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Читатель ID {reader_id} обновлен. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return reader

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении читателя: {e}")
        return None


def delete_reader(session, reader_id):
    """
    Удаление читателя
    """
    try:
        reader = get_reader_by_id(session, reader_id)
        if not reader:
            return False

        session.delete(reader)
        session.commit()
        print(f"Читатель ID {reader_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении читателя: {e}")
        return False


def delete_reader_by_email(session, email):
    """
    Удаление читателя по email
    """
    try:
        reader = get_reader_by_email(session, email)
        if not reader:
            return False

        session.delete(reader)
        session.commit()
        print(f"Читатель с email '{email}' успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении читателя: {e}")
        return False


def get_readers_count(session):
    """
    Получение общего количества читателей
    """
    try:
        count = session.query(Reader).count()
        print(f"Общее количество читателей: {count}")
        return count
    except Exception as e:
        print(f"Ошибка при подсчете читателей: {e}")
        return 0


def get_recent_readers(session, days=30):
    """
    Получение читателей, зарегистрированных за последние N дней
    """
    try:
        cutoff_date = date.today() - timedelta(days=days)
        readers = session.query(Reader).filter(
            Reader.registration_date >= cutoff_date
        ).order_by(Reader.registration_date.desc()).all()

        print(f"Найдено {len(readers)} читателей, зарегистрированных за последние {days} дней")
        return readers
    except Exception as e:
        print(f"Ошибка при поиске недавно зарегистрированных читателей: {e}")
        return []


def print_reader_info(reader):
    """
    Вывод информации о читателе в читаемом формате
    """
    if not reader:
        print("Читатель не найден")
        return

    print(f"ID: {reader.id}")
    print(f"Имя: {reader.name}")
    print(f"Email: {reader.email}")
    print(f"Телефон: {reader.phone_number or 'Не указан'}")
    print(f"Дата регистрации: {reader.registration_date}")
    print("-" * 40)


def hash_password(password):
    """Хэширование пароля"""
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password, hashed_password):
    """Проверка пароля"""
    try:
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def create_librarian(session, name, email, password, position=None):
    """
    Создание нового библиотекаря
    """
    try:
        existing_librarian = session.query(Librarian).filter(Librarian.email == email).first()
        if existing_librarian:
            print(f"Библиотекарь с email '{email}' уже существует")
            return None

        password_hash = hash_password(password)

        librarian = Librarian(
            name=name,
            email=email,
            password_hash=password_hash,
            position=position
        )

        session.add(librarian)
        session.commit()
        print(f"Библиотекарь '{name}' успешно создан (ID: {librarian.id})")
        return librarian

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании библиотекаря: {e}")
        return None


def get_librarian_by_id(session, librarian_id):
    """
    Получение библиотекаря по ID
    """
    try:
        librarian = session.query(Librarian).filter(Librarian.id == librarian_id).first()
        if librarian:
            return librarian
        else:
            print(f"Библиотекарь с ID {librarian_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске библиотекаря: {e}")
        return None


def get_librarian_by_email(session, email):
    """
    Получение библиотекаря по email
    """
    try:
        librarian = session.query(Librarian).filter(Librarian.email == email).first()
        if librarian:
            return librarian
        else:
            print(f"Библиотекарь с email '{email}' не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске библиотекаря по email: {e}")
        return None


def get_all_librarians(session, limit=None, offset=None):
    """
    Получение всех библиотекарейс разбиением на страницы
    """
    try:
        query = session.query(Librarian).order_by(Librarian.id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        librarians = query.all()
        print(f"Найдено {len(librarians)} библиотекарей")
        return librarians
    except Exception as e:
        print(f"Ошибка при получении списка библиотекарей: {e}")
        return []


def search_librarians(session, search_term):
    """
    Поиск библиотекарей по имени или email
    """
    try:
        librarians = session.query(Librarian).filter(
            or_(
                Librarian.name.ilike(f"%{search_term}%"),
                Librarian.email.ilike(f"%{search_term}%")
            )
        ).all()

        print(f"По запросу '{search_term}' найдено {len(librarians)} библиотекарей")
        return librarians
    except Exception as e:
        print(f"Ошибка при поиске библиотекарей: {e}")
        return []


def update_librarian(session, librarian_id, **kwargs):
    """
    Обновление данных библиотекаря на выбор из ['name', 'email', 'position', 'password']
    """
    try:
        librarian = get_librarian_by_id(session, librarian_id)
        if not librarian:
            return None

        valid_fields = ['name', 'email', 'position', 'password']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                if field == 'email' and value != librarian.email:
                    existing = get_librarian_by_email(session, value)
                    if existing:
                        print(f"Библиотекарь с email '{value}' уже существует")
                        return None
                    setattr(librarian, field, value)
                    updated_fields.append(field)

                elif field == 'password':
                    password_hash = hash_password(value)
                    librarian.password_hash = password_hash
                    updated_fields.append('password')

                else:
                    setattr(librarian, field, value)
                    updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Библиотекарь ID {librarian_id} обновлен. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return librarian

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении библиотекаря: {e}")
        return None


def delete_librarian(session, librarian_id):
    """
    Удаление библиотекаря
    """
    try:
        librarian = get_librarian_by_id(session, librarian_id)
        if not librarian:
            return False

        session.delete(librarian)
        session.commit()
        print(f"Библиотекарь ID {librarian_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении библиотекаря: {e}")
        return False


def delete_librarian_by_email(session, email):
    """
    Удаление библиотекаря по email
    """
    try:
        librarian = get_librarian_by_email(session, email)
        if not librarian:
            return False

        session.delete(librarian)
        session.commit()
        print(f"Библиотекарь с email '{email}' успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении библиотекаря: {e}")
        return False


def authenticate_librarian(session, email, password):
    """
    Аутентификация библиотекаря
    """
    try:
        librarian = get_librarian_by_email(session, email)
        if not librarian:
            print("Неверный email или пароль")
            return None

        if verify_password(password, librarian.password_hash):
            print(f"Успешная аутентификация для {librarian.name}")
            return librarian
        else:
            print("Неверный email или пароль")
            return None

    except Exception as e:
        print(f"Ошибка при аутентификации: {e}")
        return None


def change_librarian_password(session, librarian_id, current_password, new_password):
    """
    Смена пароля библиотекаря с проверкой текущего
    """
    try:
        librarian = get_librarian_by_id(session, librarian_id)
        if not librarian:
            return False

        if not verify_password(current_password, librarian.password_hash):
            print("Текущий пароль неверен")
            return False

        return update_librarian(session, librarian_id, password=new_password) is not None

    except Exception as e:
        print(f"Ошибка при смене пароля: {e}")
        return False


def get_librarians_count(session):
    """
    Получение общего количества библиотекарей
    """
    try:
        count = session.query(Librarian).count()
        print(f"Общее количество библиотекарей: {count}")
        return count
    except Exception as e:
        print(f"Ошибка при подсчете библиотекарей: {e}")
        return 0


def print_librarian_info(librarian, show_password=False):
    """
    Вывод информации о библиотекаре в читаемом формате
    """
    if not librarian:
        print("Библиотекарь не найден")
        return

    print(f"ID: {librarian.id}")
    print(f"Имя: {librarian.name}")
    print(f"Email: {librarian.email}")
    print(f"Должность: {librarian.position or 'Не указана'}")
    print(f"Дата приема: {librarian.hire_date}")
    if show_password:
        print(f"Хэш пароля: {librarian.password_hash}")
    print("-" * 40)


def create_book(session, title, author, isbn=None, publication_year=None, genre=None, description=None):
    """Создать новую книгу (обновленная версия)"""
    try:
        # Проверяем уникальность ISBN
        if isbn:
            existing_book = session.query(Book).filter(Book.isbn == isbn).first()
            if existing_book:
                raise ValueError(f"Книга с ISBN {isbn} уже существует")

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            publish_year=publication_year,
            description=description
        )

        session.add(book)
        session.commit()
        return book
    except Exception as e:
        session.rollback()
        raise e


def get_book_by_id(session, book_id):
    """
    Получение книги по ID
    """
    try:
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            return book
        else:
            print(f"Книга с ID {book_id} не найдена")
            return None
    except Exception as e:
        print(f"Ошибка при поиске книги: {e}")
        return None


def get_book_by_isbn(session, isbn):
    """
    Получение книги по ISBN
    """
    try:
        book = session.query(Book).filter(Book.isbn == isbn).first()
        if book:
            return book
        else:
            print(f"Книга с ISBN '{isbn}' не найдена")
            return None
    except Exception as e:
        print(f"Ошибка при поиске книги по ISBN: {e}")
        return None


def search_books(session, title=None, author=None, genre_name=None, available_only=False):
    """
    Поиск книг по различным критериям
    """
    try:
        query = session.query(Book)

        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))
        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))
        if genre_name:
            query = query.join(Book.genres).filter(Genre.name.ilike(f"%{genre_name}%"))
        if available_only:
            query = query.filter(Book.available == True)

        books = query.all()
        print(f"Найдено {len(books)} книг по заданным критериям")
        return books
    except Exception as e:
        print(f"Ошибка при поиске книг: {e}")
        return []


def get_books_by_author(session, author):
    """
    Получение книг по автору
    """
    try:
        books = session.query(Book).filter(Book.author.ilike(f"%{author}%")).all()
        print(f"Найдено {len(books)} книг автора '{author}'")
        return books
    except Exception as e:
        print(f"Ошибка при поиске книг по автору: {e}")
        return []


def get_books_by_year(session, year):
    """
    Получение книг по году издания
    """
    try:
        books = session.query(Book).filter(Book.publish_year == year).all()
        print(f"Найдено {len(books)} книг издания {year} года")
        return books
    except Exception as e:
        print(f"Ошибка при поиске книг по году: {e}")
        return []


def update_book(session, book_id, **kwargs):
    """
    Обновление данных книги ['title', 'author', 'isbn', 'publish_year', 'description', 'available']
    """
    try:
        book = get_book_by_id(session, book_id)
        if not book:
            return None

        valid_fields = ['title', 'author', 'isbn', 'publish_year', 'description', 'available']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                # Проверяем уникальность ISBN при обновлении
                if field == 'isbn' and value != book.isbn:
                    existing = get_book_by_isbn(session, value)
                    if existing:
                        print(f"Книга с ISBN '{value}' уже существует")
                        return None

                setattr(book, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Книга ID {book_id} обновлена. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return book

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении книги: {e}")
        return None


def delete_book(session, book_id):
    """
    Удаление книги
    """
    try:
        book = get_book_by_id(session, book_id)
        if not book:
            return False

        session.delete(book)
        session.commit()
        print(f"Книга ID {book_id} успешно удалена")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении книги: {e}")
        return False


def create_genre(session, name):
    """
    Создание нового жанра
    """
    try:
        # Проверяем уникальность названия жанра
        existing_genre = session.query(Genre).filter(Genre.name.ilike(name)).first()
        if existing_genre:
            print(f"Жанр '{name}' уже существует")
            return None

        genre = Genre(name=name)
        session.add(genre)
        session.commit()
        print(f"Жанр '{name}' успешно создан (ID: {genre.id})")
        return genre

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании жанра: {e}")
        return None


def get_genre_by_id(session, genre_id):
    """
    Получение жанра по ID
    """
    try:
        genre = session.query(Genre).filter(Genre.id == genre_id).first()
        if genre:
            return genre
        else:
            print(f"Жанр с ID {genre_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске жанра: {e}")
        return None


def get_genre_by_name(session, name):
    """
    Получение жанра по названию
    """
    try:
        genre = session.query(Genre).filter(Genre.name.ilike(name)).first()
        if genre:
            return genre
        else:
            print(f"Жанр '{name}' не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске жанра по названию: {e}")
        return None


def get_all_genres(session):
    """
    Получение всех жанров
    """
    try:
        genres = session.query(Genre).order_by(Genre.name).all()
        print(f"Найдено {len(genres)} жанров")
        return genres
    except Exception as e:
        print(f"Ошибка при получении списка жанров: {e}")
        return []


def search_genres(session, search_term):
    """
    Поиск жанров по названию
    """
    try:
        genres = session.query(Genre).filter(Genre.name.ilike(f"%{search_term}%")).all()
        print(f"По запросу '{search_term}' найдено {len(genres)} жанров")
        return genres
    except Exception as e:
        print(f"Ошибка при поиске жанров: {e}")
        return []


def update_genre(session, genre_id, **kwargs):
    """
    Обновление данных жанра ['name']
    """
    try:
        genre = get_genre_by_id(session, genre_id)
        if not genre:
            return None

        valid_fields = ['name']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                # Проверяем уникальность названия жанра при обновлении
                if field == 'name' and value != genre.name:
                    existing = get_genre_by_name(session, value)
                    if existing:
                        print(f"Жанр '{value}' уже существует")
                        return None

                setattr(genre, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Жанр ID {genre_id} обновлен. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return genre

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении жанра: {e}")
        return None


def delete_genre(session, genre_id):
    """
    Удаление жанра
    """
    try:
        genre = get_genre_by_id(session, genre_id)
        if not genre:
            return False

        session.delete(genre)
        session.commit()
        print(f"Жанр ID {genre_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении жанра: {e}")
        return False


def add_genre_to_book(session, book_id, genre_id):
    """
    Добавление жанра к книге
    """
    try:
        book = get_book_by_id(session, book_id)
        genre = get_genre_by_id(session, genre_id)

        if not book or not genre:
            print("Книга или жанр не найдены")
            return False

        # Проверяем, не добавлен ли уже этот жанр к книге
        if genre in book.genres:
            print(f"Жанр '{genre.name}' уже добавлен к книге '{book.title}'")
            return False

        book.genres.append(genre)
        session.commit()
        print(f"Жанр '{genre.name}' успешно добавлен к книге '{book.title}'")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении жанра к книге: {e}")
        return False


def remove_genre_from_book(session, book_id, genre_id):
    """
    Удаление жанра из книги
    """
    try:
        book = get_book_by_id(session, book_id)
        genre = get_genre_by_id(session, genre_id)

        if not book or not genre:
            print("Книга или жанр не найдены")
            return False

        if genre not in book.genres:
            print(f"Жанр '{genre.name}' не связан с книгой '{book.title}'")
            return False

        book.genres.remove(genre)
        session.commit()
        print(f"Жанр '{genre.name}' успешно удален из книги '{book.title}'")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении жанра из книги: {e}")
        return False


def get_books_by_genre(session, genre_id):
    """
    Получение всех книг определенного жанра
    """
    try:
        genre = get_genre_by_id(session, genre_id)
        if not genre:
            return []

        books = genre.books
        print(f"Найдено {len(books)} книг в жанре '{genre.name}'")
        return books
    except Exception as e:
        print(f"Ошибка при получении книг по жанру: {e}")
        return []


def get_genres_by_book(session, book_id):
    """
    Получение всех жанров книги
    """
    try:
        book = get_book_by_id(session, book_id)
        if not book:
            return []

        genres = book.genres
        print(f"Найдено {len(genres)} жанров для книги '{book.title}'")
        return genres
    except Exception as e:
        print(f"Ошибка при получении жанров книги: {e}")
        return []


def set_book_genres(session, book_id, genre_ids):
    """
    Установка жанров для книги (замена текущих)
    """
    try:
        book = get_book_by_id(session, book_id)
        if not book:
            return False

        # Получаем объекты жанров по ID
        genres = []
        for genre_id in genre_ids:
            genre = get_genre_by_id(session, genre_id)
            if genre:
                genres.append(genre)
            else:
                print(f"Жанр с ID {genre_id} не найден")

        # Заменяем текущие жанры
        book.genres = genres
        session.commit()
        print(f"Для книги '{book.title}' установлено {len(genres)} жанров")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при установке жанров для книги: {e}")
        return False


def get_books_count(session):
    """
    Получение общего количества книг
    """
    try:
        count = session.query(Book).count()
        print(f"Общее количество книг: {count}")
        return count
    except Exception as e:
        print(f"Ошибка при подсчете книг: {e}")
        return 0


def get_genres_count(session):
    """
    Получение общего количества жанров
    """
    try:
        count = session.query(Genre).count()
        print(f"Общее количество жанров: {count}")
        return count
    except Exception as e:
        print(f"Ошибка при подсчете жанров: {e}")
        return 0


def print_book_info(book):
    """
    Вывод информации о книге
    """
    if not book:
        print("Книга не найдена")
        return

    print(f"ID: {book.id}")
    print(f"Название: {book.title}")
    print(f"Автор: {book.author or 'Не указан'}")
    print(f"ISBN: {book.isbn or 'Не указан'}")
    print(f"Год издания: {book.publish_year or 'Не указан'}")
    print(f"Доступна: {'Да' if book.available else 'Нет'}")
    print(f"Описание: {book.description or 'Отсутствует'}")

    genres = [genre.name for genre in book.genres]
    print(f"Жанры: {', '.join(genres) if genres else 'Не указаны'}")
    print("-" * 50)


def print_genre_info(genre):
    """
    Вывод информации о жанре
    """
    if not genre:
        print("Жанр не найден")
        return

    print(f"ID: {genre.id}")
    print(f"Название: {genre.name}")
    print(f"Количество книг: {len(genre.books)}")
    print("-" * 30)


def create_book_copy(session, book_id, inventory_number, condition='good', location=None):
    """
    Создание нового экземпляра книги
    """
    try:
        # Проверяем существование книги
        book = session.query(Book).filter(Book.id == book_id).first()
        if not book:
            print(f"Книга с ID {book_id} не найдена")
            return None

        # Проверяем уникальность инвентарного номера
        existing_copy = session.query(BookCopy).filter(BookCopy.inventory_number == inventory_number).first()
        if existing_copy:
            print(f"Экземпляр с инвентарным номером '{inventory_number}' уже существует")
            return None

        copy = BookCopy(
            book_id=book_id,
            inventory_number=inventory_number,
            condition=condition,
            location=location
        )

        session.add(copy)
        session.commit()
        print(f"Экземпляр книги '{book.title}' создан (Инвентарный номер: {inventory_number})")
        return copy

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании экземпляра книги: {e}")
        return None


def get_copy_by_id(session, copy_id):
    """
    Получение экземпляра по ID
    """
    try:
        copy = session.query(BookCopy).filter(BookCopy.id == copy_id).first()
        if copy:
            return copy
        else:
            print(f"Экземпляр с ID {copy_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске экземпляра: {e}")
        return None


def get_copy_by_inventory(session, inventory_number):
    """
    Получение экземпляра по инвентарному номеру
    """
    try:
        copy = session.query(BookCopy).filter(BookCopy.inventory_number == inventory_number).first()
        if copy:
            return copy
        else:
            print(f"Экземпляр с инвентарным номером '{inventory_number}' не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске экземпляра по инвентарному номеру: {e}")
        return None


def get_copies_by_book(session, book_id, available_only=False):
    """
    Получение всех экземпляров определенной книги
    """
    try:
        query = session.query(BookCopy).filter(BookCopy.book_id == book_id)

        if available_only:
            query = query.filter(BookCopy.available == True)

        copies = query.all()
        status = "доступных" if available_only else ""
        print(f"Найдено {len(copies)} {status}экземпляров книги ID {book_id}")
        return copies
    except Exception as e:
        print(f"Ошибка при получении экземпляров книги: {e}")
        return []


def get_available_copies(session, book_id):
    """
    Получение доступных экземпляров книги
    """
    return get_copies_by_book(session, book_id, available_only=True)


def get_all_copies(session, limit=None, offset=None):
    """
    Получение всех экземпляров с разбиением на страницы
    """
    try:
        query = session.query(BookCopy).order_by(BookCopy.id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        copies = query.all()
        print(f"Найдено {len(copies)} экземпляров")
        return copies
    except Exception as e:
        print(f"Ошибка при получении списка экземпляров: {e}")
        return []


def search_copies(session, inventory_number=None, condition=None, location=None):
    """
    Поиск экземпляров по различным критериям
    """
    try:
        query = session.query(BookCopy)

        if inventory_number:
            query = query.filter(BookCopy.inventory_number.ilike(f"%{inventory_number}%"))
        if condition:
            query = query.filter(BookCopy.condition.ilike(f"%{condition}%"))
        if location:
            query = query.filter(BookCopy.location.ilike(f"%{location}%"))

        copies = query.all()
        print(f"Найдено {len(copies)} экземпляров по заданным критериям")
        return copies
    except Exception as e:
        print(f"Ошибка при поиске экземпляров: {e}")
        return []


def update_copy(session, copy_id, **kwargs):
    """
    Обновление данных экземпляра ['inventory_number', 'condition', 'location', 'available']
    """
    try:
        copy = get_copy_by_id(session, copy_id)
        if not copy:
            return None

        valid_fields = ['inventory_number', 'condition', 'location', 'available']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                # Проверяем уникальность инвентарного номера при обновлении
                if field == 'inventory_number' and value != copy.inventory_number:
                    existing = get_copy_by_inventory(session, value)
                    if existing:
                        print(f"Экземпляр с инвентарным номером '{value}' уже существует")
                        return None

                setattr(copy, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Экземпляр ID {copy_id} обновлен. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return copy

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении экземпляра: {e}")
        return None


def delete_copy(session, copy_id):
    """
    Удаление экземпляра
    """
    try:
        copy = get_copy_by_id(session, copy_id)
        if not copy:
            return False

        session.delete(copy)
        session.commit()
        print(f"Экземпляр ID {copy_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении экземпляра: {e}")
        return False


def delete_copy_by_inventory(session, inventory_number):
    """
    Удаление экземпляра по инвентарному номеру
    """
    try:
        copy = get_copy_by_inventory(session, inventory_number)
        if not copy:
            return False

        session.delete(copy)
        session.commit()
        print(f"Экземпляр с инвентарным номером '{inventory_number}' успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении экземпляра: {e}")
        return False


def create_multiple_copies(session, book_id, inventory_numbers, condition='good', location=None):
    """
    Создание нескольких экземпляров одной книги
    """
    try:
        book = session.query(Book).filter(Book.id == book_id).first()
        if not book:
            print(f"Книга с ID {book_id} не найдена")
            return []

        created_copies = []
        for inventory_number in inventory_numbers:
            # Проверяем уникальность инвентарного номера
            existing_copy = session.query(BookCopy).filter(BookCopy.inventory_number == inventory_number).first()
            if existing_copy:
                print(f"Пропуск: экземпляр с инвентарным номером '{inventory_number}' уже существует")
                continue

            copy = BookCopy(
                book_id=book_id,
                inventory_number=inventory_number,
                condition=condition,
                location=location
            )
            session.add(copy)
            created_copies.append(copy)

        session.commit()
        print(f"Создано {len(created_copies)} экземпляров книги '{book.title}'")
        return created_copies

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании нескольких экземпляров: {e}")
        return []


def mark_all_copies_unavailable(session, book_id):
    """
    Пометить все экземпляры книги как недоступные
    """
    try:
        copies = get_copies_by_book(session, book_id)
        updated_count = 0

        for copy in copies:
            if copy.available:
                copy.available = False
                updated_count += 1

        if updated_count > 0:
            session.commit()
            print(f"Обновлено {updated_count} экземпляров книги ID {book_id} (помечены как недоступные)")
        else:
            print("Нет экземпляров для обновления")

        return updated_count

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении доступности экземпляров: {e}")
        return 0


def get_copies_count(session, book_id=None, available_only=False):
    """
    Получение количества экземпляров
    """
    try:
        query = session.query(BookCopy)

        if book_id:
            query = query.filter(BookCopy.book_id == book_id)
        if available_only:
            query = query.filter(BookCopy.available == True)

        count = query.count()

        if book_id:
            book = session.query(Book).filter(Book.id == book_id).first()
            book_title = book.title if book else f"ID {book_id}"
            status = "доступных " if available_only else ""
            print(f"Количество {status}экземпляров книги '{book_title}': {count}")
        else:
            status = "доступных " if available_only else ""
            print(f"Общее количество {status}экземпляров: {count}")

        return count
    except Exception as e:
        print(f"Ошибка при подсчете экземпляров: {e}")
        return 0


def get_copies_statistics(session, book_id=None):
    """
    Получение статистики по экземплярам
    """
    try:
        query = session.query(BookCopy)

        if book_id:
            query = query.filter(BookCopy.book_id == book_id)
            book = session.query(Book).filter(Book.id == book_id).first()
            book_info = f" книги '{book.title}'" if book else f" книги ID {book_id}"
        else:
            book_info = ""

        total = query.count()
        available = query.filter(BookCopy.available == True).count()
        unavailable = total - available

        # Статистика по состоянию
        condition_stats = {}
        conditions = session.query(BookCopy.condition).distinct().all()
        for condition_tuple in conditions:
            condition = condition_tuple[0]
            if condition:
                condition_count = query.filter(BookCopy.condition == condition).count()
                condition_stats[condition] = condition_count

        print(f"Статистика экземпляров{book_info}:")
        print(f"  Всего: {total}")
        print(f"  Доступно: {available}")
        print(f"  Недоступно: {unavailable}")
        print("  Состояние:")
        for condition, count in condition_stats.items():
            print(f"    - {condition}: {count}")

        return {
            'total': total,
            'available': available,
            'unavailable': unavailable,
            'condition_stats': condition_stats
        }

    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {}


def print_copy_info(copy):
    """
    Вывод информации об экземпляре
    """
    if not copy:
        print("Экземпляр не найден")
        return

    book_title = copy.book.title if copy.book else "Неизвестно"

    print(f"ID экземпляра: {copy.id}")
    print(f"Книга: {book_title} (ID: {copy.book_id})")
    print(f"Инвентарный номер: {copy.inventory_number}")
    print(f"Состояние: {copy.condition}")
    print(f"Местоположение: {copy.location or 'Не указано'}")
    print(f"Доступен: {'Да' if copy.available else 'Нет'}")
    print("-" * 50)


def create_loan(session, reader_id, copy_id, librarian_id, loan_date=None, return_days=14):
    """
    Создание новой записи о выдаче книги
    """
    try:
        # Проверяем существование читателя, экземпляра и библиотекаря
        reader = session.query(Reader).filter(Reader.id == reader_id).first()
        copy = session.query(BookCopy).filter(BookCopy.id == copy_id).first()
        librarian = session.query(Librarian).filter(Librarian.id == librarian_id).first()

        if not reader:
            print(f"Читатель с ID {reader_id} не найден")
            return None
        if not copy:
            print(f"Экземпляр с ID {copy_id} не найден")
            return None
        if not librarian:
            print(f"Библиотекарь с ID {librarian_id} не найден")
            return None

        if not copy.available:
            print(f"Экземпляр {copy.inventory_number} недоступен для выдачи")
            return None

        if loan_date is None:
            loan_date = date.today()

        return_date = loan_date + timedelta(days=return_days)

        loan = Loan(
            reader_id=reader_id,
            copy_id=copy_id,
            librarian_id=librarian_id,
            loan_date=loan_date,
            return_date=return_date
        )

        copy.available = False

        session.add(loan)
        session.commit()
        print(f"Выдача создана: {reader.name} -> {copy.book.title} (ID: {loan.id})")
        return loan

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании выдачи: {e}")
        return None


def get_loan_by_id(session, loan_id):
    """
    Получение выдачи по ID
    """
    try:
        loan = session.query(Loan).filter(Loan.id == loan_id).first()
        if loan:
            return loan
        else:
            print(f"Выдача с ID {loan_id} не найдена")
            return None
    except Exception as e:
        print(f"Ошибка при поиске выдачи: {e}")
        return None


def get_loans_by_reader(session, reader_id, active_only=False):
    """
    Получение всех выдач читателя
    """
    try:
        query = session.query(Loan).filter(Loan.reader_id == reader_id)

        if active_only:
            query = query.filter(Loan.returned == False)

        loans = query.order_by(Loan.loan_date.desc()).all()
        status = "активных" if active_only else ""
        print(f"Найдено {len(loans)} {status}выдач для читателя ID {reader_id}")
        return loans
    except Exception as e:
        print(f"Ошибка при получении выдач читателя: {e}")
        return []


def get_loans_by_copy(session, copy_id):
    """
    Получение всех выдач экземпляра
    """
    try:
        loans = session.query(Loan).filter(Loan.copy_id == copy_id).order_by(Loan.loan_date.desc()).all()
        print(f"Найдено {len(loans)} выдач для экземпляра ID {copy_id}")
        return loans
    except Exception as e:
        print(f"Ошибка при получении выдач экземпляра: {e}")
        return []


def get_active_loans(session, reader_id=None):
    """
    Получение активных выдач
    """
    try:
        query = session.query(Loan).filter(Loan.returned == False)

        if reader_id:
            query = query.filter(Loan.reader_id == reader_id)

        loans = query.order_by(Loan.loan_date).all()
        reader_info = f" читателя ID {reader_id}" if reader_id else ""
        print(f"Найдено {len(loans)} активных выдач{reader_info}")
        return loans
    except Exception as e:
        print(f"Ошибка при получении активных выдач: {e}")
        return []


def get_overdue_loans(session):
    """
    Получение просроченных выдач
    """
    try:
        loans = session.query(Loan).filter(
            and_(
                Loan.returned == False,
                Loan.return_date < date.today()
            )
        ).order_by(Loan.return_date).all()

        print(f"Найдено {len(loans)} просроченных выдач")
        return loans
    except Exception as e:
        print(f"Ошибка при получении просроченных выдач: {e}")
        return []


def update_loan(session, loan_id, **kwargs):
    """
    Обновление данных выдачи ['reader_id', 'copy_id', 'librarian_id', 'loan_date', 'return_date', 'actual_return_date',
                        'returned']
    """
    try:
        loan = get_loan_by_id(session, loan_id)
        if not loan:
            return None

        valid_fields = ['reader_id', 'copy_id', 'librarian_id', 'loan_date', 'return_date', 'actual_return_date',
                        'returned']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                # Особенная логика для возврата книги
                if field == 'returned' and value == True and not loan.returned:
                    loan.actual_return_date = date.today()
                    # Помечаем экземпляр как доступный
                    copy = session.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
                    if copy:
                        copy.available = True

                setattr(loan, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Выдача ID {loan_id} обновлена. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return loan

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении выдачи: {e}")
        return None


def return_loan(session, loan_id, actual_return_date=None):
    """
    Возврат книги по выдаче
    """
    try:
        if actual_return_date is None:
            actual_return_date = date.today()

        return update_loan(session, loan_id, returned=True, actual_return_date=actual_return_date)

    except Exception as e:
        print(f"Ошибка при возврате книги: {e}")
        return None


def delete_loan(session, loan_id):
    """
    Удаление выдачи
    """
    try:
        loan = get_loan_by_id(session, loan_id)
        if not loan:
            return False

        # При удалении выдачи помечаем экземпляр как доступный
        if not loan.returned:
            copy = session.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
            if copy:
                copy.available = True

        session.delete(loan)
        session.commit()
        print(f"Выдача ID {loan_id} успешно удалена")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении выдачи: {e}")
        return False


def create_fine(session, loan_id, librarian_id, amount, issued_date=None):
    """
    Создание штрафа
    """
    try:
        loan = get_loan_by_id(session, loan_id)
        librarian = session.query(Librarian).filter(Librarian.id == librarian_id).first()

        if not loan:
            print(f"Выдача с ID {loan_id} не найдена")
            return None
        if not librarian:
            print(f"Библиотекарь с ID {librarian_id} не найден")
            return None

        existing_fine = session.query(Fine).filter(Fine.loan_id == loan_id).first()
        if existing_fine:
            print(f"Штраф для выдачи ID {loan_id} уже существует")
            return None

        if issued_date is None:
            issued_date = date.today()

        fine = Fine(
            loan_id=loan_id,
            librarian_id=librarian_id,
            amount=amount,
            issued_date=issued_date
        )

        session.add(fine)
        session.commit()
        print(f"Штраф создан: {amount} руб. для выдачи ID {loan_id} (ID штрафа: {fine.id})")
        return fine

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании штрафа: {e}")
        return None


def get_fine_by_id(session, fine_id):
    """
    Получение штрафа по ID
    """
    try:
        fine = session.query(Fine).filter(Fine.id == fine_id).first()
        if fine:
            return fine
        else:
            print(f"Штраф с ID {fine_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске штрафа: {e}")
        return None


def get_fine_by_loan(session, loan_id):
    """
    Получение штрафа по выдаче
    """
    try:
        fine = session.query(Fine).filter(Fine.loan_id == loan_id).first()
        if fine:
            return fine
        else:
            print(f"Штраф для выдачи ID {loan_id} не найден")
            return None
    except Exception as e:
        print(f"Ошибка при поиске штрафа по выдаче: {e}")
        return None


def get_fines_by_reader(session, reader_id, unpaid_only=False):
    """
    Получение штрафов читателя
    """
    try:
        query = session.query(Fine).join(Loan).filter(Loan.reader_id == reader_id)

        if unpaid_only:
            query = query.filter(Fine.paid == False)

        fines = query.order_by(Fine.issued_date.desc()).all()
        status = "неоплаченных" if unpaid_only else ""
        print(f"Найдено {len(fines)} {status}штрафов для читателя ID {reader_id}")
        return fines
    except Exception as e:
        print(f"Ошибка при получении штрафов читателя: {e}")
        return []


def get_unpaid_fines(session, reader_id=None):
    """
    Получение неоплаченных штрафов
    """
    try:
        query = session.query(Fine).filter(Fine.paid == False)

        if reader_id:
            query = query.join(Loan).filter(Loan.reader_id == reader_id)

        fines = query.order_by(Fine.issued_date).all()
        reader_info = f" читателя ID {reader_id}" if reader_id else ""
        print(f"Найдено {len(fines)} неоплаченных штрафов{reader_info}")
        return fines
    except Exception as e:
        print(f"Ошибка при получении неоплаченных штрафов: {e}")
        return []


def update_fine(session, fine_id, **kwargs):
    """
    Обновление данных штрафа
    """
    try:
        fine = get_fine_by_id(session, fine_id)
        if not fine:
            return None

        valid_fields = ['loan_id', 'librarian_id', 'amount', 'issued_date', 'paid']
        updated_fields = []

        for field, value in kwargs.items():
            if field in valid_fields:
                setattr(fine, field, value)
                updated_fields.append(field)

        if updated_fields:
            session.commit()
            print(f"Штраф ID {fine_id} обновлен. Измененные поля: {', '.join(updated_fields)}")
        else:
            print("Нет полей для обновления")

        return fine

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении штрафа: {e}")
        return None


def pay_fine(session, fine_id):
    """
    Оплата штрафа
    """
    return update_fine(session, fine_id, paid=True)


def delete_fine(session, fine_id):
    """
    Удаление штрафа
    """
    try:
        fine = get_fine_by_id(session, fine_id)
        if not fine:
            return False

        session.delete(fine)
        session.commit()
        print(f"Штраф ID {fine_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении штрафа: {e}")
        return False


def calculate_overdue_fine(session, loan_id, daily_rate=100):
    """
    Расчет штрафа за просрочку
    """
    try:
        loan = get_loan_by_id(session, loan_id)
        if not loan or loan.returned:
            return 0

        if loan.return_date >= date.today():
            return 0

        overdue_days = (date.today() - loan.return_date).days
        fine_amount = overdue_days * daily_rate

        print(f"Просрочка: {overdue_days} дней, штраф: {fine_amount} руб.")
        return fine_amount

    except Exception as e:
        print(f"Ошибка при расчете штрафа: {e}")
        return 0


def auto_create_overdue_fines(session, daily_rate=10):
    """
    Автоматическое создание штрафов для просроченных выдач
    """
    try:
        overdue_loans = get_overdue_loans(session)
        created_fines = []

        for loan in overdue_loans:
            # Проверяем, нет ли уже штрафа для этой выдачи
            existing_fine = get_fine_by_loan(session, loan.id)
            if existing_fine:
                continue

            # Создаем штраф
            fine_amount = calculate_overdue_fine(session, loan.id, daily_rate)
            if fine_amount > 0:
                # Используем библиотекаря, который выдавал книгу, или первого доступного
                librarian_id = loan.librarian_id
                if not librarian_id:
                    first_librarian = session.query(Librarian).first()
                    librarian_id = first_librarian.id if first_librarian else None

                if librarian_id:
                    fine = create_fine(session, loan.id, librarian_id, fine_amount)
                    if fine:
                        created_fines.append(fine)

        print(f"Создано {len(created_fines)} штрафов за просрочку")
        return created_fines

    except Exception as e:
        print(f"Ошибка при автоматическом создании штрафов: {e}")
        return []


def get_loan_statistics(session, reader_id=None):
    """
    Получение статистики по выдачам
    """
    try:
        query = session.query(Loan)

        if reader_id:
            query = query.filter(Loan.reader_id == reader_id)
            reader_info = f" читателя ID {reader_id}"
        else:
            reader_info = ""

        total = query.count()
        active = query.filter(Loan.returned == False).count()
        returned = total - active

        # Просроченные
        overdue = query.filter(
            and_(
                Loan.returned == False,
                Loan.return_date < date.today()
            )
        ).count()

        print(f"Статистика выдач{reader_info}:")
        print(f"  Всего выдач: {total}")
        print(f"  Активных: {active}")
        print(f"  Возвращенных: {returned}")
        print(f"  Просроченных: {overdue}")

        return {
            'total': total,
            'active': active,
            'returned': returned,
            'overdue': overdue
        }

    except Exception as e:
        print(f"Ошибка при получении статистики выдач: {e}")
        return {}


def get_fine_statistics(session, reader_id=None):
    """
    Получение статистики по штрафам
    """
    try:
        query = session.query(Fine)

        if reader_id:
            query = query.join(Loan).filter(Loan.reader_id == reader_id)
            reader_info = f" читателя ID {reader_id}"
        else:
            reader_info = ""

        total = query.count()
        paid = query.filter(Fine.paid == True).count()
        unpaid = total - paid

        # Общая сумма - исправлено использование func
        total_amount = session.query(func.sum(Fine.amount)).scalar() or 0
        unpaid_amount = session.query(func.sum(Fine.amount)).filter(Fine.paid == False).scalar() or 0

        print(f"Статистика штрафов{reader_info}:")
        print(f"  Всего штрафов: {total}")
        print(f"  Оплаченных: {paid}")
        print(f"  Неоплаченных: {unpaid}")
        print(f"  Общая сумма: {total_amount} руб.")
        print(f"  Сумма неоплаченных: {unpaid_amount} руб.")

        return {
            'total': total,
            'paid': paid,
            'unpaid': unpaid,
            'total_amount': float(total_amount),
            'unpaid_amount': float(unpaid_amount)
        }

    except Exception as e:
        print(f"Ошибка при получении статистики штрафов: {e}")
        return {}


def print_loan_info(loan):
    """
    Вывод информации о выдаче
    """
    if not loan:
        print("Выдача не найдена")
        return

    reader_name = loan.reader.name if loan.reader else "Неизвестно"
    book_title = loan.copy.book.title if loan.copy and loan.copy.book else "Неизвестно"
    librarian_name = loan.librarian.name if loan.librarian else "Неизвестно"

    print(f"ID выдачи: {loan.id}")
    print(f"Читатель: {reader_name} (ID: {loan.reader_id})")
    print(f"Книга: {book_title} (Экземпляр: {loan.copy.inventory_number if loan.copy else 'N/A'})")
    print(f"Библиотекарь: {librarian_name}")
    print(f"Дата выдачи: {loan.loan_date}")
    print(f"Дата возврата: {loan.return_date}")
    print(f"Фактическая дата возврата: {loan.actual_return_date or 'Не возвращена'}")
    print(f"Статус: {'Возвращена' if loan.returned else 'Активна'}")
    print(f"Просрочена: {'Да' if not loan.returned and loan.return_date < date.today() else 'Нет'}")
    print("-" * 50)


def print_fine_info(fine):
    """
    Вывод информации о штрафе
    """
    if not fine:
        print("Штраф не найден")
        return

    reader_name = fine.loan.reader.name if fine.loan and fine.loan.reader else "Неизвестно"
    librarian_name = fine.librarian.name if fine.librarian else "Неизвестно"

    print(f"ID штрафа: {fine.id}")
    print(f"Выдача ID: {fine.loan_id}")
    print(f"Читатель: {reader_name}")
    print(f"Библиотекарь: {librarian_name}")
    print(f"Сумма: {fine.amount} руб.")
    print(f"Дата выдачи штрафа: {fine.issued_date}")
    print(f"Оплачен: {'Да' if fine.paid else 'Нет'}")
    print("-" * 50)


def get_all_loans(session):
    """
    Получение всех выдач
    """
    try:
        loans = session.query(Loan).order_by(Loan.loan_date.desc()).all()
        return loans
    except Exception as e:
        print(f"Ошибка при получении всех выдач: {e}")
        return []


def get_returned_loans(session):
    """
    Получение возвращенных выдач
    """
    try:
        loans = session.query(Loan).filter(Loan.returned == True).order_by(Loan.loan_date.desc()).all()
        return loans
    except Exception as e:
        print(f"Ошибка при получении возвращенных выдач: {e}")
        return []


def get_all_fines(session):
    """
    Получение всех штрафов
    """
    try:
        fines = session.query(Fine).order_by(Fine.issued_date.desc()).all()
        return fines
    except Exception as e:
        print(f"Ошибка при получении всех штрафов: {e}")
        return []


# Функции для работы с книгами (дополнение к существующим)
def get_all_books(session):
    """Получить все книги с информацией об экземплярах"""
    try:
        books = session.query(Book).order_by(Book.title).all()
        return books
    except Exception as e:
        print(f"Ошибка при получении книг: {e}")
        return []


def get_books_count(session):
    """Получить общее количество книг"""
    try:
        return session.query(Book).count()
    except Exception as e:
        print(f"Ошибка при подсчете книг: {e}")
        return 0


# Функции для работы с экземплярами книг
def get_all_book_copies(session):
    """Получить все экземпляры книг"""
    try:
        copies = session.query(BookCopy).order_by(BookCopy.inventory_number).all()
        return copies
    except Exception as e:
        print(f"Ошибка при получении экземпляров: {e}")
        return []



def get_available_copies_count(session, book_id):
    """Получить количество доступных экземпляров книги"""
    try:
        count = session.query(BookCopy).filter(
            BookCopy.book_id == book_id,
            BookCopy.available == True
        ).count()
        return count
    except Exception as e:
        print(f"Ошибка при подсчете доступных экземпляров: {e}")
        return 0


def create_book_copy(session, book_id, inventory_number, condition='Хорошее', location=None):
    """Создать новый экземпляр книги"""
    try:
        # Проверяем уникальность инвентарного номера
        existing_copy = session.query(BookCopy).filter(
            BookCopy.inventory_number == inventory_number
        ).first()
        if existing_copy:
            raise ValueError(f"Экземпляр с инвентарным номером '{inventory_number}' уже существует")

        copy = BookCopy(
            book_id=book_id,
            inventory_number=inventory_number,
            condition=condition,
            location=location,
            available=True
        )

        session.add(copy)
        session.commit()
        return copy
    except Exception as e:
        session.rollback()
        raise e


def update_book_copy_status(session, copy_id, status):
    """Обновить статус экземпляра"""
    try:
        copy = session.query(BookCopy).filter(BookCopy.id == copy_id).first()
        if not copy:
            raise ValueError("Экземпляр не найден")

        copy.available = (status == 'available')
        session.commit()
        return copy
    except Exception as e:
        session.rollback()
        raise e


def write_off_copy(session, copy_id):
    """Списать экземпляр"""
    try:
        copy = session.query(BookCopy).filter(BookCopy.id == copy_id).first()
        if not copy:
            raise ValueError("Экземпляр не найден")

        # Помечаем как недоступный (списанный)
        copy.available = False
        session.commit()
        return copy
    except Exception as e:
        session.rollback()
        raise e


def get_active_loan_by_copy(session, copy_id):
    """Получить активную выдачу для экземпляра"""
    try:
        loan = session.query(Loan).filter(
            Loan.copy_id == copy_id,
            Loan.returned == False
        ).first()
        return loan
    except Exception as e:
        print(f"Ошибка при поиске активной выдачи: {e}")
        return None


if __name__ == "__main__":
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"
    engine = create_engine(DATABASE_URL, echo=False)
    session = get_session()
    # create_librarian(session, "Королева Валерия Витальевна", "admin@mail.ru", "admin", "Администратор")