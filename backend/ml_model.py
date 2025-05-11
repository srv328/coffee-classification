import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import tensorflow as tf
from tensorflow.keras import layers, models
import mysql.connector
from config import db_config
import json
import os
from datetime import datetime

class CoffeeClassifier:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.n_classes = 0
        self.numeric_features = []
        self.categorical_features = {}
        self.model_initialized = False
        self.last_training_time = None
        self.load_characteristics()
        self.initialize_model()
        
        
        model_path = 'models/coffee_classifier'
        if os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.train_model()

    def load_characteristics(self):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            
            cursor.execute("""
                SELECT DISTINCT c.id, c.name 
                FROM characteristics c
                INNER JOIN coffee_numeric_characteristics cnc ON c.id = cnc.characteristic_id
                WHERE c.type = 'numeric'
                ORDER BY c.id
            """)
            self.numeric_features = [(row[0], row[1]) for row in cursor.fetchall()]
            
            
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
            
            
            cursor.execute("SELECT COUNT(*) FROM coffee_types")
            self.n_classes = cursor.fetchone()[0]
            
            
            n_numeric = len(self.numeric_features)
            n_categorical_values = sum(len(feat['values']) for feat in self.categorical_features.values())
            n_features = n_numeric + n_categorical_values
            
            
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

    def prepare_input_data(self, numeric_chars, categorical_chars):
        try:
            print(f"Числовые характеристики: {numeric_chars}")
            print(f"Категориальные характеристики: {categorical_chars}")
            
            
            numeric_values = []
            for char_id, char_name in self.numeric_features:
                
                char_id_str = str(char_id)
                value = float(numeric_chars.get(char_id_str, 0))
                numeric_values.append(value)
            
            
            categorical_values = []
            for char_id, char_info in self.categorical_features.items():
                
                char_id_str = str(char_id)
                value = categorical_chars.get(char_id_str, '')
                
                for possible_value in char_info['values']:
                    
                    if value and possible_value:
                        categorical_values.append(1.0 if value.strip().lower() == possible_value.strip().lower() else 0.0)
                    else:
                        categorical_values.append(0.0)
            
            
            X = np.array(numeric_values + categorical_values).reshape(1, -1)
            print(f"Подготовленные данные: {X}")
            return X
        except Exception as e:
            print(f"Ошибка при подготовке данных: {e}")
            return None

    def check_for_updates(self):
        """Проверяет, нужно ли переобучить модель"""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            
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
            
            
            cursor.execute("SELECT id, name FROM coffee_types ORDER BY id")
            coffee_types = cursor.fetchall()
            self.n_classes = len(coffee_types)
            
            X_data = []
            y_data = []
            
            
            for coffee_id, _ in coffee_types:
                
                cursor.execute("""
                    SELECT characteristic_id, min_value, max_value
                    FROM coffee_numeric_characteristics
                    WHERE coffee_type_id = %s
                """, (coffee_id,))
                numeric_results = cursor.fetchall()
                
                
                n_samples = 10  
                for _ in range(n_samples):
                    numeric_chars = {}
                    for char_id, min_val, max_val in numeric_results:
                        
                        value = np.random.uniform(min_val, max_val)
                        numeric_chars[str(char_id)] = value
                    
                    
                    cursor.execute("""
                        SELECT characteristic_id, value
                        FROM coffee_categorical_characteristics
                        WHERE coffee_type_id = %s
                    """, (coffee_id,))
                    categorical_chars = {str(row[0]): row[1] for row in cursor.fetchall()}
                    
                    
                    X = self.prepare_input_data(numeric_chars, categorical_chars)
                    if X is not None:
                        X_data.append(X[0])  
                        y_data.append(coffee_id - 1)  
            
            
            X_data = np.array(X_data)
            y_data = np.array(y_data)
            
            
            self.scaler.fit(X_data)
            X_data = self.scaler.transform(X_data)
            
            
            y_data = tf.keras.utils.to_categorical(y_data, num_classes=self.n_classes)
            
            
            n_features = X_data.shape[1]
            self.model = models.Sequential([
                layers.Dense(64, activation='relu', input_shape=(n_features,)),
                layers.Dropout(0.2),
                layers.Dense(32, activation='relu'),
                layers.Dropout(0.2),
                layers.Dense(self.n_classes, activation='softmax')
            ])
            
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            
            history = self.model.fit(
                X_data, y_data,
                epochs=100,
                batch_size=32,
                validation_split=0.2,
                verbose=1
            )
            
            
            self.last_training_time = datetime.now()
            
            
            if not os.path.exists('models'):
                os.makedirs('models')
            self.save_model('models/coffee_classifier')
            
            cursor.close()
            conn.close()
            
            print("Обучение модели завершено")
            return history
            
        except Exception as e:
            print(f"Ошибка при обучении модели: {e}")
            return None

    def save_model(self, path):
        try:
            if not self.model_initialized:
                raise Exception("Модель не инициализирована")
            
            
            os.makedirs(path, exist_ok=True)
            
            
            self.model.save(f"{path}/model")
            
            
            metadata = {
                'numeric_features': self.numeric_features,
                'categorical_features': self.categorical_features
            }
            
            with open(f"{path}/metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении модели: {e}")

    def load_model(self, path):
        try:
            
            self.model = tf.keras.models.load_model(f"{path}/model")
            
            
            with open(f"{path}/metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.numeric_features = metadata['numeric_features']
                self.categorical_features = metadata['categorical_features']
            
            self.model_initialized = True
        except Exception as e:
            print(f"Ошибка при загрузке модели: {e}")

    def predict(self, input_data):
        try:
            
            self.check_for_updates()
            
            
            X = self.prepare_input_data(
                input_data['characteristics']['numeric'],
                input_data['characteristics']['categorical']
            )
            
            if X is None:
                raise ValueError("Ошибка при подготовке входных данных")
            
            
            X = self.scaler.transform(X)
            
            
            predictions = self.model.predict(X)
            
            
            print("Сырые предсказания:", predictions)
            print("Сумма вероятностей:", np.sum(predictions))
            
            return predictions
            
        except Exception as e:
            print(f"Ошибка при предсказании: {e}")
            
            return np.ones((1, self.n_classes)) / self.n_classes


classifier = CoffeeClassifier() 