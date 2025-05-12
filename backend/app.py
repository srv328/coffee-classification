from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import tensorflow as tf
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import json
import os
from dotenv import load_dotenv
from ml_model import CoffeeClassifier
from decimal import Decimal
from config import db_config
from datetime import datetime
from db import get_db_connection
from routes.characteristics import characteristics
from routes.coffee_type_characteristics import coffee_type_characteristics
import joblib
from sklearn.preprocessing import StandardScaler

load_dotenv()

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Регистрируем blueprints
app.register_blueprint(characteristics)
app.register_blueprint(coffee_type_characteristics, url_prefix='/api/expert')

classifier = CoffeeClassifier()

CHARACTERISTIC_TRANSLATIONS = {
    'acidity': 'Кислотность',
    'bitterness': 'Горечь',
    'sweetness': 'Сладость',
    'density': 'Плотность',
    'astringency': 'Терпкость',
    'roasting_degree': 'Степень обжарки',
    'grinding_degree': 'Степень помола',
    'variety': 'Разновидность',
    'processing_method': 'Метод обработки',
    'region': 'Регион произрастания',
    'roast_level': 'Степень обжарки',
    'body': 'Тело',
    'aroma': 'Аромат',
    'aftertaste': 'Послевкусие',
    'flavor': 'Вкус'
}

def statistical_analysis(input_data):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    
    cursor.execute("SELECT * FROM coffee_types")
    coffee_types = cursor.fetchall()
    
    results = []
    for coffee in coffee_types:
        match_score = 0
        total_characteristics = 0
        
        
        cursor.execute("""
            SELECT c.name, cn.min_value, cn.max_value 
            FROM coffee_numeric_characteristics cn
            JOIN characteristics c ON cn.characteristic_id = c.id
            WHERE cn.coffee_type_id = %s
        """, (coffee['id'],))
        numeric_ranges = cursor.fetchall()
        
        for range_data in numeric_ranges:
            char_name = range_data['name']
            if char_name in input_data:
                value = float(input_data[char_name])
                if range_data['min_value'] <= value <= range_data['max_value']:
                    match_score += 1
                total_characteristics += 1
        
        
        cursor.execute("""
            SELECT c.name, cc.value
            FROM coffee_categorical_characteristics cc
            JOIN characteristics c ON cc.characteristic_id = c.id
            WHERE cc.coffee_type_id = %s
        """, (coffee['id'],))
        categorical_values = cursor.fetchall()
        
        for cat_data in categorical_values:
            char_name = cat_data['name']
            if char_name in input_data:
                if input_data[char_name] == cat_data['value']:
                    match_score += 1
                total_characteristics += 1
        
        if total_characteristics > 0:
            confidence = (match_score / total_characteristics) * 100
            results.append({
                'coffee_type': coffee['name'],
                'confidence': confidence
            })
    
    cursor.close()
    conn.close()
    return sorted(results, key=lambda x: x['confidence'], reverse=True)


@app.route('/api/expert/coffee-types', methods=['GET'])
def get_coffee_types():
    print("Получен запрос на список сортов кофе")
    try:
        print("Подключение к базе данных...")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("Выполнение запроса...")
        cursor.execute("SELECT id, name FROM coffee_types ORDER BY name")
        result = cursor.fetchall()
        print(f"Получено {len(result)} сортов кофе")
        
        cursor.close()
        conn.close()
        print("Соединение с базой данных закрыто")
        
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении списка сортов кофе: {str(e)}")
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500

@app.route('/api/characteristics', methods=['GET'])
def get_characteristics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM characteristics")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/classify', methods=['POST'])
def classify_coffee():
    data = request.json
    method = data.get('method', 'statistical')
    input_data = data.get('input_data', {})
    
    if method == 'statistical':
        results = statistical_analysis(input_data)
    else:
        results = classifier.predict(input_data)
    
    return jsonify(results)

@app.route('/api/expert/add-coffee-type', methods=['POST'])
def add_coffee_type():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({
            'success': False,
            'error': 'Название сорта кофе не может быть пустым'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO coffee_types (name) VALUES (%s)",
            (name,)
        )
        conn.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except mysql.connector.Error as err:
        if err.errno == 1062:  
            return jsonify({
                'success': False,
                'error': f'Сорт кофе "{name}" уже существует'
            }), 409
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при добавлении сорта кофе'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/add-numeric-range', methods=['POST'])
def add_numeric_range():
    data = request.json
    coffee_type_id = data.get('coffee_type_id')
    characteristic_id = data.get('characteristic_id')
    min_value = data.get('min_value')
    max_value = data.get('max_value')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO numeric_ranges 
            (coffee_type_id, characteristic_id, min_value, max_value)
            VALUES (%s, %s, %s, %s)
        """, (coffee_type_id, characteristic_id, min_value, max_value))
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': str(err)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/add-categorical-value', methods=['POST'])
def add_categorical_value():
    data = request.json
    coffee_type_id = data.get('coffee_type_id')
    characteristic_id = data.get('characteristic_id')
    value_id = data.get('value_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO coffee_categorical_values 
            (coffee_type_id, characteristic_id, value_id)
            VALUES (%s, %s, %s)
        """, (coffee_type_id, characteristic_id, value_id))
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': str(err)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/delete-coffee-type/<int:coffee_id>', methods=['DELETE'])
def delete_coffee_type(coffee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        
        cursor.execute("SELECT name FROM coffee_types WHERE id = %s", (coffee_id,))
        coffee = cursor.fetchone()
        if not coffee:
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404

        
        cursor.execute("DELETE FROM coffee_numeric_characteristics WHERE coffee_type_id = %s", (coffee_id,))
        cursor.execute("DELETE FROM coffee_categorical_characteristics WHERE coffee_type_id = %s", (coffee_id,))
        
        
        cursor.execute("DELETE FROM coffee_types WHERE id = %s", (coffee_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Сорт кофе успешно удален'
        })
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Ошибка SQL при удалении сорта кофе: {err}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при удалении сорта кофе: {str(err)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_id>/characteristics', methods=['GET'])
def get_coffee_characteristics(coffee_id):
    print(f"Получен запрос на характеристики для сорта кофе {coffee_id}")
    conn = None
    cursor = None
    try:
        print("Подключение к базе данных...")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Проверяем существование сорта кофе
        print("Проверка существования сорта кофе...")
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_id,))
        if not cursor.fetchone():
            print(f"Сорт кофе {coffee_id} не найден")
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404
        
        # Получаем числовые характеристики
        print("Получение числовых характеристик...")
        cursor.execute("""
            SELECT c.id, c.name, c.type, cn.min_value, cn.max_value
            FROM coffee_numeric_characteristics cn
            JOIN characteristics c ON c.id = cn.characteristic_id
            WHERE cn.coffee_type_id = %s
        """, (coffee_id,))
        numeric_characteristics = cursor.fetchall()
        print(f"Найдено {len(numeric_characteristics)} числовых характеристик")
        
        # Получаем категориальные характеристики
        print("Получение категориальных характеристик...")
        cursor.execute("""
            SELECT c.id, c.name, c.type, cv.value
            FROM coffee_categorical_characteristics cc
            JOIN characteristics c ON c.id = cc.characteristic_id
            JOIN categorical_values cv ON cv.id = cc.categorical_value_id
            WHERE cc.coffee_type_id = %s
        """, (coffee_id,))
        categorical_characteristics = cursor.fetchall()
        print(f"Найдено {len(categorical_characteristics)} категориальных характеристик")
        
        # Группируем категориальные характеристики
        grouped_categorical = {}
        for char in categorical_characteristics:
            if char['id'] not in grouped_categorical:
                grouped_categorical[char['id']] = {
                    'id': char['id'],
                    'name': char['name'],
                    'type': char['type'],
                    'values': []
                }
            if char['value']:
                grouped_categorical[char['id']]['values'].append(char['value'])
        
        result = {
            'numeric': numeric_characteristics,
            'categorical': list(grouped_categorical.values())
        }
        
        print("Успешно сформирован ответ")
        return jsonify(result)
        
    except Exception as e:
        print(f"Ошибка при получении характеристик: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при получении характеристик: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")

@app.route('/api/expert/coffee-type/<int:coffee_id>/characteristics', methods=['POST'])
def update_coffee_characteristics(coffee_id):
    print(f"Получен запрос на обновление характеристик для сорта кофе {coffee_id}")
    conn = None
    cursor = None
    try:
        data = request.json
        print("Получены данные:", data)
        
        print("Подключение к базе данных...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование сорта кофе
        print("Проверка существования сорта кофе...")
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_id,))
        if not cursor.fetchone():
            print(f"Сорт кофе {coffee_id} не найден")
            return jsonify({
                'success': False, 
                'error': 'Сорт кофе не найден'
            }), 404
        
        # Удаляем старые характеристики
        print("Удаление старых характеристик...")
        cursor.execute("DELETE FROM coffee_numeric_characteristics WHERE coffee_type_id = %s", (coffee_id,))
        cursor.execute("DELETE FROM coffee_categorical_characteristics WHERE coffee_type_id = %s", (coffee_id,))
        
        # Добавляем новые числовые характеристики
        print("Добавление числовых характеристик...")
        for char in data.get('numeric', []):
            cursor.execute("""
                INSERT INTO coffee_numeric_characteristics 
                (coffee_type_id, characteristic_id, min_value, max_value)
                VALUES (%s, %s, %s, %s)
            """, (coffee_id, char['id'], char.get('min_value', 0), char.get('max_value', 0)))
        
        # Добавляем новые категориальные характеристики
        print("Добавление категориальных характеристик...")
        for char in data.get('categorical', []):
            for value in char.get('values', []):
                # Получаем ID значения категориальной характеристики
                cursor.execute("""
                    SELECT id FROM categorical_values 
                    WHERE characteristic_id = %s AND value = %s
                """, (char['id'], value))
                result = cursor.fetchone()
                
                if result:
                    value_id = result[0]
                    cursor.execute("""
                        INSERT INTO coffee_categorical_characteristics 
                        (coffee_type_id, characteristic_id, categorical_value_id)
                        VALUES (%s, %s, %s)
                    """, (coffee_id, char['id'], value_id))
                else:
                    # Если значение не найдено, создаем его
                    cursor.execute("""
                        INSERT INTO categorical_values (characteristic_id, value)
                        VALUES (%s, %s)
                    """, (char['id'], value))
                    value_id = cursor.lastrowid
                    
                    cursor.execute("""
                        INSERT INTO coffee_categorical_characteristics 
                        (coffee_type_id, characteristic_id, categorical_value_id)
                        VALUES (%s, %s, %s)
                    """, (coffee_id, char['id'], value_id))
        
        conn.commit()
        print("Изменения успешно сохранены")
        return jsonify({'success': True})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Ошибка при обновлении характеристик: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при обновлении характеристик: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")

@app.route('/api/expert/characteristics', methods=['POST'])
def add_characteristic():
    data = request.json
    name = data.get('name')
    type = data.get('type')  
    
    if not name or not type or type not in ['numeric', 'categorical']:
        return jsonify({
            'success': False,
            'error': 'Необходимо указать название и корректный тип характеристики'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        
        cursor.execute("SELECT id FROM characteristics WHERE name = %s", (name,))
        existing_char = cursor.fetchone()
        
        if existing_char:
            
            return jsonify({
                'success': True,
                'id': existing_char[0],
                'message': 'Характеристика уже существует'
            })
            
        
        cursor.execute(
            "INSERT INTO characteristics (name, type) VALUES (%s, %s)",
            (name, type)
        )
        char_id = cursor.lastrowid
        
        
        if type == 'categorical' and 'values' in data:
            for value in data.get('values', []):
                if value:  
                    cursor.execute(
                        "INSERT INTO categorical_values (characteristic_id, value) VALUES (%s, %s)",
                        (char_id, value)
                    )
        
        conn.commit()
        return jsonify({
            'success': True,
            'id': char_id,
            'message': 'Характеристика успешно добавлена'
        })
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Ошибка SQL при добавлении характеристики: {err}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при добавлении характеристики: {str(err)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/characteristic/<int:char_id>/values', methods=['GET'])
def get_characteristic_values(char_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        
        cursor.execute("SELECT id, name, type FROM characteristics WHERE id = %s", (char_id,))
        characteristic = cursor.fetchone()
        
        if not characteristic:
            return jsonify({
                'success': False,
                'error': 'Характеристика не найдена'
            }), 404
            
        
        if characteristic['type'] == 'categorical':
            cursor.execute("""
                SELECT id, value
                FROM categorical_values
                WHERE characteristic_id = %s
                ORDER BY value
            """, (char_id,))
            values = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'characteristic': characteristic,
                'values': values
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Это не категориальная характеристика'
            }), 400
            
    except mysql.connector.Error as err:
        print(f"Ошибка SQL: {err}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при получении значений: {str(err)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_id>/add-characteristic', methods=['POST'])
def add_characteristic_to_coffee(coffee_id):
    data = request.json
    characteristic_id = data.get('characteristic_id')
    characteristic_type = data.get('type')
    
    if not characteristic_id or not characteristic_type:
        return jsonify({
            'success': False,
            'error': 'Не указаны ID характеристики или её тип'
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404
        
        
        cursor.execute("SELECT type FROM characteristics WHERE id = %s", (characteristic_id,))
        char_data = cursor.fetchone()
        if not char_data:
            return jsonify({
                'success': False,
                'error': 'Характеристика не найдена'
            }), 404
        
        
        if characteristic_type == 'numeric':
            cursor.execute("""
                SELECT id FROM coffee_numeric_characteristics 
                WHERE coffee_type_id = %s AND characteristic_id = %s
            """, (coffee_id, characteristic_id))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Эта числовая характеристика уже добавлена к данному сорту кофе'
                }), 409
        else:
            cursor.execute("""
                SELECT id FROM coffee_categorical_characteristics 
                WHERE coffee_type_id = %s AND characteristic_id = %s
            """, (coffee_id, characteristic_id))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Эта категориальная характеристика уже добавлена к данному сорту кофе'
                }), 409
        
        if characteristic_type == 'numeric':
            min_value = data.get('min_value')
            max_value = data.get('max_value')
            
            if min_value is None or max_value is None:
                return jsonify({
                    'success': False,
                    'error': 'Для числовой характеристики необходимо указать минимальное и максимальное значения'
                }), 400
            
            cursor.execute("""
                INSERT INTO coffee_numeric_characteristics 
                (coffee_type_id, characteristic_id, min_value, max_value)
                VALUES (%s, %s, %s, %s)
            """, (coffee_id, characteristic_id, min_value, max_value))
        
        elif characteristic_type == 'categorical':
            values = data.get('values', [])
            
            if not values:
                return jsonify({
                    'success': False,
                    'error': 'Для категориальной характеристики необходимо указать хотя бы одно значение'
                }), 400
            
            for value in values:
                cursor.execute("""
                    INSERT INTO coffee_categorical_characteristics 
                    (coffee_type_id, characteristic_id, value)
                    VALUES (%s, %s, %s)
                """, (coffee_id, characteristic_id, value))
        
        else:
            return jsonify({
                'success': False,
                'error': 'Неверный тип характеристики'
            }), 400
        
        conn.commit()
        return jsonify({'success': True})
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(err)
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_id>/characteristic/<int:characteristic_id>', methods=['DELETE'])
def delete_coffee_characteristic(coffee_id, characteristic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404
        
        
        cursor.execute("SELECT type FROM characteristics WHERE id = %s", (characteristic_id,))
        char_data = cursor.fetchone()
        if not char_data:
            return jsonify({
                'success': False,
                'error': 'Характеристика не найдена'
            }), 404
        
        
        cursor.execute("""
            DELETE FROM coffee_numeric_characteristics 
            WHERE coffee_type_id = %s AND characteristic_id = %s
        """, (coffee_id, characteristic_id))
        numeric_deleted = cursor.rowcount
        
        
        cursor.execute("""
            DELETE FROM coffee_categorical_characteristics 
            WHERE coffee_type_id = %s AND characteristic_id = %s
        """, (coffee_id, characteristic_id))
        categorical_deleted = cursor.rowcount
        
        
        if numeric_deleted == 0 and categorical_deleted == 0:
            return jsonify({
                'success': False,
                'error': 'Характеристика не найдена у данного сорта кофе'
            }), 404
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Характеристика успешно удалена'
        })
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(err)
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/characteristics/values', methods=['GET'])
def get_all_characteristic_values():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Получаем числовые характеристики с их глобальными ограничениями
        cursor.execute("""
            SELECT DISTINCT c.id, c.name, c.type, 
                   ncl.min_value as min_value, 
                   ncl.max_value as max_value
            FROM characteristics c
            LEFT JOIN numeric_characteristic_limits ncl ON c.id = ncl.characteristic_id
            WHERE c.type = 'numeric'
            ORDER BY c.name
        """)
        numeric_characteristics = cursor.fetchall()
        
        # Получаем категориальные характеристики с их возможными значениями
        cursor.execute("""
            SELECT DISTINCT c.id, c.name, c.type, 
                   GROUP_CONCAT(DISTINCT cv.value ORDER BY cv.value) AS possible_values
            FROM characteristics c
            LEFT JOIN categorical_values cv ON c.id = cv.characteristic_id
            WHERE c.type = 'categorical'
            GROUP BY c.id, c.name, c.type
            ORDER BY c.name
        """)
        categorical_characteristics = cursor.fetchall()
        
        # Обрабатываем возможные значения для категориальных характеристик
        for char in categorical_characteristics:
            if char['possible_values']:
                char['possible_values'] = char['possible_values'].split(',')
            else:
                char['possible_values'] = []
        
        result = {
            'numeric': numeric_characteristics,
            'categorical': categorical_characteristics
        }
        
        return jsonify(result)
    except mysql.connector.Error as err:
        print(f"Ошибка SQL при получении значений характеристик: {err}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при получении значений характеристик: {str(err)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/specialist/analyze-static', methods=['POST'])
def analyze_static():
    data = request.json
    numeric_chars = data['characteristics']['numeric']
    categorical_chars = data['characteristics']['categorical']
    
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT id, name FROM coffee_types")
        coffee_types_data = cursor.fetchall()
        coffee_types = {row[0]: row[1] for row in coffee_types_data}
        
        results = {
            'type': None,
            'explanations': [],
            'all_types_analysis': {}
        }
        
        for coffee_id, coffee_name in coffee_types.items():
            type_analysis = {
                'name': coffee_name,
                'matches': True,
                'reasons': []
            }
            
            # Проверяем числовые характеристики
            for char_id, value in numeric_chars.items():
                cursor.execute("""
                    SELECT c.name, cn.min_value, cn.max_value 
                    FROM coffee_numeric_characteristics cn
                    JOIN characteristics c ON c.id = cn.characteristic_id
                    WHERE cn.coffee_type_id = %s AND cn.characteristic_id = %s
                """, (coffee_id, char_id))
                range_data = cursor.fetchall()
                
                cursor.execute("SELECT name FROM characteristics WHERE id = %s", (char_id,))
                char_name_result = cursor.fetchone()
                char_name = char_name_result[0] if char_name_result else f"Характеристика {char_id}"
                char_name_ru = CHARACTERISTIC_TRANSLATIONS.get(char_name, char_name)
                
                if not range_data:
                    type_analysis['matches'] = False
                    type_analysis['reasons'].append(
                        f"Характеристика '{char_name_ru}' не определена для данного сорта"
                    )
                else:
                    char_name, min_val, max_val = range_data[0]
                    char_name_ru = CHARACTERISTIC_TRANSLATIONS.get(char_name, char_name)
                    
                    if value < min_val or value > max_val:
                        type_analysis['matches'] = False
                        type_analysis['reasons'].append(
                            f"Значение '{value}' для характеристики '{char_name_ru}' "
                            f"не входит в допустимый диапазон [{min_val:.2f}, {max_val:.2f}]"
                        )
                    else:
                        type_analysis['reasons'].append(
                            f"Значение '{value}' для характеристики '{char_name_ru}' "
                            f"входит в допустимый диапазон [{min_val:.2f}, {max_val:.2f}]"
                        )
            
            # Проверяем категориальные характеристики
            for char_id, value in categorical_chars.items():
                cursor.execute("""
                    SELECT c.name, cv.value 
                    FROM coffee_categorical_characteristics cc
                    JOIN characteristics c ON c.id = cc.characteristic_id
                    JOIN categorical_values cv ON cc.categorical_value_id = cv.id
                    WHERE cc.coffee_type_id = %s AND cc.characteristic_id = %s
                """, (coffee_id, char_id))
                cat_data = cursor.fetchall()
                
                cursor.execute("SELECT name FROM characteristics WHERE id = %s", (char_id,))
                char_name_result = cursor.fetchone()
                char_name = char_name_result[0] if char_name_result else f"Характеристика {char_id}"
                char_name_ru = CHARACTERISTIC_TRANSLATIONS.get(char_name, char_name)
                
                if not cat_data:
                    type_analysis['matches'] = False
                    type_analysis['reasons'].append(
                        f"Характеристика '{char_name_ru}' не определена для данного сорта"
                    )
                else:
                    char_name, expected_value = cat_data[0]
                    char_name_ru = CHARACTERISTIC_TRANSLATIONS.get(char_name, char_name)
                    
                    if value != expected_value:
                        type_analysis['matches'] = False
                        type_analysis['reasons'].append(
                            f"Значение '{value}' для характеристики '{char_name_ru}' "
                            f"не соответствует требуемому значению '{expected_value}'"
                        )
                    else:
                        type_analysis['reasons'].append(
                            f"Значение '{value}' для характеристики '{char_name_ru}' "
                            f"соответствует требуемому значению '{expected_value}'"
                        )
            
            results['all_types_analysis'][coffee_name] = type_analysis
            
            if type_analysis['matches'] and not results['type']:
                results['type'] = coffee_name
                results['explanations'].append(f"Наиболее подходящий тип: {coffee_name}")
        
        if not results['type']:
            results['explanations'].append("Не найдено подходящих типов кофе.")
            
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in analyze_static: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/specialist/analyze-ml', methods=['POST'])
def analyze_ml():
    try:
        data = request.json
        print('Полученные данные:', data)
        
        if not data or 'characteristics' not in data:
            return jsonify({'error': 'Отсутствуют характеристики в входных данных'}), 400
            
        characteristics = data['characteristics']
        if 'numeric' not in characteristics or 'categorical' not in characteristics:
            return jsonify({'error': 'Отсутствуют числовые или категориальные характеристики'}), 400
            
        numeric_chars = characteristics['numeric']
        categorical_chars = characteristics['categorical']
        
        
        predictions = classifier.predict(data)
        print('Сырые предсказания:', predictions)
        
        
        predictions = predictions / np.sum(predictions)
        print('Нормализованные предсказания:', predictions)
        
        
        total_prob = np.sum(predictions[0])
        if abs(total_prob - 1.0) > 1e-6:
            print(f"Предупреждение: сумма вероятностей не равна 1: {total_prob}")
            predictions = predictions / total_prob
        
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM coffee_types")
        coffee_types_data = cursor.fetchall()
        coffee_types = {row[0]: row[1] for row in coffee_types_data}
        cursor.close()
        connection.close()
        
        
        results = {
            'type': None,
            'explanations': [],
            'probabilities': {}
        }
        
        
        for type_id, prob in enumerate(predictions[0]):
            if type_id + 1 in coffee_types:
                
                results['probabilities'][coffee_types[type_id + 1]] = round(float(prob) * 100, 2)
        
        
        max_prob_idx = predictions[0].argmax()
        if max_prob_idx + 1 in coffee_types:
            predicted_type = coffee_types[max_prob_idx + 1]
            results['type'] = predicted_type
            results['explanations'].append(
                f"Модель ИИ предсказала тип '{predicted_type}' на основе введённых данных."
            )
            results['explanations'].append(
                "Вероятности для каждого типа приведены ниже."
            )
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in analyze_ml: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/specialist/knowledge-base', methods=['GET'])
def get_knowledge_base():
    """Получение всей базы знаний для специалиста"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Получаем все сорта кофе
        cursor.execute("SELECT id, name FROM coffee_types ORDER BY name")
        coffee_types = cursor.fetchall()
        
        result = []
        
        for coffee in coffee_types:
            # Получаем числовые характеристики
            cursor.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.type,
                    cn.min_value,
                    cn.max_value
                FROM coffee_numeric_characteristics cn
                JOIN characteristics c ON c.id = cn.characteristic_id
                WHERE cn.coffee_type_id = %s
            """, (coffee['id'],))
            numeric_characteristics = cursor.fetchall()
            
            # Получаем категориальные характеристики
            cursor.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.type,
                    GROUP_CONCAT(cv.value) as value_list
                FROM coffee_categorical_characteristics cc
                JOIN characteristics c ON c.id = cc.characteristic_id
                JOIN categorical_values cv ON cc.categorical_value_id = cv.id
                WHERE cc.coffee_type_id = %s
                GROUP BY c.id, c.name, c.type
            """, (coffee['id'],))
            categorical_characteristics = cursor.fetchall()
            
            # Обрабатываем категориальные значения
            for char in categorical_characteristics:
                if char['value_list']:
                    char['values'] = char['value_list'].split(',')
                else:
                    char['values'] = []
                del char['value_list']  # Удаляем временное поле
            
            result.append({
                'id': coffee['id'],
                'name': coffee['name'],
                'characteristics': {
                    'numeric': numeric_characteristics,
                    'categorical': categorical_characteristics
                }
            })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Ошибка при получении базы знаний: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_type_id>/values', methods=['GET'])
def get_coffee_type_values(coffee_type_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Проверяем существование сорта кофе
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_type_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Сорт кофе не найден"}), 404
        
        # Получаем числовые характеристики и их значения
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.type,
                ncl.min_value as global_min,
                ncl.max_value as global_max,
                cn.min_value as coffee_min,
                cn.max_value as coffee_max
            FROM characteristics c
            JOIN numeric_characteristic_limits ncl ON c.id = ncl.characteristic_id
            JOIN coffee_numeric_characteristics cn ON c.id = cn.characteristic_id
            WHERE cn.coffee_type_id = %s
        """, (coffee_type_id,))
        numeric_values = cursor.fetchall()
        
        # Получаем категориальные характеристики и их значения
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.type,
                (
                    SELECT GROUP_CONCAT(cv.value)
                    FROM coffee_categorical_characteristics cc
                    JOIN categorical_values cv ON cc.categorical_value_id = cv.id
                    WHERE cc.coffee_type_id = %s AND cc.characteristic_id = c.id
                ) as selected_values,
                (
                    SELECT GROUP_CONCAT(DISTINCT cv2.value)
                    FROM categorical_values cv2
                    WHERE cv2.characteristic_id = c.id
                ) as available_values
            FROM characteristics c
            WHERE c.type = 'categorical'
            AND EXISTS (
                SELECT 1 
                FROM coffee_categorical_characteristics cc 
                WHERE cc.coffee_type_id = %s AND cc.characteristic_id = c.id
            )
        """, (coffee_type_id, coffee_type_id))
        categorical_values = cursor.fetchall()
        
        # Обрабатываем результаты
        for char in categorical_values:
            if char['selected_values']:
                char['selected_values'] = char['selected_values'].split(',')
            else:
                char['selected_values'] = []
                
            if char['available_values']:
                char['available_values'] = char['available_values'].split(',')
            else:
                char['available_values'] = []
        
        return jsonify({
            "numeric": numeric_values,
            "categorical": categorical_values
        })
        
    except Exception as e:
        print(f"Ошибка при получении значений характеристик: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_type_id>/values', methods=['POST'])
def update_coffee_type_values(coffee_type_id):
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование сорта кофе
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_type_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Сорт кофе не найден"}), 404
        
        # Обновляем числовые значения
        if 'numeric' in data:
            for char in data['numeric']:
                # Проверяем ограничения
                cursor.execute("""
                    SELECT min_value, max_value 
                    FROM numeric_characteristic_limits 
                    WHERE characteristic_id = %s
                """, (char['id'],))
                limits = cursor.fetchone()
                
                if limits:
                    # Преобразуем значения в Decimal для корректного сравнения
                    min_value = max(Decimal(str(limits[0])), Decimal(str(char.get('min_value', 0))))
                    max_value = min(Decimal(str(limits[1])), Decimal(str(char.get('max_value', 0))))
                else:
                    min_value = Decimal(str(char.get('min_value', 0)))
                    max_value = Decimal(str(char.get('max_value', 0)))
                
                # Обновляем значения
                cursor.execute("""
                    UPDATE coffee_numeric_characteristics 
                    SET min_value = %s, max_value = %s
                    WHERE coffee_type_id = %s AND characteristic_id = %s
                """, (min_value, max_value, coffee_type_id, char['id']))
        
        # Обновляем категориальные значения
        if 'categorical' in data:
            for char in data['categorical']:
                # Удаляем старые значения
                cursor.execute("""
                    DELETE FROM coffee_categorical_characteristics 
                    WHERE coffee_type_id = %s AND characteristic_id = %s
                """, (coffee_type_id, char['id']))
                
                # Добавляем новые значения
                for value in char.get('selected_values', []):
                    # Получаем ID значения категориальной характеристики
                    cursor.execute("""
                        SELECT id FROM categorical_values 
                        WHERE characteristic_id = %s AND value = %s
                    """, (char['id'], value))
                    result = cursor.fetchone()
                    
                    if result:
                        value_id = result[0]
                        # Добавляем новое значение
                        cursor.execute("""
                            INSERT INTO coffee_categorical_characteristics 
                            (coffee_type_id, characteristic_id, categorical_value_id)
                            VALUES (%s, %s, %s)
                        """, (coffee_type_id, char['id'], value_id))
        
        conn.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Ошибка при обновлении значений характеристик: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/expert/completeness-check', methods=['GET'])
def check_completeness():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Получаем все сорта кофе
        cursor.execute("SELECT id, name FROM coffee_types")
        coffee_types = cursor.fetchall()
        
        result = {
            'no_characteristics': [],  # Сорта без выбранных характеристик
            'incomplete_values': []    # Сорта с неполными значениями
        }
        
        for coffee in coffee_types:
            # Проверяем наличие характеристик
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM coffee_numeric_characteristics 
                WHERE coffee_type_id = %s
            """, (coffee['id'],))
            numeric_count = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM coffee_categorical_characteristics 
                WHERE coffee_type_id = %s
            """, (coffee['id'],))
            categorical_count = cursor.fetchone()['count']
            
            if numeric_count == 0 and categorical_count == 0:
                result['no_characteristics'].append({
                    'id': coffee['id'],
                    'name': coffee['name']
                })
                continue
            
            # Проверяем числовые значения
            cursor.execute("""
                SELECT 
                    c.name,
                    cn.min_value,
                    cn.max_value,
                    ncl.min_value as global_min,
                    ncl.max_value as global_max
                FROM coffee_numeric_characteristics cn
                JOIN characteristics c ON c.id = cn.characteristic_id
                JOIN numeric_characteristic_limits ncl ON c.id = ncl.characteristic_id
                WHERE cn.coffee_type_id = %s
                AND (
                    cn.min_value IS NULL 
                    OR cn.max_value IS NULL
                    OR cn.min_value < ncl.min_value
                    OR cn.max_value > ncl.max_value
                    OR cn.min_value = 0 AND cn.max_value = 0
                )
            """, (coffee['id'],))
            invalid_numeric = cursor.fetchall()
            
            # Проверяем категориальные значения
            cursor.execute("""
                SELECT c.name
                FROM coffee_categorical_characteristics cc
                JOIN characteristics c ON c.id = cc.characteristic_id
                WHERE cc.coffee_type_id = %s
                AND NOT EXISTS (
                    SELECT 1 FROM coffee_categorical_characteristics cc2
                    WHERE cc2.coffee_type_id = cc.coffee_type_id
                    AND cc2.characteristic_id = cc.characteristic_id
                    AND cc2.categorical_value_id IS NOT NULL
                )
            """, (coffee['id'],))
            empty_categorical = cursor.fetchall()
            
            if invalid_numeric or empty_categorical:
                result['incomplete_values'].append({
                    'id': coffee['id'],
                    'name': coffee['name'],
                    'empty_numeric': [
                        f"{char['name']} (текущие значения: {char['min_value']} - {char['max_value']}, "
                        f"допустимый диапазон: {char['global_min']} - {char['global_max']})"
                        for char in invalid_numeric
                    ],
                    'empty_categorical': [char['name'] for char in empty_categorical]
                })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Ошибка при проверке полноты данных: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True) 