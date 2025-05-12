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

-- Таблица характеристик
CREATE TABLE IF NOT EXISTS characteristics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type ENUM('numeric', 'categorical') NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица глобальных ограничений для числовых характеристик
CREATE TABLE IF NOT EXISTS numeric_characteristic_limits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    characteristic_id INT NOT NULL,
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    FOREIGN KEY (characteristic_id) REFERENCES characteristics(id),
    UNIQUE KEY unique_numeric_char_limits (characteristic_id)
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
    categorical_value_id INT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (coffee_type_id) REFERENCES coffee_types(id) ON DELETE CASCADE,
    FOREIGN KEY (characteristic_id) REFERENCES characteristics(id) ON DELETE CASCADE,
    FOREIGN KEY (categorical_value_id) REFERENCES categorical_values(id) ON DELETE CASCADE,
    UNIQUE KEY unique_categorical_char_per_coffee (coffee_type_id, characteristic_id, categorical_value_id)
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

-- Вставка характеристик
INSERT INTO characteristics (name, type) VALUES
('Кислотность', 'numeric'),
('Тело', 'numeric'),
('Аромат', 'categorical'),
('Вкус', 'categorical'),
('Послевкусие', 'categorical'),
('Степень обжарки', 'numeric');

-- Вставка глобальных ограничений для числовых характеристик
INSERT INTO numeric_characteristic_limits (characteristic_id, min_value, max_value) VALUES
(1, 1, 10),  -- Кислотность: от 1 до 10
(2, 1, 10),  -- Тело: от 1 до 10
(6, 1, 10);  -- Степень обжарки: от 1 до 10

-- Вставка глобальных значений категориальных характеристик
INSERT INTO categorical_values (characteristic_id, value) VALUES
-- Аромат (id=3)
(3, 'Цветочный'),
(3, 'Фруктовый'),
(3, 'Ореховый'),
(3, 'Шоколадный'),
(3, 'Пряный'),
(3, 'Древесный'),
-- Вкус (id=4)
(4, 'Сладкий'),
(4, 'Кислый'),
(4, 'Горький'),
(4, 'Соленый'),
(4, 'Фруктовый'),
(4, 'Ореховый'),
(4, 'Шоколадный'),
-- Послевкусие (id=5)
(5, 'Чистое'),
(5, 'Сладкое'),
(5, 'Горьковатое'),
(5, 'Сухое'),
(5, 'Короткое'),
(5, 'Длительное');

-- Вставка числовых характеристик для Арабики
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(1, 1, 4, 7),  -- Кислотность
(1, 2, 6, 8),  -- Тело
(1, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Арабики
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(1, 3, 1),  -- Аромат: Цветочный
(1, 3, 2),  -- Аромат: Фруктовый
(1, 4, 7),  -- Вкус: Сладкий
(1, 4, 8),  -- Вкус: Кислый
(1, 5, 13), -- Послевкусие: Чистое
(1, 5, 14); -- Послевкусие: Сладкое

-- Вставка числовых характеристик для Робусты
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(2, 1, 8, 9),  -- Кислотность
(2, 2, 5, 8),  -- Тело
(2, 6, 8, 9);  -- Обжарка

-- Вставка категориальных характеристик для Робусты
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(2, 3, 3),  -- Аромат: Ореховый
(2, 3, 5),  -- Аромат: Пряный
(2, 4, 9),  -- Вкус: Горький
(2, 4, 10), -- Вкус: Соленый
(2, 5, 15), -- Послевкусие: Горьковатое
(2, 5, 16); -- Послевкусие: Сухое

-- Вставка числовых характеристик для Либерики
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(3, 1, 3, 5),  -- Кислотность
(3, 2, 3, 6),  -- Тело
(3, 6, 6, 7);  -- Обжарка

-- Вставка категориальных характеристик для Либерики
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(3, 3, 6),  -- Аромат: Древесный
(3, 4, 9),  -- Вкус: Горький
(3, 5, 16), -- Послевкусие: Сухое
(3, 5, 17); -- Послевкусие: Короткое

-- Вставка числовых характеристик для Колумбия Супремо
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(4, 1, 6, 8),  -- Кислотность
(4, 2, 7, 8),  -- Тело
(4, 6, 4, 6);  -- Обжарка

-- Вставка категориальных характеристик для Колумбия Супремо
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(4, 3, 2),  -- Аромат: Фруктовый
(4, 3, 4),  -- Аромат: Шоколадный
(4, 4, 7),  -- Вкус: Сладкий
(4, 4, 11), -- Вкус: Фруктовый
(4, 5, 13), -- Послевкусие: Чистое
(4, 5, 18); -- Послевкусие: Длительное

-- Вставка числовых характеристик для Бразилия Сантос
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(5, 1, 5, 7),  -- Кислотность
(5, 2, 6, 7),  -- Тело
(5, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Бразилия Сантос
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(5, 3, 3),  -- Аромат: Ореховый
(5, 3, 4),  -- Аромат: Шоколадный
(5, 4, 7),  -- Вкус: Сладкий
(5, 4, 12), -- Вкус: Ореховый
(5, 5, 14), -- Послевкусие: Сладкое
(5, 5, 18); -- Послевкусие: Длительное

-- Вставка числовых характеристик для Эфиопия Иргачеффе
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(6, 1, 7, 9),  -- Кислотность
(6, 2, 5, 7),  -- Тело
(6, 6, 2, 4);  -- Обжарка

-- Вставка категориальных характеристик для Эфиопия Иргачеффе
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(6, 3, 1),  -- Аромат: Цветочный
(6, 3, 5),  -- Аромат: Пряный
(6, 4, 8),  -- Вкус: Кислый
(6, 4, 11), -- Вкус: Фруктовый
(6, 5, 13), -- Послевкусие: Чистое
(6, 5, 18); -- Послевкусие: Длительное

-- Вставка числовых характеристик для Гондурас SHG
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(7, 1, 6, 7),  -- Кислотность
(7, 2, 6, 7),  -- Тело
(7, 6, 3, 5);  -- Обжарка

-- Вставка категориальных характеристик для Гондурас SHG
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(7, 3, 4),  -- Аромат: Шоколадный
(7, 3, 5),  -- Аромат: Пряный
(7, 4, 7),  -- Вкус: Сладкий
(7, 4, 13), -- Вкус: Шоколадный
(7, 5, 14), -- Послевкусие: Сладкое
(7, 5, 18); -- Послевкусие: Длительное

-- Вставка числовых характеристик для Кения АА
INSERT INTO coffee_numeric_characteristics (coffee_type_id, characteristic_id, min_value, max_value) VALUES
(8, 1, 8, 9),  -- Кислотность
(8, 2, 6, 7),  -- Тело
(8, 6, 4, 6);  -- Обжарка

-- Вставка категориальных характеристик для Кения АА
INSERT INTO coffee_categorical_characteristics (coffee_type_id, characteristic_id, categorical_value_id) VALUES
(8, 3, 1),  -- Аромат: Цветочный
(8, 3, 2),  -- Аромат: Фруктовый
(8, 4, 8),  -- Вкус: Кислый
(8, 4, 11), -- Вкус: Фруктовый
(8, 5, 13), -- Послевкусие: Чистое
(8, 5, 18); -- Послевкусие: Длительное 