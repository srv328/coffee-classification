from flask import Blueprint, jsonify, request
from db import get_db_connection

coffee_type_characteristics = Blueprint('coffee_type_characteristics', __name__)

@coffee_type_characteristics.route('/coffee-type/<int:coffee_type_id>/characteristics', methods=['GET'])
def get_coffee_type_characteristics(coffee_type_id):
    print(f"Получен запрос на характеристики для сорта кофе {coffee_type_id}")
    conn = None
    cursor = None
    try:
        print("Подключение к базе данных...")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Проверяем существование сорта кофе
        print("Проверка существования сорта кофе...")
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_type_id,))
        if not cursor.fetchone():
            print(f"Сорт кофе {coffee_type_id} не найден")
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404
        
        # Получаем все числовые характеристики
        print("Получение числовых характеристик...")
        cursor.execute("""
            SELECT c.id, c.name, c.type
            FROM characteristics c
            WHERE c.type = 'numeric'
        """)
        all_numeric = cursor.fetchall()
        
        # Получаем выбранные числовые характеристики
        cursor.execute("""
            SELECT characteristic_id
            FROM coffee_numeric_characteristics
            WHERE coffee_type_id = %s
        """, (coffee_type_id,))
        selected_numeric = [row['characteristic_id'] for row in cursor.fetchall()]
        
        # Получаем все категориальные характеристики
        print("Получение категориальных характеристик...")
        cursor.execute("""
            SELECT c.id, c.name, c.type
            FROM characteristics c
            WHERE c.type = 'categorical'
        """)
        all_categorical = cursor.fetchall()
        
        # Получаем выбранные категориальные характеристики
        cursor.execute("""
            SELECT DISTINCT characteristic_id
            FROM coffee_categorical_characteristics
            WHERE coffee_type_id = %s
        """, (coffee_type_id,))
        selected_categorical = [row['characteristic_id'] for row in cursor.fetchall()]
        
        # Формируем ответ
        response = {
            'numeric': all_numeric,
            'categorical': all_categorical,
            'selected': {
                'numeric': selected_numeric,
                'categorical': selected_categorical
            }
        }
        
        print("Успешно сформирован ответ")
        return jsonify(response)

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

@coffee_type_characteristics.route('/coffee-type/<int:coffee_type_id>/characteristics', methods=['POST'])
def update_coffee_type_characteristics(coffee_type_id):
    print(f"Получен запрос на обновление характеристик для сорта кофе {coffee_type_id}")
    conn = None
    cursor = None
    try:
        data = request.get_json()
        print("Получены данные:", data)
        
        print("Подключение к базе данных...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование сорта кофе
        print("Проверка существования сорта кофе...")
        cursor.execute("SELECT id FROM coffee_types WHERE id = %s", (coffee_type_id,))
        if not cursor.fetchone():
            print(f"Сорт кофе {coffee_type_id} не найден")
            return jsonify({
                'success': False,
                'error': 'Сорт кофе не найден'
            }), 404
        
        # Начинаем транзакцию
        print("Начало транзакции...")
        cursor.execute("START TRANSACTION")
        
        # Удаляем все существующие характеристики
        print("Удаление старых характеристик...")
        cursor.execute("DELETE FROM coffee_numeric_characteristics WHERE coffee_type_id = %s", (coffee_type_id,))
        cursor.execute("DELETE FROM coffee_categorical_characteristics WHERE coffee_type_id = %s", (coffee_type_id,))
        
        # Добавляем только выбранные числовые характеристики
        print("Добавление числовых характеристик...")
        for char in data.get('numeric', []):
            print(f"Обработка числовой характеристики: {char}")
            cursor.execute("""
                INSERT INTO coffee_numeric_characteristics 
                (coffee_type_id, characteristic_id, min_value, max_value)
                VALUES (%s, %s, %s, %s)
            """, (coffee_type_id, char['id'], char.get('min_value', 0), char.get('max_value', 0)))
        
        # Добавляем только выбранные категориальные характеристики
        print("Добавление категориальных характеристик...")
        for char in data.get('categorical', []):
            print(f"Обработка категориальной характеристики: {char}")
            # Получаем все возможные значения для характеристики
            cursor.execute("""
                SELECT id FROM categorical_values 
                WHERE characteristic_id = %s
            """, (char['id'],))
            values = cursor.fetchall()
            
            if values:
                # Берем первое значение как дефолтное
                value_id = values[0][0]
                cursor.execute("""
                    INSERT INTO coffee_categorical_characteristics 
                    (coffee_type_id, characteristic_id, categorical_value_id)
                    VALUES (%s, %s, %s)
                """, (coffee_type_id, char['id'], value_id))
        
        # Подтверждаем транзакцию
        print("Подтверждение транзакции...")
        cursor.execute("COMMIT")
        
        print("Характеристики успешно обновлены")
        return jsonify({'success': True})
        
    except Exception as e:
        if conn:
            print("Откат транзакции из-за ошибки...")
            cursor.execute("ROLLBACK")
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