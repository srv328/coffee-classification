import React, { useState, useEffect, useCallback } from "react";
import { useParams, useLocation } from "react-router-dom";
import axios from "axios";
import AddCharacteristicForm from "./AddCharacteristicForm";
import Swal from "sweetalert2";

const CoffeeTypeDetails = () => {
  const params = useParams();
  const location = useLocation();
  const id = params.id;

  console.log("Params:", params);
  console.log("Location:", location);
  console.log("Extracted ID:", id);
  console.log("Pathname:", location.pathname);
  console.log("Path segments:", location.pathname.split("/"));

  const [coffeeType, setCoffeeType] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCoffeeType = useCallback(async () => {
    if (!id) {
      console.error("ID is undefined or null");
      setLoading(false);
      return;
    }

    const coffeeId = parseInt(id, 10);
    if (isNaN(coffeeId)) {
      console.error("ID is not a valid number:", id);
      setLoading(false);
      return;
    }

    try {
      console.log("Fetching coffee type with ID:", coffeeId);
      const response = await axios.get(
        `http://localhost:5000/api/coffee-types/${coffeeId}`
      );
      setCoffeeType(response.data);
    } catch (error) {
      console.error("Error fetching coffee type:", error);
      Swal.fire({
        icon: "error",
        title: "Ошибка",
        text: "Не удалось загрузить информацию о сорте кофе",
      });
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCoffeeType();
  }, [fetchCoffeeType, id]);

  if (!id) {
    return (
      <div className="alert alert-danger">
        Ошибка: ID сорта кофе не определен в URL. Текущий путь:{" "}
        {location.pathname}
      </div>
    );
  }

  const coffeeId = parseInt(id, 10);
  if (isNaN(coffeeId)) {
    return (
      <div className="alert alert-danger">
        Ошибка: ID сорта кофе должен быть числом. Получено: {id}
      </div>
    );
  }

  if (loading) {
    return <div className="text-center">Загрузка...</div>;
  }

  if (!coffeeType) {
    return <div className="alert alert-warning">Сорт кофе не найден</div>;
  }

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-12">
          <h2>{coffeeType.name}</h2>

          <div className="card mb-4">
            <div className="card-body">
              <h4>Характеристики</h4>
              {coffeeType.characteristics &&
              coffeeType.characteristics.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Название</th>
                      <th>Тип</th>
                      <th>Значения</th>
                    </tr>
                  </thead>
                  <tbody>
                    {coffeeType.characteristics.map((char) => (
                      <tr key={char.id}>
                        <td>{char.name}</td>
                        <td>
                          {char.type === "numeric"
                            ? "Числовая"
                            : "Категориальная"}
                        </td>
                        <td>
                          {char.type === "numeric"
                            ? `${char.min || "Не задано"} - ${
                                char.max || "Не задано"
                              }`
                            : char.values?.join(", ") || "Нет значений"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-muted">Характеристики еще не добавлены</p>
              )}
            </div>
          </div>

          <AddCharacteristicForm
            coffeeId={coffeeId}
            onCharacteristicAdded={fetchCoffeeType}
          />
        </div>
      </div>
    </div>
  );
};

export default CoffeeTypeDetails;
