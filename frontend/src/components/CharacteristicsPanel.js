import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import { translateCharacteristic } from "../utils/translations";
import AddCharacteristicForm from "./AddCharacteristicForm";

const CharacteristicsPanel = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [selectedCoffeeType, setSelectedCoffeeType] = useState(null);
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: [],
  });
  const [showAddForm, setShowAddForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchCoffeeTypes();
  }, []);

  const fetchCoffeeTypes = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/coffee-types"
      );
      setCoffeeTypes(response.data);
    } catch (error) {
      Swal.fire("Ошибка", "Не удалось загрузить сорта кофе", "error");
    }
  };

  const fetchCoffeeCharacteristics = async (coffeeId) => {
    setIsLoading(true);
    try {
      console.log(`Загружаем характеристики для сорта с ID=${coffeeId}`);
      const response = await axios.get(
        `http://localhost:5000/api/expert/coffee-type/${coffeeId}/characteristics`
      );
      console.log("Полученные данные:", response.data);
      setCharacteristics({
        numeric: response.data.numeric || [],
        categorical: response.data.categorical || [],
      });
    } catch (error) {
      console.error("Ошибка при загрузке характеристик:", error);
      if (error.response) {
        console.error("Данные ответа:", error.response.data);
        console.error("Статус:", error.response.status);
      }
      Swal.fire("Ошибка", "Не удалось загрузить характеристики", "error");
      setCharacteristics({
        numeric: [],
        categorical: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCoffeeTypeChange = (e) => {
    const coffeeId = parseInt(e.target.value, 10);
    if (isNaN(coffeeId)) {
      setSelectedCoffeeType(null);
      setCharacteristics({ numeric: [], categorical: [] });
    } else {
      setSelectedCoffeeType(coffeeId);
      fetchCoffeeCharacteristics(coffeeId);
    }
    setShowAddForm(false);
  };

  const handleNumericCharacteristicChange = (charId, field, value) => {
    const numericValue = parseFloat(value);
    const isValid = !isNaN(numericValue);

    setCharacteristics((prev) => ({
      ...prev,
      numeric: (prev.numeric || []).map((char) =>
        char.id === charId
          ? {
              ...char,
              [field]: isValid ? numericValue : value,
              isInvalid: {
                ...char.isInvalid,
                [field]: !isValid || value === "",
              },
            }
          : char
      ),
    }));
  };

  const handleCategoricalCharacteristicChange = (charId, selectedValues) => {
    setCharacteristics((prev) => ({
      ...prev,
      categorical: (prev.categorical || []).map((char) =>
        char.id === charId
          ? {
              ...char,
              selected_value_ids: selectedValues,
              selected_values: selectedValues.map(
                (id) => char.values[char.value_ids.indexOf(id)]
              ),
            }
          : char
      ),
    }));
  };

  const handleSaveCharacteristics = async () => {
    if (!selectedCoffeeType) return;

    const invalidNumeric = (characteristics.numeric || []).find(
      (char) =>
        char.min_value === null ||
        char.min_value === undefined ||
        char.min_value === "" ||
        char.max_value === null ||
        char.max_value === undefined ||
        char.max_value === "" ||
        parseFloat(char.min_value) > parseFloat(char.max_value)
    );

    if (invalidNumeric) {
      Swal.fire({
        icon: "warning",
        title: "Некорректные данные",
        text: `Для характеристики "${translateCharacteristic(
          invalidNumeric.name
        )}" указаны некорректные значения. Минимальное значение должно быть меньше или равно максимальному, и поля не могут быть пустыми.`,
      });
      return;
    }

    try {
      const response = await axios.post(
        `http://localhost:5000/api/expert/coffee-type/${selectedCoffeeType}/characteristics`,
        characteristics
      );

      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Характеристики сохранены",
        });
      }
    } catch (error) {
      console.error("Ошибка при сохранении характеристик:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text:
          error.response?.data?.error || "Не удалось сохранить характеристики",
      });
    }
  };

  const handleCharacteristicAdded = () => {
    if (selectedCoffeeType) {
      fetchCoffeeCharacteristics(selectedCoffeeType);
    }
    setShowAddForm(false);
  };

  const handleDeleteCharacteristic = async (characteristicId) => {
    if (!selectedCoffeeType) return;

    const result = await Swal.fire({
      title: "Удалить характеристику?",
      text: "Это действие нельзя отменить!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Да, удалить!",
      cancelButtonText: "Отмена",
    });

    if (result.isConfirmed) {
      try {
        const response = await axios.delete(
          `http://localhost:5000/api/expert/coffee-type/${selectedCoffeeType}/characteristic/${characteristicId}`
        );

        if (response.data.success) {
          Swal.fire({
            icon: "success",
            title: "Успешно",
            text: "Характеристика удалена",
          });
          fetchCoffeeCharacteristics(selectedCoffeeType);
        }
      } catch (error) {
        console.error("Ошибка при удалении характеристики:", error);
        Swal.fire({
          icon: "error",
          title: "Ошибка",
          text:
            error.response?.data?.error || "Не удалось удалить характеристику",
        });
      }
    }
  };

  return (
    <div className="container mt-4">
      <h2>Характеристики сортов кофе</h2>

      <div className="row mb-4">
        <div className="col-md-8">
          <label htmlFor="coffeeTypeSelect" className="form-label">
            Выберите сорт кофе
          </label>
          <select
            id="coffeeTypeSelect"
            className="form-select"
            value={selectedCoffeeType || ""}
            onChange={handleCoffeeTypeChange}
          >
            <option value="">Выберите сорт</option>
            {coffeeTypes.map((coffee) => (
              <option key={coffee.id} value={coffee.id}>
                {coffee.name}
              </option>
            ))}
          </select>
        </div>
        <div className="col-md-4 d-flex align-items-end">
          {selectedCoffeeType && (
            <button
              className="btn btn-success"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              {showAddForm ? "Скрыть форму" : "Добавить характеристику"}
            </button>
          )}
        </div>
      </div>

      {showAddForm &&
        (selectedCoffeeType ? (
          <AddCharacteristicForm
            coffeeId={selectedCoffeeType}
            onCharacteristicAdded={handleCharacteristicAdded}
          />
        ) : (
          <div className="alert alert-warning">
            Пожалуйста, выберите сорт кофе перед добавлением характеристики
          </div>
        ))}

      {isLoading ? (
        <div className="text-center mt-4">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </div>
      ) : (
        selectedCoffeeType && (
          <div>
            <div className="mb-4">
              <h4>Числовые характеристики</h4>
              {(characteristics.numeric || []).map((char) => (
                <div key={char.id} className="card mb-3">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center">
                      <h5 className="card-title">
                        {translateCharacteristic(char.name)}
                      </h5>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteCharacteristic(char.id)}
                      >
                        Удалить
                      </button>
                    </div>
                    <div className="row">
                      <div className="col-md-6">
                        <label className="form-label">
                          Минимальное значение
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          className={`form-control ${
                            char.isInvalid?.min_value ? "is-invalid" : ""
                          }`}
                          value={char.min_value !== null ? char.min_value : ""}
                          onChange={(e) =>
                            handleNumericCharacteristicChange(
                              char.id,
                              "min_value",
                              e.target.value
                            )
                          }
                          required
                        />
                        {char.isInvalid?.min_value && (
                          <div className="invalid-feedback">
                            Введите корректное значение
                          </div>
                        )}
                      </div>
                      <div className="col-md-6">
                        <label className="form-label">
                          Максимальное значение
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          className={`form-control ${
                            char.isInvalid?.max_value ? "is-invalid" : ""
                          }`}
                          value={char.max_value !== null ? char.max_value : ""}
                          onChange={(e) =>
                            handleNumericCharacteristicChange(
                              char.id,
                              "max_value",
                              e.target.value
                            )
                          }
                          required
                        />
                        {char.isInvalid?.max_value && (
                          <div className="invalid-feedback">
                            Введите корректное значение
                          </div>
                        )}
                      </div>
                      {char.min_value !== null &&
                        char.max_value !== null &&
                        parseFloat(char.min_value) >
                          parseFloat(char.max_value) && (
                          <div className="col-12 mt-2">
                            <div className="alert alert-danger py-1">
                              Минимальное значение не может быть больше
                              максимального
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-4">
              <h4>Категориальные характеристики</h4>
              {(characteristics.categorical || []).map((char) => (
                <div key={char.id} className="card mb-3">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center">
                      <h5 className="card-title">
                        {translateCharacteristic(char.name)}
                      </h5>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteCharacteristic(char.id)}
                      >
                        Удалить
                      </button>
                    </div>
                    <div className="row">
                      <div className="col-12">
                        <label className="form-label">Значения</label>
                        <select
                          multiple
                          className="form-select"
                          value={char.selected_value_ids || []}
                          onChange={(e) =>
                            handleCategoricalCharacteristicChange(
                              char.id,
                              Array.from(
                                e.target.selectedOptions,
                                (option) => option.value
                              )
                            )
                          }
                        >
                          {(char.values || []).map((value, index) => (
                            <option key={index} value={value}>
                              {value}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-end">
              <button
                className="btn btn-primary"
                onClick={handleSaveCharacteristics}
              >
                Сохранить изменения
              </button>
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default CharacteristicsPanel;
