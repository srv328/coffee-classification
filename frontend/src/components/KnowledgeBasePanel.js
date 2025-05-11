import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Container,
  Card,
  Accordion,
  Table,
  Spinner,
  Alert,
} from "react-bootstrap";
import { translateCharacteristic } from "../utils/translations";

const KnowledgeBasePanel = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCoffeeTypes();
  }, []);

  const fetchCoffeeTypes = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/coffee-types"
      );
      const types = response.data;

      const typesWithCharacteristics = await Promise.all(
        types.map(async (type) => {
          try {
            const charResponse = await axios.get(
              `http://localhost:5000/api/expert/coffee-type/${type.id}/characteristics`
            );
            console.log(`Характеристики для ${type.name}:`, charResponse.data);
            return {
              ...type,
              characteristics: charResponse.data,
            };
          } catch (err) {
            console.error(
              `Ошибка при загрузке характеристик для ${type.name}:`,
              err
            );
            return {
              ...type,
              characteristics: { numeric: [], categorical: [] },
            };
          }
        })
      );

      setCoffeeTypes(typesWithCharacteristics);
      setLoading(false);
    } catch (err) {
      setError("Ошибка при загрузке данных");
      setLoading(false);
      console.error("Ошибка при загрузке данных:", err);
    }
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </Spinner>
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
      <h2 className="mb-4">База знаний</h2>

      <Accordion>
        {coffeeTypes.map((type, index) => (
          <Accordion.Item key={type.id} eventKey={index.toString()}>
            <Accordion.Header>{type.name}</Accordion.Header>
            <Accordion.Body>
              <Card>
                <Card.Body>
                  <h5 className="mb-3">Характеристики:</h5>

                  {type.characteristics.numeric.length > 0 && (
                    <div className="mb-4">
                      <h6>Числовые характеристики:</h6>
                      <Table striped bordered hover size="sm">
                        <thead>
                          <tr>
                            <th>Характеристика</th>
                            <th>Минимальное значение</th>
                            <th>Максимальное значение</th>
                          </tr>
                        </thead>
                        <tbody>
                          {type.characteristics.numeric.map((char) => (
                            <tr key={char.id}>
                              <td>{translateCharacteristic(char.name)}</td>
                              <td>{char.min_value}</td>
                              <td>{char.max_value}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  )}

                  {type.characteristics.categorical.length > 0 && (
                    <div>
                      <h6>Категориальные характеристики:</h6>
                      <Table striped bordered hover size="sm">
                        <thead>
                          <tr>
                            <th>Характеристика</th>
                            <th>Значения</th>
                          </tr>
                        </thead>
                        <tbody>
                          {type.characteristics.categorical.map((char) => (
                            <tr key={char.id}>
                              <td>{translateCharacteristic(char.name)}</td>
                              <td>
                                {char.values.map((value, index) => (
                                  <span
                                    key={index}
                                    className="badge bg-secondary me-1"
                                  >
                                    {value}
                                  </span>
                                ))}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  )}

                  {type.characteristics.numeric.length === 0 &&
                    type.characteristics.categorical.length === 0 && (
                      <Alert variant="warning">
                        Для этого сорта кофе пока не заданы характеристики
                      </Alert>
                    )}
                </Card.Body>
              </Card>
            </Accordion.Body>
          </Accordion.Item>
        ))}
      </Accordion>
    </Container>
  );
};

export default KnowledgeBasePanel;
