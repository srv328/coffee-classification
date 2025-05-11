import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Container,
  Form,
  Button,
  Card,
  Row,
  Col,
  Alert,
  Spinner,
} from "react-bootstrap";
import { translateCharacteristic } from "../utils/translations";

const SpecialistPanel = () => {
  const [characteristics, setCharacteristics] = useState({
    numeric: [],
    categorical: [],
  });
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [staticResults, setStaticResults] = useState(null);
  const [mlResults, setMlResults] = useState(null);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    fetchCharacteristics();
  }, []);

  const fetchCharacteristics = async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/expert/characteristics/values"
      );
      console.log("Полученные характеристики:", response.data);

      const data = {
        numeric: response.data.numeric || [],
        categorical: response.data.categorical || [],
      };
      setCharacteristics(data);

      const initialFormData = {};
      data.numeric.forEach((char) => {
        initialFormData[`numeric_${char.id}`] = "";
      });
      data.categorical.forEach((char) => {
        initialFormData[`categorical_${char.id}`] = "";
      });
      setFormData(initialFormData);

      setLoading(false);
    } catch (err) {
      console.error("Ошибка при загрузке характеристик:", err);
      setError("Ошибка при загрузке характеристик");
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const validateForm = () => {
    const hasNumericValue = Object.entries(formData).some(
      ([key, value]) => key.startsWith("numeric_") && value !== ""
    );

    const hasCategoricalValue = Object.entries(formData).some(
      ([key, value]) => key.startsWith("categorical_") && value !== ""
    );

    if (!hasNumericValue && !hasCategoricalValue) {
      setFormError("Пожалуйста, заполните хотя бы одну характеристику");
      return false;
    }

    setFormError(null);
    return true;
  };

  const handleStaticAnalysis = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setAnalyzing(true);
    setStaticResults(null);
    setMlResults(null);

    try {
      const requestData = prepareRequestData();
      console.log("Отправляемые данные для статического анализа:", requestData);

      const staticResponse = await axios.post(
        "http://localhost:5000/api/specialist/analyze-static",
        requestData
      );
      console.log("Результаты статического анализа:", staticResponse.data);
      setStaticResults(staticResponse.data);
    } catch (err) {
      console.error("Ошибка при статическом анализе:", err);
      setError("Ошибка при статическом анализе данных");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleMlAnalysis = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setAnalyzing(true);
    setStaticResults(null);
    setMlResults(null);

    try {
      const requestData = prepareRequestData();
      console.log("Отправляемые данные для ML-анализа:", requestData);

      const mlResponse = await axios.post(
        "http://localhost:5000/api/specialist/analyze-ml",
        requestData
      );
      console.log("Результаты ML-анализа:", mlResponse.data);
      setMlResults(mlResponse.data);
    } catch (err) {
      console.error("Ошибка при ML-анализе:", err);
      setError("Ошибка при анализе с помощью нейронной сети");
    } finally {
      setAnalyzing(false);
    }
  };

  const prepareRequestData = () => {
    const requestData = {
      characteristics: {
        numeric: {},
        categorical: {},
      },
    };

    Object.entries(formData).forEach(([key, value]) => {
      if (key.startsWith("numeric_")) {
        const id = key.split("_")[1];
        if (value !== "") {
          requestData.characteristics.numeric[id] = parseFloat(value);
        }
      } else if (key.startsWith("categorical_")) {
        const id = key.split("_")[1];
        if (value !== "") {
          requestData.characteristics.categorical[id] = value;
        }
      }
    });

    console.log("Подготовленные данные для отправки:", requestData);
    return requestData;
  };

  if (loading) {
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </Spinner>
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
      <h2 className="mb-4">Определение сорта кофе</h2>

      <Form>
        {formError && (
          <Alert variant="danger" className="mb-3">
            {formError}
          </Alert>
        )}

        {characteristics.numeric.length > 0 && (
          <Card className="mb-4">
            <Card.Body>
              <h5 className="mb-3">Числовые характеристики</h5>
              <Row>
                {characteristics.numeric.map((char) => (
                  <Col md={6} key={char.id} className="mb-3">
                    <Form.Group>
                      <Form.Label>
                        {translateCharacteristic(char.name)}
                      </Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        name={`numeric_${char.id}`}
                        value={formData[`numeric_${char.id}`]}
                        onChange={handleInputChange}
                      />
                    </Form.Group>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>
        )}

        {characteristics.categorical.length > 0 && (
          <Card className="mb-4">
            <Card.Body>
              <h5 className="mb-3">Категориальные характеристики</h5>
              <Row>
                {characteristics.categorical.map((char) => (
                  <Col md={6} key={char.id} className="mb-3">
                    <Form.Group>
                      <Form.Label>
                        {translateCharacteristic(char.name)}
                      </Form.Label>
                      <Form.Select
                        name={`categorical_${char.id}`}
                        value={formData[`categorical_${char.id}`]}
                        onChange={handleInputChange}
                      >
                        <option value="">Выберите значение</option>
                        {(char.possible_values || "")
                          .split(",")
                          .map((value, index) => (
                            <option key={index} value={value.trim()}>
                              {value.trim()}
                            </option>
                          ))}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>
        )}

        <div className="d-grid gap-2">
          <Row>
            <Col>
              <Button
                variant="primary"
                onClick={handleStaticAnalysis}
                size="lg"
                disabled={analyzing}
                className="w-100"
              >
                {analyzing ? "Анализ..." : "Решатель"}
              </Button>
            </Col>
            <Col>
              <Button
                variant="success"
                onClick={handleMlAnalysis}
                size="lg"
                disabled={analyzing}
                className="w-100"
              >
                {analyzing ? "Анализ..." : "Анализ с помощью ИИ"}
              </Button>
            </Col>
          </Row>
        </div>
      </Form>

      {staticResults && (
        <Card className="mt-4">
          <Card.Header>
            <h5 className="mb-0">Результат классификации (Решатель):</h5>
          </Card.Header>
          <Card.Body>
            <h6>
              Тип кофе:{" "}
              {staticResults.type ||
                "Все гипотезы о сорте кофе опровергнуты. Сорт кофе не определён"}
            </h6>

            <h6 className="mt-3">Объяснение:</h6>
            <ul className="mb-3">
              {staticResults.explanations.map((explanation, index) => (
                <li key={index}>{explanation}</li>
              ))}
            </ul>

            <h6 className="mt-4">Подробный анализ по типам:</h6>
            <div className="mt-3">
              {Object.entries(staticResults.all_types_analysis || {})
                .sort(([, a], [, b]) => {
                  if (a.matches !== b.matches) {
                    return b.matches ? 1 : -1;
                  }
                  return a.name.localeCompare(b.name);
                })
                .map(([typeName, analysis]) => (
                  <Card
                    key={typeName}
                    className="mb-3"
                    border={analysis.matches ? "success" : "danger"}
                  >
                    <Card.Header
                      className={
                        analysis.matches
                          ? "bg-success bg-opacity-10"
                          : "bg-danger bg-opacity-10"
                      }
                    >
                      <h6 className="mb-0">
                        {typeName}
                        {analysis.matches ? (
                          <span className="text-success ms-2">(Подходит)</span>
                        ) : (
                          <span className="text-danger ms-2">
                            (Не подходит)
                          </span>
                        )}
                      </h6>
                    </Card.Header>
                    <Card.Body>
                      <ul className="mb-0">
                        {analysis.reasons
                          .sort((a, b) => {
                            const aContainsNe = a.includes("не");
                            const bContainsNe = b.includes("не");
                            return aContainsNe === bContainsNe
                              ? 0
                              : aContainsNe
                              ? 1
                              : -1;
                          })
                          .map((reason, index) => (
                            <li
                              key={index}
                              className={
                                reason.includes("не")
                                  ? "text-danger"
                                  : "text-success"
                              }
                            >
                              {reason}
                            </li>
                          ))}
                      </ul>
                    </Card.Body>
                  </Card>
                ))}
            </div>
          </Card.Body>
        </Card>
      )}

      {mlResults && (
        <Card className="mt-4">
          <Card.Header>
            <h5 className="mb-0">Результат классификации (Нейронная сеть):</h5>
          </Card.Header>
          <Card.Body>
            <h6>Тип кофе: {mlResults.type}</h6>

            <h6 className="mt-3">Объяснение:</h6>
            <ul className="mb-0">
              {mlResults.explanations.map((explanation, index) => (
                <li key={index}>{explanation}</li>
              ))}
            </ul>

            {mlResults.probabilities && (
              <>
                <h6 className="mt-3">Вероятности:</h6>
                <ul className="mb-0">
                  {Object.entries(mlResults.probabilities)
                    .sort(([, a], [, b]) => b - a)
                    .map(([type, probability]) => (
                      <li key={type}>
                        {type}: {probability.toFixed(2)}%
                      </li>
                    ))}
                </ul>
              </>
            )}
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default SpecialistPanel;
