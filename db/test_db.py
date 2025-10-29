from db_config import DB_HOST, DB_NAME, DB_USER, DB_PORT, DB_PASS
from sqlalchemy import create_engine
import db_funcs as db
from models import Base


DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"

if __name__ == "__main__":
    print("Hello, World!")
    engine = create_engine(DATABASE_URL, echo=False)
    session = db.get_session()
    db.set_book_genres(session, 1, [1, 3])