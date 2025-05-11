import React, { useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate,
  useLocation,
} from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

// Компоненты
import ExpertPanel from "./components/ExpertPanel";
import CharacteristicsPanel from "./components/CharacteristicsPanel";
import CoffeeTypeDetails from "./components/CoffeeTypeDetails";
import CharacteristicValuesPanel from "./components/CharacteristicValuesPanel";
import SpecialistPanel from "./components/SpecialistPanel";
import CompletenessPanel from "./components/CompletenessPanel";
import KnowledgeBasePanel from "./components/KnowledgeBasePanel";
import SpecialistKnowledgeBase from "./components/SpecialistKnowledgeBase";

function UserSelect({ onSelect }) {
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 text-center">
          <h2>Система классификации кофе</h2>
          <div className="mt-4">
            <button
              className="btn btn-primary me-3"
              onClick={() => onSelect("expert")}
            >
              Войти как эксперт
            </button>
            <button
              className="btn btn-success"
              onClick={() => onSelect("specialist")}
            >
              Войти как специалист
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Layout({ userType, onLogout, children }) {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <div className="d-flex">
      <div
        className="sidebar bg-light"
        style={{ width: "300px", minHeight: "100vh" }}
      >
        <div className="p-3">
          <div className="d-flex justify-content-between align-items-center border-bottom pb-2">
            <h4 className="mb-0 me-4">
              {userType === "expert" ? "Эксперт" : "Специалист"}
            </h4>
            <button
              className="btn btn-outline-danger btn-sm"
              style={{ minWidth: "100px" }}
              onClick={onLogout}
            >
              <i className="bi bi-box-arrow-right me-1"></i>
              Выйти
            </button>
          </div>
        </div>
        <div className="nav flex-column">
          {userType === "expert" && (
            <>
              <div className="sidebar-heading px-3 mt-2 mb-3 text-muted">
                <h6>Управление данными</h6>
              </div>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/expert/coffee-types")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/expert/coffee-types"
              >
                Сорта кофе
              </Link>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/expert/characteristics")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/expert/characteristics"
              >
                Характеристики кофе
              </Link>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/expert/possible-values")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/expert/possible-values"
              >
                Возможные значения
              </Link>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/expert/completeness")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/expert/completeness"
              >
                Проверка полноты
              </Link>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/expert/knowledge-base")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/expert/knowledge-base"
              >
                Просмотреть базу знаний
              </Link>
            </>
          )}
          {userType === "specialist" && (
            <>
              <div className="sidebar-heading px-3 mt-2 mb-3 text-muted">
                <h6>Анализ кофе</h6>
              </div>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/specialist/classify")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/specialist/classify"
              >
                Классификация
              </Link>
              <Link
                className={`nav-link mb-2 ${
                  isActive("/specialist/knowledge-base")
                    ? "active bg-secondary text-white"
                    : "text-dark"
                }`}
                to="/specialist/knowledge-base"
              >
                База знаний
              </Link>
            </>
          )}
        </div>
      </div>
      <div className="flex-grow-1 p-4">{children}</div>
    </div>
  );
}

function App() {
  const [userType, setUserType] = useState(null);

  const handleLogout = () => {
    setUserType(null);
  };

  if (!userType) {
    return <UserSelect onSelect={setUserType} />;
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <Navigate
              to={
                userType === "expert"
                  ? "/expert/coffee-types"
                  : "/specialist/classify"
              }
            />
          }
        />

        {/* Маршруты эксперта */}
        <Route
          path="/expert/*"
          element={
            userType === "expert" ? (
              <Layout userType={userType} onLogout={handleLogout}>
                <Routes>
                  <Route
                    path="/"
                    element={<div>Панель управления эксперта</div>}
                  />
                  <Route path="coffee-types" element={<ExpertPanel />} />
                  <Route
                    path="characteristics"
                    element={<CharacteristicsPanel />}
                  />
                  <Route
                    path="possible-values"
                    element={<CharacteristicValuesPanel />}
                  />
                  <Route
                    path="type-values"
                    element={<div>Управление значениями для сортов</div>}
                  />
                  <Route path="completeness" element={<CompletenessPanel />} />
                  <Route
                    path="knowledge-base"
                    element={<KnowledgeBasePanel />}
                  />
                  <Route
                    path="initial-data"
                    element={<div>Ввод исходных данных</div>}
                  />
                  <Route
                    path="coffee-type/:id"
                    element={<CoffeeTypeDetails />}
                  />
                  <Route path="*" element={<Navigate to="/expert" replace />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/" replace />
            )
          }
        />

        {/* Маршруты специалиста */}
        <Route
          path="/specialist/*"
          element={
            userType === "specialist" ? (
              <Layout userType={userType} onLogout={handleLogout}>
                <Routes>
                  <Route
                    path="/"
                    element={<Navigate to="/specialist/classify" replace />}
                  />
                  <Route path="classify" element={<SpecialistPanel />} />
                  <Route
                    path="knowledge-base"
                    element={<SpecialistKnowledgeBase />}
                  />
                  <Route
                    path="*"
                    element={<Navigate to="/specialist/classify" replace />}
                  />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
