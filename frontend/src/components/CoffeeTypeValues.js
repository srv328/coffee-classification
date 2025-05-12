import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import { translateCharacteristic } from "../utils/translations";

const CoffeeTypeValues = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [selectedCoffeeType, setSelectedCoffeeType] = useState(null);
  const [characteristicValues, setCharacteristicValues] = useState({
    numeric: [],
    categorical: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchCoffeeTypes();
  }, []);

  useEffect(() => {
    if (selectedCoffeeType) {
      fetchCharacteristicValues(selectedCoffeeType);
    }
  }, [selectedCoffeeType]);

  const fetchCoffeeTypes = async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/expert/coffee-types");
      setCoffeeTypes(response.data);
      if (response.data.length > 0) {
        setSelectedCoffeeType(response.data[0].id);
      }
    } catch (error) {
      console.error("Ошибка при загрузке сортов кофе:", error);
      Swal.fire("Ошибка", "Не удалось загрузить список сортов кофе", "error");
    }
  };

  const fetchCharacteristicValues = async (coffeeTypeId) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`http://localhost:5000/api/expert/coffee-type/${coffeeTypeId}/values`);
      setCharacteristicValues(response.data);
      setHasChanges(false);
    } catch (error) {
      console.error("Ошибка при загрузке значений характеристик:", error);
      Swal.fire("Ошибка", "Не удалось загрузить значения характеристик", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNumericValueChange = (charId, field, value) => {
    const newValue = parseFloat(value);
    const char = characteristicValues.numeric.find(c => c.id === charId);
    
    if (!char) return;

    // Обновляем локальное состояние без проверок
    setCharacteristicValues(prev => ({
      ...prev,
      numeric: prev.numeric.map(c => 
        c.id === charId 
          ? { ...c, coffee_min: field === 'min' ? newValue : c.coffee_min, coffee_max: field === 'max' ? newValue : c.coffee_max }
          : c
      )
    }));
    setHasChanges(true);
  };

  const handleCategoricalValueChange = (charId, values) => {
    // Преобразуем значения в массив, если это не массив
    const selectedValues = Array.isArray(values) ? values : [values];
    
    setCharacteristicValues(prev => ({
      ...prev,
      categorical: prev.categorical.map(c => 
        c.id === charId 
          ? { ...c, selected_values: selectedValues }
          : c
      )
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      // Проверяем все числовые значения перед сохранением
      const invalidNumeric = characteristicValues.numeric.find(char => {
        // Проверяем глобальные ограничения
        if (parseFloat(char.coffee_min) < parseFloat(char.global_min) || 
            parseFloat(char.coffee_min) > parseFloat(char.global_max) ||
            parseFloat(char.coffee_max) < parseFloat(char.global_min) || 
            parseFloat(char.coffee_max) > parseFloat(char.global_max)) {
          return true;
        }
        // Проверяем, что минимум не больше максимума
        if (parseFloat(char.coffee_min) > parseFloat(char.coffee_max)) {
          return true;
        }
        return false;
      });
      
      if (invalidNumeric) {
        Swal.fire({
          icon: "error",
          title: "Ошибка валидации",
          text: `Для характеристики "${translateCharacteristic(invalidNumeric.name)}" значения некорректны. Проверьте, что:
            - Значения находятся в пределах от ${parseFloat(invalidNumeric.global_min)} до ${parseFloat(invalidNumeric.global_max)}
            - Минимальное значение не больше максимального`
        });
        return;
      }

      const response = await axios.post(
        `http://localhost:5000/api/expert/coffee-type/${selectedCoffeeType}/values`,
        {
          numeric: characteristicValues.numeric.map(char => ({
            id: char.id,
            min_value: parseFloat(char.coffee_min),
            max_value: parseFloat(char.coffee_max)
          })),
          categorical: characteristicValues.categorical.map(char => ({
            id: char.id,
            selected_values: char.selected_values || []
          }))
        }
      );

      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Значения характеристик сохранены"
        });
        setHasChanges(false);
      }
    } catch (error) {
      console.error("Ошибка при сохранении значений:", error);
      Swal.fire("Ошибка", "Не удалось сохранить значения характеристик", "error");
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
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Значения свойств для сорта</h2>
        <button 
          className="btn btn-primary"
          onClick={handleSave}
          disabled={!hasChanges}
        >
          Сохранить изменения
        </button>
      </div>
      
      <div className="mb-4">
        <label htmlFor="coffeeTypeSelect" className="form-label">Выберите сорт кофе:</label>
        <select 
          id="coffeeTypeSelect" 
          className="form-select"
          value={selectedCoffeeType || ''}
          onChange={(e) => {
            if (hasChanges) {
              Swal.fire({
                title: 'Есть несохраненные изменения',
                text: 'Хотите сохранить изменения перед переходом?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Да, сохранить',
                cancelButtonText: 'Нет, отменить'
              }).then((result) => {
                if (result.isConfirmed) {
                  handleSave().then(() => setSelectedCoffeeType(Number(e.target.value)));
                } else {
                  setSelectedCoffeeType(Number(e.target.value));
                }
              });
            } else {
              setSelectedCoffeeType(Number(e.target.value));
            }
          }}
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
            {characteristicValues.numeric.map(char => (
              <div key={char.id} className="mb-3">
                <label className="form-label">{translateCharacteristic(char.name)}</label>
                <div className="row">
                  <div className="col">
                    <input
                      type="number"
                      className="form-control"
                      placeholder="Мин. значение"
                      min={char.global_min}
                      max={char.global_max}
                      value={char.coffee_min || ''}
                      onChange={(e) => handleNumericValueChange(char.id, 'min', e.target.value)}
                    />
                  </div>
                  <div className="col">
                    <input
                      type="number"
                      className="form-control"
                      placeholder="Макс. значение"
                      min={char.global_min}
                      max={char.global_max}
                      value={char.coffee_max || ''}
                      onChange={(e) => handleNumericValueChange(char.id, 'max', e.target.value)}
                    />
                  </div>
                </div>
                <small className="text-muted">
                  Допустимый диапазон: {char.global_min} - {char.global_max}
                </small>
              </div>
            ))}
          </div>
          
          <div className="col-md-6">
            <h3>Категориальные характеристики</h3>
            {characteristicValues.categorical.map(char => (
              <div key={char.id} className="mb-3">
                <label className="form-label">{translateCharacteristic(char.name)}</label>
                <select
                  className="form-select"
                  multiple
                  value={char.selected_values || []}
                  onChange={(e) => {
                    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                    handleCategoricalValueChange(char.id, selectedOptions);
                  }}
                >
                  {char.available_values?.map(value => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
                <small className="text-muted">
                  Для выбора нескольких значений удерживайте Ctrl (Cmd на Mac)
                </small>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoffeeTypeValues; 