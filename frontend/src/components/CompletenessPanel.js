import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Card, Alert, ListGroup } from "react-bootstrap";
import Swal from "sweetalert2";
import { translateCharacteristic } from "../utils/translations";

const CompletenessPanel = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completenessData, setCompletenessData] = useState({
    no_characteristics: [],
    incomplete_values: []
  });

  useEffect(() => {
    checkCompleteness();
  }, []);

  const checkCompleteness = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        "http://localhost:5000/api/expert/completeness-check"
      );
      setCompletenessData(response.data);
      setLoading(false);

      // Показываем предупреждение, если есть проблемы
      if (response.data.no_characteristics.length > 0 || response.data.incomplete_values.length > 0) {
        let message = '';
        
        if (response.data.no_characteristics.length > 0) {
          message += `Сорта без характеристик: ${response.data.no_characteristics.map(c => c.name).join(', ')}\n\n`;
        }
        
        if (response.data.incomplete_values.length > 0) {
          message += 'Сорта с неполными значениями:\n';
          response.data.incomplete_values.forEach(coffee => {
            message += `\n${coffee.name}:\n`;
            if (coffee.empty_numeric.length > 0) {
              message += `- Числовые характеристики с недопустимыми значениями:\n`;
              coffee.empty_numeric.forEach(char => {
                message += `  * ${char}\n`;
              });
            }
            if (coffee.empty_categorical.length > 0) {
              message += `- Категориальные характеристики без значений: ${coffee.empty_categorical.map(translateCharacteristic).join(', ')}\n`;
            }
          });
        }

        Swal.fire({
          icon: "warning",
          title: "Внимание!",
          html: message.replace(/\n/g, '<br>'),
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

  const totalIssues = completenessData.no_characteristics.length + completenessData.incomplete_values.length;

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Проверка полноты данных</h2>

      {totalIssues > 0 ? (
        <>
          {completenessData.no_characteristics.length > 0 && (
            <Alert variant="warning" className="mb-4">
              <h4 className="alert-heading">Сорта без характеристик</h4>
              <p>Следующие сорта кофе не имеют выбранных характеристик:</p>
              <ListGroup>
                {completenessData.no_characteristics.map((type) => (
                  <ListGroup.Item key={type.id} variant="warning">
                    {type.name}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Alert>
          )}

          {completenessData.incomplete_values.length > 0 && (
            <Alert variant="warning" className="mb-4">
              <h4 className="alert-heading">Сорта с неполными значениями</h4>
              {completenessData.incomplete_values.map((coffee) => (
                <div key={coffee.id} className="mb-3">
                  <h5>{coffee.name}</h5>
                  {coffee.empty_numeric.length > 0 && (
                    <div>
                      <strong>Числовые характеристики с недопустимыми значениями:</strong>
                      <ul>
                        {coffee.empty_numeric.map((char, index) => (
                          <li key={index}>{translateCharacteristic(char)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {coffee.empty_categorical.length > 0 && (
                    <div>
                      <strong>Категориальные характеристики без значений:</strong>
                      <ul>
                        {coffee.empty_categorical.map((char, index) => (
                          <li key={index}>{translateCharacteristic(char)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </Alert>
          )}
        </>
      ) : (
        <Alert variant="success">
          <h4 className="alert-heading">Отлично!</h4>
          <p>Все сорта кофе имеют полный набор характеристик и значений.</p>
        </Alert>
      )}

      <Card className="mt-4">
        <Card.Header>Статистика</Card.Header>
        <Card.Body>
          <p>Всего проблем: {totalIssues}</p>
          <p>Сортов без характеристик: {completenessData.no_characteristics.length}</p>
          <p>Сортов с неполными значениями: {completenessData.incomplete_values.length}</p>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default CompletenessPanel;
