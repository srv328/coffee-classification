import React, { useState, useEffect } from "react";
import {
  Container,
  Card,
  Accordion,
  Table,
  Spinner,
  Alert,
} from "react-bootstrap";
import { translateCharacteristic } from "../utils/translations";
import axios from "axios";

const SpecialistKnowledgeBase = () => {
  const [coffeeTypes, setCoffeeTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchKnowledgeBase();
  }, []);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/specialist/knowledge-base"
      );
      setCoffeeTypes(response.data);
      setLoading(false);
    } catch (err) {
      setError("Ошибка при загрузке базы знаний");
      setLoading(false);
      console.error("Ошибка при загрузке базы знаний:", err);
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
                </Card.Body>
              </Card>
            </Accordion.Body>
          </Accordion.Item>
        ))}
      </Accordion>
    </Container>
  );
};

export default SpecialistKnowledgeBase;
