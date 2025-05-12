import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import { FaTrash } from "react-icons/fa";

const ExpertPanel = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [selectedCoffeeType, setSelectedCoffeeType] = useState(null);
  const [newCoffeeType, setNewCoffeeType] = useState({
    name: "",
  });
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: [],
  });

  useEffect(() => {
    fetchCoffeeTypes();
  }, []);

  const fetchCoffeeTypes = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/expert/coffee-types"
      );
      setCoffeeTypes(response.data);
    } catch (error) {
      Swal.fire("Ошибка", "Не удалось загрузить сорта кофе", "error");
    }
  };

  const fetchCoffeeCharacteristics = async (coffeeId) => {
    try {
      const response = await axios.get(
        `http://localhost:5000/api/expert/coffee-type/${coffeeId}/characteristics`
      );
      console.log("Загруженные характеристики:", response.data);
      setCharacteristics(response.data);
    } catch (error) {
      console.error("Ошибка при загрузке характеристик:", error);
      Swal.fire("Ошибка", "Не удалось загрузить характеристики", "error");
    }
  };

  const handleAddCoffeeType = async () => {
    if (!newCoffeeType.name.trim()) {
      Swal.fire({
        icon: "warning",
        title: "Внимание",
        text: "Название сорта кофе не может быть пустым",
      });
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5000/api/expert/add-coffee-type",
        {
          name: newCoffeeType.name.trim(),
        }
      );

      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Новый сорт кофе добавлен",
        });
        setNewCoffeeType({ name: "" });
        fetchCoffeeTypes();
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.error || "Не удалось добавить сорт кофе";
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: errorMessage,
      });
    }
  };

  const handleCoffeeTypeSelect = async (coffee) => {
    setSelectedCoffeeType(coffee);
    await fetchCoffeeCharacteristics(coffee.id);
  };

  const handleNumericCharacteristicChange = (charId, field, value) => {
    setCharacteristics((prev) => ({
      ...prev,
      numeric: prev.numeric.map((char) =>
        char.id === charId ? { ...char, [field]: value } : char
      ),
    }));
  };

  const handleCategoricalCharacteristicChange = (charId, selectedValues) => {
    setCharacteristics((prev) => ({
      ...prev,
      categorical: prev.categorical.map((char) =>
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

    try {
      const response = await axios.post(
        `http://localhost:5000/api/expert/coffee-type/${selectedCoffeeType.id}/characteristics`,
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
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text:
          error.response?.data?.error || "Не удалось сохранить характеристики",
      });
    }
  };

  const handleDeleteCoffeeType = async (coffeeId, coffeeName) => {
    try {
      const result = await Swal.fire({
        title: "Подтверждение удаления",
        text: `Вы действительно хотите удалить сорт кофе "${coffeeName}"?`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Да, удалить",
        cancelButtonText: "Отмена",
      });

      if (result.isConfirmed) {
        const response = await axios.delete(
          `http://localhost:5000/api/expert/delete-coffee-type/${coffeeId}`
        );

        if (response.data.success) {
          Swal.fire({
            icon: "success",
            title: "Успешно",
            text: "Сорт кофе успешно удален",
          });

          if (selectedCoffeeType?.id === coffeeId) {
            setSelectedCoffeeType(null);
            setCharacteristics({ numeric: [], categorical: [] });
          }

          fetchCoffeeTypes();
        }
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.error || "Не удалось удалить сорт кофе";
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: errorMessage,
      });
    }
  };

  return (
    <div className="container mt-4">
      <h2>Панель эксперта</h2>

      <div className="row mt-4">
        <div className="col-md-6">
          <h3>Добавить новый сорт кофе</h3>
          <div className="mb-3">
            <label htmlFor="name" className="form-label">
              Название
            </label>
            <input
              type="text"
              className="form-control"
              id="name"
              value={newCoffeeType.name}
              onChange={(e) =>
                setNewCoffeeType({ ...newCoffeeType, name: e.target.value })
              }
            />
          </div>
          <button className="btn btn-primary" onClick={handleAddCoffeeType}>
            Добавить
          </button>
        </div>

        <div className="col-md-6">
          <h3>Существующие сорта</h3>
          <div className="list-group">
            {coffeeTypes.map((coffee) => (
              <div
                key={coffee.id}
                className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${
                  selectedCoffeeType?.id === coffee.id ? "active" : ""
                }`}
              >
                <span
                  className="flex-grow-1"
                  onClick={() => handleCoffeeTypeSelect(coffee)}
                  style={{ cursor: "pointer" }}
                >
                  {coffee.name}
                </span>
                <button
                  className="btn btn-link text-danger p-0 ms-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCoffeeType(coffee.id, coffee.name);
                  }}
                  style={{
                    opacity: selectedCoffeeType?.id === coffee.id ? 0.7 : 1,
                    color:
                      selectedCoffeeType?.id === coffee.id ? "#fff" : undefined,
                  }}
                >
                  <FaTrash />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedCoffeeType && (
        <div className="row mt-4">
          <div className="col-12">
            <h3>Характеристики для {selectedCoffeeType.name}</h3>

            <div className="mb-4">
              <h4>Числовые характеристики</h4>
              {characteristics.numeric.map((char) => (
                <div key={char.id} className="card mb-3">
                  <div className="card-body">
                    <h5 className="card-title">{char.name}</h5>
                    <div className="row">
                      <div className="col-md-6">
                        <label className="form-label">
                          Минимальное значение
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          className="form-control"
                          value={char.min_value || ""}
                          onChange={(e) =>
                            handleNumericCharacteristicChange(
                              char.id,
                              "min_value",
                              parseFloat(e.target.value)
                            )
                          }
                        />
                      </div>
                      <div className="col-md-6">
                        <label className="form-label">
                          Максимальное значение
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          className="form-control"
                          value={char.max_value || ""}
                          onChange={(e) =>
                            handleNumericCharacteristicChange(
                              char.id,
                              "max_value",
                              parseFloat(e.target.value)
                            )
                          }
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-4">
              <h4>Категориальные характеристики</h4>
              {characteristics.categorical.map((char) => (
                <div key={char.id} className="card mb-3">
                  <div className="card-body">
                    <h5 className="card-title">{char.name}</h5>
                    <select
                      className="form-select"
                      multiple
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
                      style={{ height: "150px" }}
                    >
                      {char.value_ids.map((valueId, index) => (
                        <option key={valueId} value={valueId}>
                          {char.values[index]}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-4">
              <button
                className="btn btn-primary"
                onClick={handleSaveCharacteristics}
              >
                Сохранить характеристики
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpertPanel;
