-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS Users (
    id_user UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    phone_number VARCHAR(20) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE,
    address VARCHAR(255),
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
    genre_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы книг
CREATE TABLE IF NOT EXISTS Books (
    id_book UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    title VARCHAR(255) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы связи книг и авторов
CREATE TABLE IF NOT EXISTS BookAuthors (
    id_book UUID,
    id_author UUID,
    PRIMARY KEY (id_book, id_author),
    FOREIGN KEY (id_book) REFERENCES Books(id_book) ON DELETE CASCADE,
    FOREIGN KEY (id_author) REFERENCES Authors(id_author) ON DELETE CASCADE
);

-- Создание таблицы связи книг и жанров
CREATE TABLE IF NOT EXISTS BookGenres (
    id_book UUID,
    id_genre UUID,
    PRIMARY KEY (id_book, id_genre),
    FOREIGN KEY (id_book) REFERENCES Books(id_book) ON DELETE CASCADE,
    FOREIGN KEY (id_genre) REFERENCES Genres(id_genre) ON DELETE CASCADE
);

-- Виртуальная таблица для объединения информации о книгах
CREATE OR REPLACE VIEW BookDetails AS
SELECT 
    b.id_book,
    b.title,
    b.is_available,
    b.created_at AS book_created_at,
    b.updated_at AS book_updated_at,
    a.author_name,
    a.created_at AS author_created_at,
    a.updated_at AS author_updated_at,
    g.genre_name,
    g.created_at AS genre_created_at,
    g.updated_at AS genre_updated_at
FROM Books b
LEFT JOIN BookAuthors ba ON b.id_book = ba.id_book
LEFT JOIN Authors a ON ba.id_author = a.id_author
LEFT JOIN BookGenres bg ON b.id_book = bg.id_book
LEFT JOIN Genres g ON bg.id_genre = g.id_genre;


-- Создание таблицы учета взятия-возвращения книг
CREATE TABLE IF NOT EXISTS BorrowReturnLogs (
    id_log UUID PRIMARY KEY DEFAULT (gen_random_uuid()),
    id_book UUID,
    id_user UUID,
    borrow_date DATE NOT NULL,
    return_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_book) REFERENCES Books(id_book),
    FOREIGN KEY (id_user) REFERENCES Users(id_user)
);
