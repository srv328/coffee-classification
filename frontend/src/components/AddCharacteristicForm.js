import React, { useState, useEffect } from "react";
import axios from "axios";
import Swal from "sweetalert2";

const AddCharacteristicForm = ({ coffeeId, onCharacteristicAdded }) => {
  const [formData, setFormData] = useState({
    name: "",
    type: "numeric",
    values: [""],
    min_value: "",
    max_value: "",
    id: null,
  });

  useEffect(() => {
    console.log("CoffeeId in AddCharacteristicForm:", coffeeId);
  }, [coffeeId]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleValueChange = (index, value) => {
    setFormData((prev) => ({
      ...prev,
      values: prev.values.map((v, i) => (i === index ? value : v)),
    }));
  };

  const addValue = () => {
    setFormData((prev) => ({
      ...prev,
      values: [...prev.values, ""],
    }));
  };

  const removeValue = (index) => {
    setFormData((prev) => ({
      ...prev,
      values: prev.values.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!coffeeId) {
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: "ID сорта кофе не определен",
      });
      return;
    }

    if (!formData.name.trim()) {
      Swal.fire({
        icon: "warning",
        title: "Внимание",
        text: "Введите название характеристики",
      });
      return;
    }

    if (formData.type === "numeric") {
      if (!formData.min_value || !formData.max_value) {
        Swal.fire({
          icon: "warning",
          title: "Внимание",
          text: "Введите диапазон значений для числовой характеристики",
        });
        return;
      }
      if (parseFloat(formData.min_value) > parseFloat(formData.max_value)) {
        Swal.fire({
          icon: "warning",
          title: "Внимание",
          text: "Минимальное значение не может быть больше максимального",
        });
        return;
      }
    }

    if (
      formData.type === "categorical" &&
      formData.values.some((v) => !v.trim())
    ) {
      Swal.fire({
        icon: "warning",
        title: "Внимание",
        text: "Заполните все значения для категориальной характеристики",
      });
      return;
    }

    try {
      const createResponse = await axios.post(
        "http://localhost:5000/api/expert/characteristics",
        {
          name: formData.name.trim(),
          type: formData.type,
          values:
            formData.type === "categorical"
              ? formData.values.filter((v) => v.trim())
              : [],
        }
      );

      if (!createResponse.data.success) {
        throw new Error(
          createResponse.data.error || "Не удалось создать характеристику"
        );
      }

      const characteristicId = createResponse.data.id;

      const response = await axios.post(
        `http://localhost:5000/api/expert/coffee-type/${coffeeId}/add-characteristic`,
        {
          characteristic_id: characteristicId,
          type: formData.type,
          values:
            formData.type === "categorical"
              ? formData.values.filter((v) => v.trim())
              : [],
          min_value:
            formData.type === "numeric" ? parseFloat(formData.min_value) : null,
          max_value:
            formData.type === "numeric" ? parseFloat(formData.max_value) : null,
        }
      );

      if (response.data.success) {
        Swal.fire({
          icon: "success",
          title: "Успешно",
          text: "Характеристика добавлена",
        });
        setFormData({
          name: "",
          type: "numeric",
          values: [""],
          min_value: "",
          max_value: "",
          id: null,
        });
        if (onCharacteristicAdded) {
          onCharacteristicAdded();
        }
      }
    } catch (error) {
      console.error("Error adding characteristic:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text:
          error.response?.data?.error || "Не удалось добавить характеристику",
      });
    }
  };

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h4>Добавить новую характеристику</h4>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Название характеристики</label>
            <input
              type="text"
              className="form-control"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Введите название характеристики"
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Тип характеристики</label>
            <select
              className="form-select"
              name="type"
              value={formData.type}
              onChange={handleInputChange}
            >
              <option value="numeric">Числовая</option>
              <option value="categorical">Категориальная</option>
            </select>
          </div>

          {formData.type === "numeric" && (
            <div className="mb-3">
              <div className="row">
                <div className="col-md-6">
                  <label className="form-label">Минимальное значение</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    name="min_value"
                    value={formData.min_value}
                    onChange={handleInputChange}
                    placeholder="Введите минимальное значение"
                  />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Максимальное значение</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    name="max_value"
                    value={formData.max_value}
                    onChange={handleInputChange}
                    placeholder="Введите максимальное значение"
                  />
                </div>
              </div>
            </div>
          )}

          {formData.type === "categorical" && (
            <div className="mb-3">
              <label className="form-label">Значения</label>
              {formData.values.map((value, index) => (
                <div key={index} className="input-group mb-2">
                  <input
                    type="text"
                    className="form-control"
                    value={value}
                    onChange={(e) => handleValueChange(index, e.target.value)}
                    placeholder={`Значение ${index + 1}`}
                  />
                  <button
                    type="button"
                    className="btn btn-outline-danger"
                    onClick={() => removeValue(index)}
                    disabled={formData.values.length === 1}
                  >
                    Удалить
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={addValue}
              >
                Добавить значение
              </button>
            </div>
          )}

          <button type="submit" className="btn btn-primary">
            Добавить характеристику
          </button>
        </form>
      </div>
    </div>
  );
};

export default AddCharacteristicForm;
