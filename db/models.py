from sqlalchemy import (
    create_engine, Column, Integer, String, Date, Text,
    Boolean, Numeric, ForeignKey, Table, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from datetime import date


class Base(DeclarativeBase):
    pass


# Ассоциативная таблица для связи многие-ко-многим между Books и Genres
genres_books = Table(
    'genres_books',
    Base.metadata,
    Column('genre_id', Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True)
)


class Reader(Base):
    __tablename__ = 'readers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(20))
    registration_date = Column(Date, default=date.today)

    loans = relationship("Loan", back_populates="reader", cascade="all, delete-orphan")
    # reviews = relationship("BookReview", back_populates="reader", cascade="all, delete-orphan")

    def repr(self):
        return f"<Reader(id={self.id}, name='{self.name}')>"


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    isbn = Column(String(20), unique=True)
    publish_year = Column(Integer)
    description = Column(Text)
    available = Column(Boolean, default=True)

    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    # reviews = relationship("BookReview", back_populates="book", cascade="all, delete-orphan")
    genres = relationship("Genre", secondary=genres_books, back_populates="books")

    def repr(self):
        return f"<Book(id={self.id}, title='{self.title}')>"


class BookCopy(Base):
    __tablename__ = 'book_copies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    inventory_number = Column(String(50), unique=True, nullable=False)
    condition = Column(String(50), default='good')
    location = Column(String(100))
    available = Column(Boolean, default=True)
    status = Column(String(20), default='available')

    book = relationship("Book", back_populates="copies")
    loans = relationship("Loan", back_populates="copy", cascade="all, delete-orphan")

    def repr(self):
        return f"<BookCopy(id={self.id}, inventory='{self.inventory_number}')>"


class Genre(Base):
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    books = relationship("Book", secondary=genres_books, back_populates="genres")

    def repr(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Librarian(Base):
    __tablename__ = 'librarians'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    hire_date = Column(Date, default=date.today)
    position = Column(String(100))

    loans = relationship("Loan", back_populates="librarian")
    fines = relationship("Fine", back_populates="librarian")

    def repr(self):
        return f"<Librarian(id={self.id}, name='{self.name}')>"


class Loan(Base):
    __tablename__ = 'loans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column(Integer, ForeignKey('readers.id', ondelete='CASCADE'), nullable=False)
    copy_id = Column(Integer, ForeignKey('book_copies.id', ondelete='CASCADE'), nullable=False)
    librarian_id = Column(Integer, ForeignKey('librarians.id', ondelete='SET NULL'))
    loan_date = Column(Date, nullable=False)
    return_date = Column(Date)
    actual_return_date = Column(Date)
    returned = Column(Boolean, default=False)

    reader = relationship("Reader", back_populates="loans")
    copy = relationship("BookCopy", back_populates="loans")
    librarian = relationship("Librarian", back_populates="loans")
    fine = relationship("Fine", back_populates="loan", uselist=False, cascade="all, delete-orphan")

    def repr(self):
        return f"<Loan(id={self.id}, reader_id={self.reader_id}, copy_id={self.copy_id})>"


# class BookReview(Base):
#     __tablename__ = 'book_reviews'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
#     reader_id = Column(Integer, ForeignKey('readers.id', ondelete='CASCADE'), nullable=False)
#     review_text = Column(Text)
#     rating = Column(Integer)
#     review_date = Column(Date, default=date.today)

#     book = relationship("Book", back_populates="reviews")
#     reader = relationship("Reader", back_populates="reviews")

#     table_args = (
#         CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
#     )

#     def repr(self):
#         return f"<BookReview(id={self.id}, book_id={self.book_id}, rating={self.rating})>"


class Fine(Base):
    __tablename__ = 'fines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey('loans.id', ondelete='CASCADE'), nullable=False)
    librarian_id = Column(Integer, ForeignKey('librarians.id', ondelete='SET NULL'))
    amount = Column(Numeric(6, 2), nullable=False)
    issued_date = Column(Date, default=date.today)
    paid = Column(Boolean, default=False)

    loan = relationship("Loan", back_populates="fine")
    librarian = relationship("Librarian", back_populates="fines")

    def repr(self):
        return f"<Fine(id={self.id}, amount={self.amount}, paid={self.paid})>"


