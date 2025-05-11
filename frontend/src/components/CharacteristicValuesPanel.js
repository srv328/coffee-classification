import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Row, Col, Card, ListGroup } from "react-bootstrap";
import { translateCharacteristic } from "../utils/translations";

const CharacteristicValuesPanel = () => {
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCharacteristicValues();
  }, []);

  const fetchCharacteristicValues = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/expert/characteristics/values"
      );
      setCharacteristics(response.data);
      setLoading(false);
    } catch (err) {
      setError("Ошибка при загрузке значений характеристик");
      setLoading(false);
      console.error("Ошибка при загрузке значений характеристик:", err);
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
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Возможные значения характеристик</h2>

      <Row>
        <Col md={6}>
          <Card className="mb-4">
            <Card.Header>Числовые характеристики</Card.Header>
            <Card.Body>
              <ListGroup variant="flush">
                {characteristics.numeric.map((char) => (
                  <ListGroup.Item key={char.id}>
                    <strong>{translateCharacteristic(char.name)}</strong>
                    <div className="mt-2">
                      <span className="text-muted">Диапазон: </span>
                      от {char.min_value} до {char.max_value}
                    </div>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="mb-4">
            <Card.Header>Категориальные характеристики</Card.Header>
            <Card.Body>
              <ListGroup variant="flush">
                {characteristics.categorical.map((char) => (
                  <ListGroup.Item key={char.id}>
                    <strong>{translateCharacteristic(char.name)}</strong>
                    <div className="mt-2">
                      <span className="text-muted">Возможные значения: </span>
                      {char.possible_values.split(",").map((value, index) => (
                        <span key={index} className="badge bg-secondary me-1">
                          {value}
                        </span>
                      ))}
                    </div>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default CharacteristicValuesPanel;
