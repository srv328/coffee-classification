import React from "react";
import { Navbar, Nav, Container } from "react-bootstrap";
import { Link } from "react-router-dom";

const Navigation = () => {
  return (
    <Navbar bg="dark" variant="dark" expand="lg">
      <Container>
        <Navbar.Brand as={Link} to="/">
          Система классификации кофе
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/expert/coffee-types">
              Сорта кофе
            </Nav.Link>
            <Nav.Link as={Link} to="/expert/characteristics">
              Характеристики кофе
            </Nav.Link>
            <Nav.Link as={Link} to="/expert/characteristic-values">
              Возможные значения
            </Nav.Link>
            <Nav.Link as={Link} to="/specialist/classify">
              Классификация
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation;
