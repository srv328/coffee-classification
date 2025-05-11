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

def get_db_connection():
    return mysql.connector.connect(**db_config)


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


@app.route('/api/coffee-types', methods=['GET'])
def get_coffee_types():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM coffee_types")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        
        cursor.execute("""
            SELECT c.id, c.name, c.type, cn.min_value, cn.max_value
            FROM coffee_numeric_characteristics cn
            JOIN characteristics c ON c.id = cn.characteristic_id
            WHERE cn.coffee_type_id = %s
        """, (coffee_id,))
        numeric_characteristics = cursor.fetchall()
        
        
        cursor.execute("""
            SELECT c.id, c.name, c.type, cc.value
            FROM coffee_categorical_characteristics cc
            JOIN characteristics c ON c.id = cc.characteristic_id
            WHERE cc.coffee_type_id = %s
        """, (coffee_id,))
        categorical_characteristics = cursor.fetchall()
        
        
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
        
        return jsonify(result)
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': str(err)
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert/coffee-type/<int:coffee_id>/characteristics', methods=['POST'])
def update_coffee_characteristics(coffee_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False, 
                'error': 'Сорт кофе не найден'
            }), 404
            
        
        for char in data.get('numeric', []):
            if 'id' not in char or 'min_value' not in char or 'max_value' not in char:
                return jsonify({
                    'success': False,
                    'error': 'Некорректные данные характеристик'
                }), 400
                
            if char['min_value'] is None or char['max_value'] is None:
                return jsonify({
                    'success': False,
                    'error': f'Пустые значения для характеристики {char.get("name", "")}'
                }), 400
                
            if float(char['min_value']) > float(char['max_value']):
                return jsonify({
                    'success': False,
                    'error': f'Минимальное значение больше максимального для характеристики {char.get("name", "")}'
                }), 400

        
        for char in data.get('numeric', []):
            cursor.execute("""
                INSERT INTO coffee_numeric_characteristics 
                (coffee_type_id, characteristic_id, min_value, max_value)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                min_value = VALUES(min_value),
                max_value = VALUES(max_value)
            """, (coffee_id, char['id'], char['min_value'], char['max_value']))

        
        for char in data.get('categorical', []):
            
            if 'id' not in char:
                return jsonify({
                    'success': False,
                    'error': 'Некорректные данные категориальных характеристик'
                }), 400
                
            
            cursor.execute("""
                DELETE FROM coffee_categorical_characteristics 
                WHERE coffee_type_id = %s AND characteristic_id = %s
            """, (coffee_id, char['id']))
            
            
            for value in char.get('values', []):
                cursor.execute("""
                    INSERT INTO coffee_categorical_characteristics 
                    (coffee_type_id, characteristic_id, value)
                    VALUES (%s, %s, %s)
                """, (coffee_id, char['id'], value))

        conn.commit()
        return jsonify({'success': True})

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Ошибка SQL при обновлении характеристик: {err}")
        return jsonify({
            'success': False,
            'error': f'Произошла ошибка при обновлении характеристик: {str(err)}'
        }), 500
    except Exception as e:
        conn.rollback()
        print(f"Непредвиденная ошибка при обновлении характеристик: {e}")
        return jsonify({
            'success': False,
            'error': f'Непредвиденная ошибка: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

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
        
        cursor.execute("""
            SELECT DISTINCT c.id, c.name, c.type, 
                   MIN(cn.min_value) as min_value, 
                   MAX(cn.max_value) as max_value
            FROM characteristics c
            LEFT JOIN coffee_numeric_characteristics cn ON c.id = cn.characteristic_id
            WHERE c.type = 'numeric'
            GROUP BY c.id, c.name, c.type
        """)
        numeric_characteristics = cursor.fetchall()
        
        
        cursor.execute("""
            SELECT DISTINCT c.id, c.name, c.type, 
                   GROUP_CONCAT(DISTINCT cc.value ORDER BY cc.value) AS possible_values
            FROM characteristics c
            LEFT JOIN coffee_categorical_characteristics cc ON c.id = cc.characteristic_id
            WHERE c.type = 'categorical'
            GROUP BY c.id, c.name, c.type
        """)
        categorical_characteristics = cursor.fetchall()
        
        
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
            
            
            for char_id, value in categorical_chars.items():
                cursor.execute("""
                    SELECT c.name, cc.value 
                    FROM coffee_categorical_characteristics cc
                    JOIN characteristics c ON c.id = cc.characteristic_id
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
        
        cursor.execute("SELECT id, name FROM coffee_types ORDER BY name")
        coffee_types = cursor.fetchall()
        
        result = []
        
        
        for coffee in coffee_types:
            
            cursor.execute("""
                SELECT c.id, c.name, c.type, cn.min_value, cn.max_value
                FROM coffee_numeric_characteristics cn
                JOIN characteristics c ON c.id = cn.characteristic_id
                WHERE cn.coffee_type_id = %s
            """, (coffee['id'],))
            numeric_characteristics = cursor.fetchall()
            
            
            cursor.execute("""
                SELECT c.id, c.name, c.type, cc.value
                FROM coffee_categorical_characteristics cc
                JOIN characteristics c ON c.id = cc.characteristic_id
                WHERE cc.coffee_type_id = %s
            """, (coffee['id'],))
            categorical_characteristics = cursor.fetchall()
            
            
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
            
            
            result.append({
                'id': coffee['id'],
                'name': coffee['name'],
                'characteristics': {
                    'numeric': numeric_characteristics,
                    'categorical': list(grouped_categorical.values())
                }
            })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Ошибка при получении базы знаний: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True) 