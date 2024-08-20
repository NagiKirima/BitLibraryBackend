-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS Users (
    id_user UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    phone_number VARCHAR(20) NOT NULL UNIQUE CHECK (phone_number ~ '^7[0-9]{10}$'),
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы авторов
CREATE TABLE IF NOT EXISTS Authors (
    id_author UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    author_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы жанров
CREATE TABLE IF NOT EXISTS Genres (
    id_genre UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    genre_name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы книг
CREATE TABLE IF NOT EXISTS Books (
    id_book UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_book_name ON Books(title);

-- Создание таблицы связи книг и авторов
CREATE TABLE IF NOT EXISTS BookAuthors (
    id_book UUID NOT NULL,
    id_author UUID NOT NULL,
    PRIMARY KEY (id_book, id_author),
    FOREIGN KEY (id_book) REFERENCES Books(id_book) ON DELETE CASCADE,
    FOREIGN KEY (id_author) REFERENCES Authors(id_author) ON DELETE CASCADE,
    CONSTRAINT unique_book_author_combination UNIQUE (id_book, id_author)
);

-- Создание таблицы связи книг и жанров
CREATE TABLE IF NOT EXISTS BookGenres (
    id_book UUID NOT NULL,
    id_genre UUID NOT NULL,
    PRIMARY KEY (id_book, id_genre),
    FOREIGN KEY (id_book) REFERENCES Books(id_book) ON DELETE CASCADE,
    FOREIGN KEY (id_genre) REFERENCES Genres(id_genre) ON DELETE CASCADE,
    CONSTRAINT unique_book_genre_combination UNIQUE (id_book, id_genre)
);

-- Виртуальная таблица для объединения информации о книгах
CREATE OR REPLACE VIEW BookDetails AS
WITH UniqueAuthors AS (
    SELECT 
        b.id_book,
        jsonb_agg(DISTINCT jsonb_build_object(
            'id_author', a.id_author,
            'author_name', a.author_name
        )) AS authors
    FROM 
        Books b
    LEFT JOIN 
        BookAuthors ba ON b.id_book = ba.id_book
    LEFT JOIN 
        Authors a ON ba.id_author = a.id_author
    GROUP BY 
        b.id_book
),
UniqueGenres AS (
    SELECT 
        b.id_book,
        jsonb_agg(DISTINCT jsonb_build_object(
            'id_genre', g.id_genre,
            'genre_name', g.genre_name
        )) AS genres
    FROM 
        Books b
    LEFT JOIN 
        BookGenres bg ON b.id_book = bg.id_book
    LEFT JOIN 
        Genres g ON bg.id_genre = g.id_genre
    GROUP BY 
        b.id_book
)
SELECT 
    b.id_book,
    b.title,
    ua.authors,
    ug.genres
FROM 
    Books b
LEFT JOIN 
    UniqueAuthors ua ON b.id_book = ua.id_book
LEFT JOIN 
    UniqueGenres ug ON b.id_book = ug.id_book;


-- Создание таблицы учета взятия-возвращения книг
CREATE TABLE IF NOT EXISTS BorrowReturnLogs (
    id_borrow UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    id_book UUID NOT NULL,
    id_user UUID NOT NULL,
    borrow_date DATE NOT NULL,
    return_date DATE NOT NULL,
    is_returned BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_book) REFERENCES Books(id_book) ON DELETE CASCADE,
    FOREIGN KEY (id_user) REFERENCES Users(id_user) ON DELETE CASCADE
);

-- Функция для обновления временной метки
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP; 
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Users
CREATE OR REPLACE TRIGGER update_users_updated_at BEFORE UPDATE
    ON Users FOR EACH ROW EXECUTE FUNCTION 
    update_updated_at_column();

-- Authors
CREATE OR REPLACE TRIGGER update_authors_updated_at BEFORE UPDATE
    ON Authors FOR EACH ROW EXECUTE FUNCTION 
    update_updated_at_column();

-- Genres
CREATE OR REPLACE TRIGGER update_genres_updated_at BEFORE UPDATE
    ON Genres FOR EACH ROW EXECUTE FUNCTION 
    update_updated_at_column();

-- Books
CREATE OR REPLACE TRIGGER update_books_updated_at BEFORE UPDATE
    ON Books FOR EACH ROW EXECUTE FUNCTION 
    update_updated_at_column();

-- BorrowReturnLogs
CREATE OR REPLACE TRIGGER update_borrowlogs_updated_at BEFORE UPDATE
    ON BorrowReturnLogs FOR EACH ROW EXECUTE FUNCTION 
    update_updated_at_column();