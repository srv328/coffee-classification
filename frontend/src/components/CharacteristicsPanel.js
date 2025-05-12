import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import { translateCharacteristic } from "../utils/translations";

const CharacteristicsPanel = () => {
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCharacteristic, setNewCharacteristic] = useState({
    name: "",
    type: "numeric",
    min_value: "",
    max_value: "",
    values: [],
  });

  // Состояния для редактируемых значений
  const [editingNumeric, setEditingNumeric] = useState({});
  const [editingCategorical, setEditingCategorical] = useState({});

  useEffect(() => {
    fetchCharacteristics();
  }, []);

  const fetchCharacteristics = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get("http://localhost:5000/api/expert/characteristics");
      setCharacteristics(response.data);
      // Инициализируем состояния редактирования
      const numericEditing = {};
      const categoricalEditing = {};
      response.data.numeric.forEach(char => {
        numericEditing[char.id] = { min_value: char.min_value, max_value: char.max_value };
      });
      response.data.categorical.forEach(char => {
        categoricalEditing[char.id] = { values: [...char.values] };
      });
      setEditingNumeric(numericEditing);
      setEditingCategorical(categoricalEditing);
    } catch (error) {
      console.error("Ошибка при загрузке характеристик:", error);
      Swal.fire("Ошибка", "Не удалось загрузить характеристики", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCharacteristic = async () => {
    try {
      const response = await axios.post("http://localhost:5000/api/expert/characteristics", newCharacteristic);
      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Характеристика добавлена",
        });
        setShowAddForm(false);
        setNewCharacteristic({
          name: "",
          type: "numeric",
          min_value: "",
          max_value: "",
          values: [],
        });
        fetchCharacteristics();
      }
    } catch (error) {
      console.error("Ошибка при добавлении характеристики:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: error.response?.data?.error || "Не удалось добавить характеристику",
      });
    }
  };

  const handleDeleteCharacteristic = async (characteristicId) => {
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
        const response = await axios.delete(`http://localhost:5000/api/expert/characteristics/${characteristicId}`);
        if (response.data.success) {
          Swal.fire({
            icon: "success",
            title: "Успешно",
            text: "Характеристика удалена",
          });
          fetchCharacteristics();
        }
      } catch (error) {
        console.error("Ошибка при удалении характеристики:", error);
        Swal.fire({
          icon: "error",
          title: "Ошибка",
          text: error.response?.data?.error || "Не удалось удалить характеристику",
        });
      }
    }
  };

  const handleNumericChange = (charId, field, value) => {
    setEditingNumeric(prev => ({
      ...prev,
      [charId]: {
        ...prev[charId],
        [field]: value
      }
    }));
  };

  const handleCategoricalChange = (charId, values) => {
    setEditingCategorical(prev => ({
      ...prev,
      [charId]: {
        values: values.split(",").map(v => v.trim()).filter(v => v)
      }
    }));
  };

  const validateNumericLimits = (minValue, maxValue) => {
    if (minValue === "" || maxValue === "") {
      return "Все поля должны быть заполнены";
    }
    if (parseFloat(minValue) >= parseFloat(maxValue)) {
      return "Минимальное значение должно быть меньше максимального";
    }
    return null;
  };

  const validateCategoricalValues = (values) => {
    if (values.length === 0) {
      return "Должно быть указано хотя бы одно значение";
    }
    if (values.some(v => v === "")) {
      return "Все значения должны быть заполнены";
    }
    return null;
  };

  const handleSaveNumericLimits = async (charId) => {
    const { min_value, max_value } = editingNumeric[charId];
    const error = validateNumericLimits(min_value, max_value);
    
    if (error) {
      Swal.fire({
        icon: "error",
        title: "Ошибка валидации",
        text: error
      });
      return;
    }

    try {
      const response = await axios.put(`http://localhost:5000/api/expert/characteristics/${charId}/numeric-limits`, {
        min_value: parseFloat(min_value),
        max_value: parseFloat(max_value)
      });
      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Ограничения обновлены"
        });
        fetchCharacteristics();
      }
    } catch (error) {
      console.error("Ошибка при обновлении ограничений:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: error.response?.data?.error || "Не удалось обновить ограничения"
      });
    }
  };

  const handleSaveCategoricalValues = async (charId) => {
    const { values } = editingCategorical[charId];
    const error = validateCategoricalValues(values);
    
    if (error) {
      Swal.fire({
        icon: "error",
        title: "Ошибка валидации",
        text: error
      });
      return;
    }

    try {
      const response = await axios.put(`http://localhost:5000/api/expert/characteristics/${charId}/categorical-values`, {
        values: values
      });
      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Значения обновлены"
        });
        fetchCharacteristics();
      }
    } catch (error) {
      console.error("Ошибка при обновлении значений:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: error.response?.data?.error || "Не удалось обновить значения"
      });
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Характеристики кофе</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? "Отмена" : "Добавить характеристику"}
        </button>
      </div>

      {showAddForm && (
        <div className="card mb-4">
          <div className="card-body">
            <h5 className="card-title">Новая характеристика</h5>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label className="form-label">Название</label>
                <input
                  type="text"
                  className="form-control"
                  value={newCharacteristic.name}
                  onChange={(e) =>
                    setNewCharacteristic({ ...newCharacteristic, name: e.target.value })
                  }
                />
              </div>
              <div className="col-md-6 mb-3">
                <label className="form-label">Тип</label>
                <select
                  className="form-select"
                  value={newCharacteristic.type}
                  onChange={(e) =>
                    setNewCharacteristic({ ...newCharacteristic, type: e.target.value })
                  }
                >
                  <option value="numeric">Числовая</option>
                  <option value="categorical">Категориальная</option>
                </select>
              </div>
              {newCharacteristic.type === "numeric" ? (
                <>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Минимальное значение</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newCharacteristic.min_value}
                      onChange={(e) =>
                        setNewCharacteristic({
                          ...newCharacteristic,
                          min_value: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Максимальное значение</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newCharacteristic.max_value}
                      onChange={(e) =>
                        setNewCharacteristic({
                          ...newCharacteristic,
                          max_value: e.target.value,
                        })
                      }
                    />
                  </div>
                </>
              ) : (
                <div className="col-12 mb-3">
                  <label className="form-label">Возможные значения (через запятую)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newCharacteristic.values.join(", ")}
                    onChange={(e) =>
                      setNewCharacteristic({
                        ...newCharacteristic,
                        values: e.target.value.split(",").map((v) => v.trim()),
                      })
                    }
                  />
                </div>
              )}
            </div>
            <button
              className="btn btn-success"
              onClick={handleAddCharacteristic}
            >
              Добавить
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </div>
      ) : (
        <>
          <div className="mb-4">
            <h4>Числовые характеристики</h4>
            {characteristics.numeric.map((char) => (
              <div key={char.id} className="card mb-3">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h5 className="card-title mb-0">{translateCharacteristic(char.name)}</h5>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteCharacteristic(char.id)}
                    >
                      Удалить
                    </button>
                  </div>
                  <div className="row">
                    <div className="col-md-5">
                      <label className="form-label">Минимальное значение</label>
                      <input
                        type="number"
                        className="form-control"
                        value={editingNumeric[char.id]?.min_value || ""}
                        onChange={(e) => handleNumericChange(char.id, "min_value", e.target.value)}
                      />
                    </div>
                    <div className="col-md-5">
                      <label className="form-label">Максимальное значение</label>
                      <input
                        type="number"
                        className="form-control"
                        value={editingNumeric[char.id]?.max_value || ""}
                        onChange={(e) => handleNumericChange(char.id, "max_value", e.target.value)}
                      />
                    </div>
                    <div className="col-md-2 d-flex align-items-end">
                      <button
                        className="btn btn-primary w-100"
                        onClick={() => handleSaveNumericLimits(char.id)}
                      >
                        Сохранить
                      </button>
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
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h5 className="card-title mb-0">{translateCharacteristic(char.name)}</h5>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteCharacteristic(char.id)}
                    >
                      Удалить
                    </button>
                  </div>
                  <div className="row">
                    <div className="col-10">
                      <label className="form-label">Возможные значения (через запятую)</label>
                      <input
                        type="text"
                        className="form-control"
                        value={editingCategorical[char.id]?.values.join(", ") || ""}
                        onChange={(e) => handleCategoricalChange(char.id, e.target.value)}
                      />
                    </div>
                    <div className="col-2 d-flex align-items-end">
                      <button
                        className="btn btn-primary w-100"
                        onClick={() => handleSaveCategoricalValues(char.id)}
                      >
                        Сохранить
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default CharacteristicsPanel;
