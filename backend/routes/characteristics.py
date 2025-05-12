from flask import Blueprint, jsonify, request
from db import get_db_connection
import mysql.connector

characteristics = Blueprint('characteristics', __name__, url_prefix='/api/expert/characteristics')

@characteristics.route('/', methods=['GET'])
def get_characteristics():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Получаем все характеристики
        cursor.execute('SELECT * FROM characteristics ORDER BY name')
        characteristics = cursor.fetchall()
        
        # Разделяем на числовые и категориальные
        numeric = []
        categorical = []

        for char in characteristics:
            if char['type'] == 'numeric':
                # Получаем ограничения для числовых характеристик
                cursor.execute(
                    'SELECT min_value, max_value FROM numeric_characteristic_limits WHERE characteristic_id = %s',
                    (char['id'],)
                )
                limits = cursor.fetchone()
                
                if limits:
                    numeric.append({
                        'id': char['id'],
                        'name': char['name'],
                        'type': char['type'],
                        'min_value': limits['min_value'],
                        'max_value': limits['max_value']
                    })
            else:
                # Получаем значения для категориальных характеристик
                cursor.execute(
                    'SELECT value FROM categorical_values WHERE characteristic_id = %s ORDER BY value',
                    (char['id'],)
                )
                values = cursor.fetchall()
                
                categorical.append({
                    'id': char['id'],
                    'name': char['name'],
                    'type': char['type'],
                    'values': [v['value'] for v in values]
                })

        return jsonify({'numeric': numeric, 'categorical': categorical})
    except Exception as e:
        print('Ошибка при получении характеристик:', str(e))
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@characteristics.route('/', methods=['POST'])
def add_characteristic():
    try:
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        min_value = data.get('min_value')
        max_value = data.get('max_value')
        values = data.get('values', [])

        db = get_db_connection()
        cursor = db.cursor()

        # Начинаем транзакцию
        db.start_transaction()

        # Добавляем характеристику
        cursor.execute(
            'INSERT INTO characteristics (name, type) VALUES (%s, %s)',
            (name, type)
        )
        characteristic_id = cursor.lastrowid

        if type == 'numeric':
            # Добавляем ограничения для числовой характеристики
            cursor.execute(
                'INSERT INTO numeric_characteristic_limits (characteristic_id, min_value, max_value) VALUES (%s, %s, %s)',
                (characteristic_id, min_value, max_value)
            )
        else:
            # Добавляем значения для категориальной характеристики
            for value in values:
                cursor.execute(
                    'INSERT INTO categorical_values (characteristic_id, value) VALUES (%s, %s)',
                    (characteristic_id, value)
                )

        db.commit()
        return jsonify({'success': True, 'id': characteristic_id})
    except Exception as e:
        db.rollback()
        print('Ошибка при добавлении характеристики:', str(e))
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@characteristics.route('/<int:id>', methods=['DELETE'])
def delete_characteristic(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Начинаем транзакцию
        db.start_transaction()

        # Удаляем ограничения числовых характеристик
        cursor.execute('DELETE FROM numeric_characteristic_limits WHERE characteristic_id = %s', (id,))
        
        # Удаляем значения категориальных характеристик
        cursor.execute('DELETE FROM categorical_values WHERE characteristic_id = %s', (id,))
        
        # Удаляем саму характеристику
        cursor.execute('DELETE FROM characteristics WHERE id = %s', (id,))

        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        print('Ошибка при удалении характеристики:', str(e))
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@characteristics.route('/<int:id>/numeric-limits', methods=['PUT'])
def update_numeric_limits(id):
    try:
        data = request.get_json()
        min_value = data.get('min_value')
        max_value = data.get('max_value')

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            'UPDATE numeric_characteristic_limits SET min_value = %s, max_value = %s WHERE characteristic_id = %s',
            (min_value, max_value, id)
        )
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        print('Ошибка при обновлении ограничений:', str(e))
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@characteristics.route('/<int:id>/categorical-values', methods=['PUT'])
def update_categorical_values(id):
    try:
        data = request.get_json()
        values = data.get('values', [])

        db = get_db_connection()
        cursor = db.cursor()

        # Начинаем транзакцию
        db.start_transaction()

        # Удаляем старые значения
        cursor.execute('DELETE FROM categorical_values WHERE characteristic_id = %s', (id,))

        # Добавляем новые значения
        for value in values:
            cursor.execute(
                'INSERT INTO categorical_values (characteristic_id, value) VALUES (%s, %s)',
                (id, value)
            )

        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        print('Ошибка при обновлении значений:', str(e))
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500 