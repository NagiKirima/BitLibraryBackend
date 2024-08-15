-- Очищаем таблицы
TRUNCATE TABLE BookGenres CASCADE;
TRUNCATE TABLE BorrowReturnLogs CASCADE;
TRUNCATE TABLE Books CASCADE;
TRUNCATE TABLE Genres CASCADE;
TRUNCATE TABLE Authors CASCADE;
TRUNCATE TABLE Users CASCADE;

-- Генерация пользователей
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..10 LOOP
        INSERT INTO Users (full_name, birth_date, address, phone_number) VALUES 
        (
            'User ' || i,
            (CURRENT_DATE - ((RANDOM() * 3650)::int)),
            'Address ' || i,
            '123-456-789' || (i::text)
        );
    END LOOP;
END $$;

-- Генерация авторов
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..5 LOOP
        INSERT INTO Authors (author_name) VALUES 
        (
            'Author ' || i
        );
    END LOOP;
END $$;

-- Генерация жанров
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..8 LOOP
        INSERT INTO Genres (genre_name) VALUES 
        (
            'Genre ' || i
        );
    END LOOP;
END $$;

-- Генерация книг
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..20 LOOP
        INSERT INTO Books (title, is_available) VALUES 
        (
            'Book Title ' || i,
            (RANDOM() > 0.5)  -- Случайный статус
        );
    END LOOP;
END $$;

-- Генерация отношений между книгами и авторами
DO $$
DECLARE
    book_id UUID;
    author_id UUID;
BEGIN
    FOR book_id IN SELECT id_book FROM Books LOOP
        -- Генерация от 1 до 3 авторов для каждой книги
        FOR author_id IN SELECT id_author FROM Authors ORDER BY RANDOM() LIMIT (1 + (RANDOM() * 2)::int) LOOP
            INSERT INTO BookAuthors (id_book, id_author) VALUES (book_id, author_id);
        END LOOP;
    END LOOP;
END $$;

-- Генерация отношений между книгами и жанрами
DO $$
DECLARE
    book_id UUID;
    genre_id UUID;
BEGIN
    FOR book_id IN SELECT id_book FROM Books LOOP
        -- Генерация от 1 до 3 жанров для каждой книги
        FOR genre_id IN SELECT id_genre FROM Genres ORDER BY RANDOM() LIMIT (1 + (RANDOM() * 2)::int) LOOP
            INSERT INTO BookGenres (id_book, id_genre) VALUES (book_id, genre_id);
        END LOOP;
    END LOOP;
END $$;

-- Генерация логов взятия и возврата книг
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..30 LOOP
        INSERT INTO BorrowReturnLogs (id_book, id_user, borrow_date, return_date) VALUES 
        (
            (SELECT id_book FROM Books ORDER BY RANDOM() LIMIT 1),  -- Случайная книга
            (SELECT id_user FROM Users ORDER BY RANDOM() LIMIT 1),  -- Случайный пользователь
            (CURRENT_DATE - (RANDOM() * 30)::int),  -- Случайная дата займа в пределах 30 дней назад
            (CURRENT_DATE - (RANDOM() * 30)::int) + (1 + (RANDOM() * 10)::int)  -- Случайная дата возврата от 1 до 10 дней позже
        );
    END LOOP;
END $$;
