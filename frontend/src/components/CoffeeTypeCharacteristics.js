import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import { translateCharacteristic } from "../utils/translations";

const CoffeeTypeCharacteristics = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [selectedCoffeeType, setSelectedCoffeeType] = useState(null);
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: []
  });
  const [selectedCharacteristics, setSelectedCharacteristics] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      // Загружаем список сортов кофе
      const coffeeResponse = await axios.get("http://localhost:5000/api/expert/coffee-types");
      setCoffeeTypes(coffeeResponse.data);

      // Загружаем список характеристик
      const charResponse = await axios.get("http://localhost:5000/api/expert/characteristics");
      setCharacteristics(charResponse.data);

      // Загружаем выбранные характеристики для каждого сорта
      const selectedData = {};
      for (const coffee of coffeeResponse.data) {
        const response = await axios.get(`http://localhost:5000/api/expert/coffee-type/${coffee.id}/characteristics`);
        selectedData[coffee.id] = {
          numeric: response.data.selected.numeric,
          categorical: response.data.selected.categorical
        };
      }
      setSelectedCharacteristics(selectedData);
      
      // Устанавливаем первый сорт кофе как выбранный по умолчанию
      if (coffeeResponse.data.length > 0) {
        setSelectedCoffeeType(coffeeResponse.data[0].id);
      }
    } catch (error) {
      console.error("Ошибка при загрузке данных:", error);
      Swal.fire("Ошибка", "Не удалось загрузить данные", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (coffeeId, charId, type) => {
    try {
      const isSelected = selectedCharacteristics[coffeeId]?.[type]?.includes(charId);
      const newSelected = { ...selectedCharacteristics };
      
      if (!newSelected[coffeeId]) {
        newSelected[coffeeId] = { numeric: [], categorical: [] };
      }

      if (isSelected) {
        // Удаляем характеристику
        newSelected[coffeeId][type] = newSelected[coffeeId][type].filter(id => id !== charId);
      } else {
        // Добавляем характеристику
        newSelected[coffeeId][type].push(charId);
      }

      // Сначала обновляем состояние локально
      setSelectedCharacteristics(newSelected);

      // Затем сохраняем изменения на сервере
      const response = await axios.post(
        `http://localhost:5000/api/expert/coffee-type/${coffeeId}/characteristics`,
        {
          numeric: newSelected[coffeeId].numeric.map(id => ({
            id,
            min_value: 0,
            max_value: 0
          })),
          categorical: newSelected[coffeeId].categorical.map(id => ({
            id,
            values: []
          }))
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || "Ошибка при сохранении");
      }
    } catch (error) {
      console.error("Ошибка при обновлении характеристик:", error);
      Swal.fire("Ошибка", "Не удалось обновить характеристики", "error");
      // В случае ошибки возвращаем предыдущее состояние
      await fetchData();
    }
  };

  if (isLoading) {
    return (
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <h2>Характеристики сортов кофе</h2>
      
      <div className="mb-4">
        <label htmlFor="coffeeTypeSelect" className="form-label">Выберите сорт кофе:</label>
        <select 
          id="coffeeTypeSelect" 
          className="form-select"
          value={selectedCoffeeType || ''}
          onChange={(e) => setSelectedCoffeeType(Number(e.target.value))}
        >
          {coffeeTypes.map(coffee => (
            <option key={coffee.id} value={coffee.id}>
              {coffee.name}
            </option>
          ))}
        </select>
      </div>

      {selectedCoffeeType && (
        <div className="row">
          <div className="col-md-6">
            <h3>Числовые характеристики</h3>
            {characteristics.numeric.map(char => (
              <div key={char.id} className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id={`numeric-${selectedCoffeeType}-${char.id}`}
                  checked={selectedCharacteristics[selectedCoffeeType]?.numeric?.includes(char.id) || false}
                  onChange={() => handleToggle(selectedCoffeeType, char.id, 'numeric')}
                />
                <label className="form-check-label" htmlFor={`numeric-${selectedCoffeeType}-${char.id}`}>
                  {translateCharacteristic(char.name)}
                </label>
              </div>
            ))}
          </div>
          
          <div className="col-md-6">
            <h3>Категориальные характеристики</h3>
            {characteristics.categorical.map(char => (
              <div key={char.id} className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id={`categorical-${selectedCoffeeType}-${char.id}`}
                  checked={selectedCharacteristics[selectedCoffeeType]?.categorical?.includes(char.id) || false}
                  onChange={() => handleToggle(selectedCoffeeType, char.id, 'categorical')}
                />
                <label className="form-check-label" htmlFor={`categorical-${selectedCoffeeType}-${char.id}`}>
                  {translateCharacteristic(char.name)}
                </label>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoffeeTypeCharacteristics; 