import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Card, Alert, ListGroup } from "react-bootstrap";
import Swal from "sweetalert2";

const CompletenessPanel = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [incompleteTypes, setIncompleteTypes] = useState([]);

  useEffect(() => {
    checkCompleteness();
  }, []);

  const checkCompleteness = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        "http://localhost:5000/api/coffee-types"
      );
      const types = response.data;
      setCoffeeTypes(types);

      const incomplete = [];
      for (const type of types) {
        try {
          const charResponse = await axios.get(
            `http://localhost:5000/api/expert/coffee-type/${type.id}/characteristics`
          );
          const characteristics = charResponse.data;

          if (
            (!characteristics.numeric ||
              characteristics.numeric.length === 0) &&
            (!characteristics.categorical ||
              characteristics.categorical.length === 0)
          ) {
            incomplete.push(type);
          }
        } catch (err) {
          console.error(
            `Ошибка при проверке характеристик для сорта ${type.name}:`,
            err
          );
        }
      }

      setIncompleteTypes(incomplete);
      setLoading(false);

      if (incomplete.length > 0) {
        Swal.fire({
          icon: "warning",
          title: "Внимание!",
          html: `Найдено ${incomplete.length} сортов кофе без характеристик. 
                           Пожалуйста, добавьте характеристики для этих сортов.`,
          confirmButtonText: "Понятно",
        });
      }
    } catch (err) {
      setError("Ошибка при проверке полноты данных");
      setLoading(false);
      console.error("Ошибка при проверке полноты данных:", err);
    }
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Проверка полноты данных</h2>

      {incompleteTypes.length > 0 ? (
        <Alert variant="warning" className="mb-4">
          <h4 className="alert-heading">Внимание!</h4>
          <p>
            Найдены сорта кофе без характеристик. Пожалуйста, добавьте
            характеристики для этих сортов:
          </p>
          <ListGroup>
            {incompleteTypes.map((type) => (
              <ListGroup.Item key={type.id} variant="warning">
                {type.name}
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Alert>
      ) : (
        <Alert variant="success">
          <h4 className="alert-heading">Отлично!</h4>
          <p>Все сорта кофе имеют характеристики. Данные полные.</p>
        </Alert>
      )}

      <Card className="mt-4">
        <Card.Header>Статистика</Card.Header>
        <Card.Body>
          <p>Всего сортов кофе: {coffeeTypes.length}</p>
          <p>Сортов без характеристик: {incompleteTypes.length}</p>
          <p>
            Сортов с характеристиками:{" "}
            {coffeeTypes.length - incompleteTypes.length}
          </p>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default CompletenessPanel;
