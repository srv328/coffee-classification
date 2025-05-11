-- Создание базы данных
DROP DATABASE IF EXISTS coffee_classification;
CREATE DATABASE IF NOT EXISTS coffee_classification;
USE coffee_classification;

-- Таблица сортов кофе
CREATE TABLE IF NOT EXISTS coffee_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица характеристик (теперь без привязки к типу кофе)
CREATE TABLE IF NOT EXISTS characteristics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type ENUM('numeric', 'categorical') NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица возможных значений для категориальных характеристик
CREATE TABLE IF NOT EXISTS categorical_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    characteristic_id INT NOT NULL,
    value VARCHAR(100) NOT NULL,
    FOREIGN KEY (characteristic_id) REFERENCES characteristics(id),
    UNIQUE KEY unique_value_per_characteristic (characteristic_id, value)
);

-- Таблица числовых характеристик для сортов кофе
CREATE TABLE IF NOT EXISTS coffee_numeric_characteristics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coffee_type_id INT NOT NULL,
    characteristic_id INT NOT NULL,
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (coffee_type_id) REFERENCES coffee_types(id) ON DELETE CASCADE,
    FOREIGN KEY (characteristic_id) REFERENCES characteristics(id) ON DELETE CASCADE,
    UNIQUE KEY unique_numeric_char_per_coffee (coffee_type_id, characteristic_id)
);

-- Таблица категориальных характеристик для сортов кофе
CREATE TABLE IF NOT EXISTS coffee_categorical_characteristics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coffee_type_id INT NOT NULL,
    characteristic_id INT NOT NULL,
    value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (coffee_type_id) REFERENCES coffee_types(id) ON DELETE CASCADE,
    FOREIGN KEY (characteristic_id) REFERENCES characteristics(id) ON DELETE CASCADE
); 

-- Вставка базовых сортов кофе
INSERT INTO coffee_types (name) VALUES
('Арабика'),
('Робуста'),
('Либерика'),
('Колумбия Супремо'),
('Бразилия Сантос'),
('Эфиопия Иргачеффе'),
('Гондурас SHG'),
('Кения АА');

-- Вставка характеристик (если еще не вставлены)
INSERT IGNORE INTO characteristics (name, type) VALUES
('acidity', 'numeric'),
('body', 'numeric'),
('aroma', 'categorical'),
('flavor', 'categorical'),
('aftertaste', 'categorical'),
('roast_level', 'numeric');

-- Вставка числовых характеристик для Арабики
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(1, 1, 4, 7),  -- Кислотность
(1, 2, 6, 8),  -- Тело
(1, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Арабики
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(1, 3, 'Цветочный'),
(1, 3, 'Фруктовый'),
(1, 4, 'Сладкий'),
(1, 4, 'Кислый'),
(1, 5, 'Чистое'),
(1, 5, 'Сладкое');

-- Вставка числовых характеристик для Робусты
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(2, 1, 8, 9),  -- Кислотность
(2, 2, 5, 8),  -- Тело
(2, 6, 8, 9);  -- Обжарка

-- Вставка категориальных характеристик для Робусты
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(2, 3, 'Ореховый'),
(2, 3, 'Пряный'),
(2, 4, 'Горький'),
(2, 4, 'Соленый'),
(2, 5, 'Горьковатое'),
(2, 5, 'Сухое');

-- Вставка числовых характеристик для Либерики
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(3, 1, 3, 5),  -- Кислотность
(3, 2, 3, 6),  -- Тело
(3, 6, 6, 7);  -- Обжарка

-- Вставка категориальных характеристик для Либерики
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(3, 3, 'Древесный'),
(3, 4, 'Горький'),
(3, 5, 'Сухое'),
(3, 5, 'Короткое');

-- Вставка числовых характеристик для Колумбия Супремо
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(4, 1, 6, 8),  -- Кислотность
(4, 2, 7, 8),  -- Тело
(4, 6, 4, 6);  -- Обжарка

-- Вставка категориальных характеристик для Колумбия Супремо
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(4, 3, 'Фруктовый'),
(4, 3, 'Шоколадный'),
(4, 4, 'Сладкий'),
(4, 4, 'Фруктовый'),
(4, 5, 'Чистое'),
(4, 5, 'Длительное');

-- Вставка числовых характеристик для Бразилия Сантос
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(5, 1, 5, 7),  -- Кислотность
(5, 2, 6, 7),  -- Тело
(5, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Бразилия Сантос
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(5, 3, 'Ореховый'),
(5, 3, 'Шоколадный'),
(5, 4, 'Сладкий'),
(5, 4, 'Ореховый'),
(5, 5, 'Сладкое'),
(5, 5, 'Длительное');

-- Вставка числовых характеристик для Эфиопия Иргачеффе
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(6, 1, 7, 9),  -- Кислотность
(6, 2, 5, 7),  -- Тело
(6, 6, 2, 4);  -- Обжарка

-- Вставка категориальных характеристик для Эфиопия Иргачеффе
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(6, 3, 'Цветочный'),
(6, 3, 'Пряный'),
(6, 4, 'Кислый'),
(6, 4, 'Фруктовый'),
(6, 5, 'Чистое'),
(6, 5, 'Длительное');

-- Вставка числовых характеристик для Гондурас SHG
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(7, 1, 6, 7),  -- Кислотность
(7, 2, 6, 7),  -- Тело
(7, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Гондурас SHG
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(7, 3, 'Шоколадный'),
(7, 3, 'Пряный'),
(7, 4, 'Сладкий'),
(7, 4, 'Шоколадный'),
(7, 5, 'Сладкое'),
(7, 5, 'Длительное');

-- Вставка числовых характеристик для Кения АА
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(8, 1, 8, 9),  -- Кислотность
(8, 2, 6, 7),  -- Тело
(8, 6, 4, 6);  -- Обжарка

-- Вставка категориальных характеристик для Кения АА
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, value) VALUES
(8, 3, 'Фруктовый'),
(8, 3, 'Цветочный'),
(8, 4, 'Кислый'),
(8, 4, 'Фруктовый'),
(8, 5, 'Чистое'),
(8, 5, 'Длительное'); 