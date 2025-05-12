import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import tensorflow as tf
from tensorflow.keras import layers, models
import mysql.connector
from config import db_config
import json
import os
from datetime import datetime
import pandas as pd
import joblib
from db import get_db_connection

class CoffeeClassifier:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = None
        self.characteristic_mapping = {'numeric': {}, 'categorical': {}}
        self.n_classes = 0
        self.numeric_features = []
        self.categorical_features = {}
        self.model_initialized = False
        self.last_training_time = None
        
        # Инициализация в правильном порядке
        self.load_characteristic_mapping()  # Сначала загружаем маппинг
        self.load_characteristics()         # Затем характеристики
        self.initialize_model()            # Инициализируем модель
        self.load_model()                  # Загружаем или создаем модель
        self.load_encoders()               # Загружаем энкодеры
        self.load_scaler()                 # Загружаем scaler

    def load_characteristics(self):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Получаем числовые характеристики
            cursor.execute("""
                SELECT DISTINCT c.id, c.name 
                FROM characteristics c
                INNER JOIN coffee_numeric_characteristics cnc ON c.id = cnc.characteristic_id
                WHERE c.type = 'numeric'
                ORDER BY c.id
            """)
            self.numeric_features = [(row[0], row[1]) for row in cursor.fetchall()]
            
            # Получаем категориальные характеристики
            cursor.execute("""
                SELECT c.id, c.name, GROUP_CONCAT(DISTINCT cv.value ORDER BY cv.value) as possible_values
                FROM characteristics c
                INNER JOIN coffee_categorical_characteristics ccc ON c.id = ccc.characteristic_id
                LEFT JOIN categorical_values cv ON c.id = cv.characteristic_id
                WHERE c.type = 'categorical'
                GROUP BY c.id, c.name
                ORDER BY c.id
            """)
            for row in cursor.fetchall():
                char_id, char_name, values = row
                if values:
                    self.categorical_features[char_id] = {
                        'name': char_name,
                        'values': values.split(',')
                    }
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Ошибка при загрузке характеристик: {e}")

    def initialize_model(self):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Получаем количество классов
            cursor.execute("SELECT COUNT(*) FROM coffee_types")
            self.n_classes = cursor.fetchone()[0]
            
            # Вычисляем размерность входных данных
            n_numeric = len(self.numeric_features)
            n_categorical_values = sum(len(feat['values']) for feat in self.categorical_features.values())
            n_features = n_numeric + n_categorical_values
            
            # Создаем модель
            self.model = models.Sequential([
                layers.Dense(128, activation='relu', input_shape=(n_features,)),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                layers.Dense(64, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                layers.Dense(32, activation='relu'),
                layers.BatchNormalization(),
                layers.Dense(self.n_classes, activation='softmax')
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            cursor.close()
            conn.close()
            self.model_initialized = True
        except Exception as e:
            print(f"Ошибка при инициализации модели: {e}")

    def load_model(self):
        """Загружает модель из файла или создает новую"""
        try:
            model_path = os.path.join('models', 'coffee_classifier.h5')
            if os.path.exists(model_path):
                print("Загрузка существующей модели...")
                self.model = tf.keras.models.load_model(model_path)
            else:
                print("Модель не найдена, начинаем обучение...")
                self.train_model()
        except Exception as e:
            print(f"Ошибка при загрузке модели: {e}")
            print("Создаем новую модель...")
            self.train_model()

    def load_encoders(self):
        try:
            encoders_path = os.path.join('models', 'label_encoders.joblib')
            if os.path.exists(encoders_path):
                self.label_encoders = joblib.load(encoders_path)
        except Exception as e:
            print(f"Ошибка при загрузке энкодеров: {e}")

    def load_scaler(self):
        try:
            scaler_path = os.path.join('models', 'scaler.joblib')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            else:
                self.scaler = StandardScaler()
                self.fit_scaler()
        except Exception as e:
            print(f"Ошибка при загрузке scaler: {e}")
            self.scaler = StandardScaler()

    def load_characteristic_mapping(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Получаем числовые характеристики
            cursor.execute("""
                SELECT id, name 
                FROM characteristics 
                WHERE type = 'numeric'
                ORDER BY id
            """)
            numeric_chars = cursor.fetchall()
            
            # Получаем категориальные характеристики
            cursor.execute("""
                SELECT c.id, c.name, GROUP_CONCAT(DISTINCT cv.value) as possible_values
                FROM characteristics c
                LEFT JOIN categorical_values cv ON c.id = cv.characteristic_id
                WHERE c.type = 'categorical'
                GROUP BY c.id, c.name
                ORDER BY c.id
            """)
            categorical_chars = cursor.fetchall()
            
            # Создаем маппинг
            self.characteristic_mapping = {
                'numeric': {str(char['id']): char['name'] for char in numeric_chars},
                'categorical': {str(char['id']): {
                    'name': char['name'],
                    'values': char['possible_values'].split(',') if char['possible_values'] else []
                } for char in categorical_chars}
            }
            
            print("Загружен маппинг характеристик:")
            print("Числовые характеристики:", self.characteristic_mapping['numeric'])
            print("Категориальные характеристики:", self.characteristic_mapping['categorical'])
            
        except Exception as e:
            print(f"Ошибка при загрузке маппинга характеристик: {e}")
            self.characteristic_mapping = {'numeric': {}, 'categorical': {}}
        finally:
            cursor.close()
            conn.close()

    def fit_scaler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Получаем все числовые значения
            cursor.execute("""
                SELECT cnc.characteristic_id, cnc.min_value, cnc.max_value
                FROM coffee_numeric_characteristics cnc
                JOIN characteristics c ON c.id = cnc.characteristic_id
                WHERE c.type = 'numeric'
                ORDER BY cnc.characteristic_id
            """)
            numeric_values = cursor.fetchall()
            
            if numeric_values:
                # Преобразуем в numpy array, сохраняя порядок характеристик
                values = []
                for char_id in sorted(self.characteristic_mapping['numeric'].keys()):
                    char_values = [v for v in numeric_values if str(v['characteristic_id']) == str(char_id)]
                    if char_values:
                        values.append([char_values[0]['min_value'], char_values[0]['max_value']])
                    else:
                        values.append([0.0, 0.0])
                
                values = np.array(values)
                print("Размерность данных для обучения scaler:", values.shape)
                
                # Обучаем scaler на двумерных данных
                self.scaler = StandardScaler()
                # Преобразуем данные в нужный формат (n_samples, n_features)
                values_reshaped = values.reshape(-1, 1)
                self.scaler.fit(values_reshaped)
                
                # Сохраняем scaler
                os.makedirs('models', exist_ok=True)
                joblib.dump(self.scaler, os.path.join('models', 'scaler.joblib'))
                
        except Exception as e:
            print(f"Ошибка при обучении scaler: {e}")
        finally:
            cursor.close()
            conn.close()

    def prepare_input_data(self, input_data):
        try:
            if not isinstance(input_data, dict) or 'characteristics' not in input_data:
                raise ValueError("Неверный формат входных данных")
                
            characteristics = input_data['characteristics']
            if not isinstance(characteristics, dict):
                raise ValueError("Неверный формат характеристик")
                
            numeric_chars = characteristics.get('numeric', {})
            categorical_chars = characteristics.get('categorical', {})
            
            if not isinstance(numeric_chars, dict) or not isinstance(categorical_chars, dict):
                raise ValueError("Неверный формат числовых или категориальных характеристик")
            
            # Подготавливаем числовые характеристики
            numeric_features = []
            for char_id in sorted(self.characteristic_mapping['numeric'].keys()):
                try:
                    if str(char_id) in numeric_chars:
                        value = float(numeric_chars[str(char_id)])
                        numeric_features.append(value)
                    else:
                        numeric_features.append(0.0)
                except (ValueError, TypeError):
                    numeric_features.append(0.0)
            
            # Подготавливаем категориальные характеристики
            categorical_features = []
            for char_id in sorted(self.characteristic_mapping['categorical'].keys()):
                if str(char_id) in categorical_chars:
                    value = str(categorical_chars[str(char_id)])
                    char_values = self.characteristic_mapping['categorical'][char_id]['values']
                    # One-hot encoding для категориального значения
                    one_hot = [1 if v == value else 0 for v in char_values]
                    categorical_features.extend(one_hot)
                else:
                    # Если значение не указано, заполняем нулями
                    char_values = self.characteristic_mapping['categorical'][char_id]['values']
                    categorical_features.extend([0] * len(char_values))
            
            # Нормализуем числовые признаки
            if self.scaler is not None and numeric_features:
                try:
                    # Преобразуем числовые признаки в двумерный массив
                    numeric_array = np.array(numeric_features).reshape(-1, 1)
                    print("Размерность числовых признаков перед нормализацией:", numeric_array.shape)
                    normalized_numeric = self.scaler.transform(numeric_array)
                    numeric_features = normalized_numeric.flatten().tolist()
                except Exception as e:
                    print(f"Ошибка при нормализации числовых признаков: {e}")
            
            # Объединяем все признаки
            features = numeric_features + categorical_features
            
            return np.array([features])
        except Exception as e:
            print(f"Ошибка при подготовке входных данных: {e}")
            return None

    def check_for_updates(self):
        """Проверяет, нужно ли переобучить модель"""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Проверяем последнее обновление данных
            cursor.execute("""
                SELECT MAX(GREATEST(
                    (SELECT MAX(updated_at) FROM coffee_types),
                    (SELECT MAX(updated_at) FROM coffee_numeric_characteristics),
                    (SELECT MAX(updated_at) FROM coffee_categorical_characteristics)
                )) as last_update
            """)
            last_update = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Если есть обновления, переобучаем модель
            if not self.last_training_time or (last_update and last_update > self.last_training_time):
                print("Обнаружены изменения в данных. Переобучение модели...")
                self.train_model()
                return True
                
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            
        return False

    def train_model(self):
        try:
            print("Начало обучения модели...")
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Получаем все типы кофе
            cursor.execute("SELECT id, name FROM coffee_types ORDER BY id")
            coffee_types = cursor.fetchall()
            self.n_classes = len(coffee_types)
            
            X_data = []
            y_data = []
            
            # Генерируем обучающие данные
            for coffee_id, _ in coffee_types:
                # Получаем числовые характеристики
                cursor.execute("""
                    SELECT cnc.characteristic_id, cnc.min_value, cnc.max_value
                    FROM coffee_numeric_characteristics cnc
                    JOIN characteristics c ON c.id = cnc.characteristic_id
                    WHERE cnc.coffee_type_id = %s AND c.type = 'numeric'
                """, (coffee_id,))
                numeric_results = cursor.fetchall()
                
                # Генерируем несколько образцов для каждого типа кофе
                n_samples = 10
                for _ in range(n_samples):
                    numeric_chars = {}
                    for char_id, min_val, max_val in numeric_results:
                        # Генерируем случайное значение в диапазоне
                        value = np.random.uniform(min_val, max_val)
                        numeric_chars[str(char_id)] = value
                    
                    # Получаем категориальные характеристики
                    cursor.execute("""
                        SELECT ccc.characteristic_id, cv.value
                        FROM coffee_categorical_characteristics ccc
                        JOIN categorical_values cv ON ccc.categorical_value_id = cv.id
                        JOIN characteristics c ON c.id = ccc.characteristic_id
                        WHERE ccc.coffee_type_id = %s AND c.type = 'categorical'
                    """, (coffee_id,))
                    categorical_chars = {str(row[0]): row[1] for row in cursor.fetchall()}
                    
                    # Подготавливаем входные данные
                    input_data = {
                        'characteristics': {
                            'numeric': numeric_chars,
                            'categorical': categorical_chars
                        }
                    }
                    
                    print("Подготовка входных данных:", input_data)
                    X = self.prepare_input_data(input_data)
                    
                    if X is not None:
                        X_data.append(X[0])
                        y_data.append(coffee_id - 1)  # -1 для 0-based индексации
                    else:
                        print("Пропуск образца из-за ошибки подготовки данных")
            
            if not X_data:
                raise ValueError("Не удалось сгенерировать обучающие данные")
            
            # Преобразуем данные в numpy массивы
            X_data = np.array(X_data)
            y_data = np.array(y_data)
            
            print("Размерность обучающих данных:", X_data.shape)
            print("Размерность меток:", y_data.shape)
            
            # Преобразуем метки в one-hot encoding
            y_data = tf.keras.utils.to_categorical(y_data, num_classes=self.n_classes)
            
            # Создаем и компилируем модель
            n_features = X_data.shape[1]
            self.model = models.Sequential([
                layers.Dense(128, activation='relu', input_shape=(n_features,)),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                layers.Dense(64, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                layers.Dense(32, activation='relu'),
                layers.BatchNormalization(),
                layers.Dense(self.n_classes, activation='softmax')
            ])
            
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Обучаем модель
            history = self.model.fit(
                X_data, y_data,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                verbose=1
            )
            
            # Обновляем время последнего обучения
            self.last_training_time = datetime.now()
            
            # Сохраняем модель
            os.makedirs('models', exist_ok=True)
            self.model.save(os.path.join('models', 'coffee_classifier.h5'))
            
            cursor.close()
            conn.close()
            
            print("Обучение модели завершено")
            return history
            
        except Exception as e:
            print(f"Ошибка при обучении модели: {e}")
            return None

    def predict(self, input_data):
        try:
            # Проверяем обновления
            self.check_for_updates()
            
            # Подготавливаем входные данные
            X = self.prepare_input_data(input_data)
            
            if X is None:
                raise ValueError("Ошибка при подготовке входных данных")
            
            # Получаем предсказания
            predictions = self.model.predict(X, verbose=0)
            
            print("Сырые предсказания:", predictions)
            print("Сумма вероятностей:", np.sum(predictions))
            
            # Нормализуем предсказания
            predictions = predictions / np.sum(predictions, axis=1, keepdims=True)
            print("Нормализованные предсказания:", predictions)
            
            return predictions
            
        except Exception as e:
            print(f"Ошибка при предсказании: {e}")
            # Возвращаем равномерное распределение в случае ошибки
            return np.ones((1, self.n_classes)) / self.n_classes


# Создаем экземпляр классификатора
classifier = CoffeeClassifier() 