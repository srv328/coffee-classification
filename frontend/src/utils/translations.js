// Маппинг для перевода названий характеристик
export const characteristicsTranslation = {
  // Существующие характеристики
  'acidity': 'Кислотность',
  'body': 'Тело',
  'aroma': 'Аромат',
  'flavor': 'Вкус',
  'aftertaste': 'Послевкусие',
  'roast_level': 'Степень обжарки',
  
  // Дополнительные возможные характеристики
  'sweetness': 'Сладость',
  'bitterness': 'Горечь',
  'fruitiness': 'Фруктовость',
  'nutty': 'Ореховость',
  'chocolate': 'Шоколадность',
  'caramel': 'Карамельность',
  'floral': 'Цветочные нотки',
  'spicy': 'Пряность',
  'herbal': 'Травяные нотки',
  'earthiness': 'Землистость',
  'balance': 'Сбалансированность',
  'cleanliness': 'Чистота вкуса',
  'complexity': 'Сложность',
  'finish': 'Финиш',
  'intensity': 'Интенсивность'
};

// Функция для перевода названия
export const translateCharacteristic = (name) => {
  return characteristicsTranslation[name] || name;
}; 