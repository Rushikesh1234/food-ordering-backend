# 🍔 Food Ordering Backend (UberEats-Style)
Scalable Food Ordering Backend (FastAPI, PostgreSQL, JWT, Redis, Kafka, RabbitMQ)

A **production-grade backend system** for a multi-restaurant food ordering platform, inspired by UberEats/Doordash/Zomato. Built using **FastAPI**, **PostgreSQL**, and **SQLAlchemy**, following clean architecture and real-world backend engineering principles.

This repository represents **Phase 1 (MVP)** — a fully functional, secure, and scalable backend core.

---

## 🚀 Features (Phase 1 – MVP)

### 👤 Authentication & Authorization
- **Secure Auth:** JWT-based authentication with password hashing via `bcrypt`.
- **RBAC:** Role-Based Access Control (Admin, Restaurant Owner, and Customer).
- **Session Security:** Protected routes using FastAPI dependencies.

### 🏪 Multi-Restaurant Management
- **Independent Scoping:** Restaurants managed as unique entities.
- **Menu Ownership:** Menu items are strictly scoped and validated against specific restaurants.

### 📋 Order Lifecycle & Logic
- **Business Logic Enforcement:** Backend-enforced price calculations (never trust the client).
- **Atomic Transactions:** Database integrity ensured via SQLAlchemy session management.
- **Validation:** Pydantic-driven data validation for every request.

---

## 🏗 Project Architecture

The project follows **Clean Architecture / Service-Oriented** principles to ensure testability and separation of concerns.

```bash
food-ordering-backend/
├── app/
│   ├── api/          # Route handlers (Controllers)
│   ├── core/         # Security (JWT, hashing) and Config
│   ├── db/           # Database session and connection setup
│   ├── models/       # SQLAlchemy ORM models (Data Layer)
│   ├── schemas/      # Pydantic models (Validation Layer)
│   ├── services/     # Business Logic (Service Layer)
├── main.py           # FastAPI entry point
├── .env.example      # Environment variable template
└── requirements.txt  # Project dependencies
```

## 🧩 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | FastAPI (Python) |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy 2.0 |
| **Authentication** | JWT (PyJWT) |
| **Validation** | Pydantic v2 |
| **Architecture** | Clean / Service-Oriented |

## 🛠 Getting Started

### 1. Clone & Setup
```bash
git clone [https://github.com/Rushikesh1234/food-ordering-backend.git](https://github.com/Rushikesh1234/food-ordering-backend.git)
cd food-ordering-backend
python -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Environment Variables
Create a .env file in the root directory:
```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
```

### 3. Run the Server
```bash
uvicorn main:app --reload
```

## 📦 Core Domain Models

- **User**: Handles identity and roles.
- **Restaurant**: The parent entity for menus and orders.
- **MenuItem**: Individual items linked to a restaurant with price snapshots.
- **Order**: The parent record for a transaction (user, restaurant, total).
- **OrderItem**: Line items capturing the price at the time of purchase to ensure historical accuracy.

---

## 🛣 Roadmap

- [ ] **Phase 2**: Event-Driven Architecture (Kafka/RabbitMQ) for Notifications.
- [ ] **Phase 3**: Database Migrations with Alembic.
- [ ] **Phase 4**: Containerization with Docker & Kubernetes.

---

## 👨‍💻 Author
**Rushikesh Khamkar** *Software Engineer (Backend / Systems)* [LinkedIn](https://www.linkedin.com/in/khamkar-rushikesh/) | [GitHub](https://github.com/Rushikesh1234) | [Portfolio](https://rushikesh1234.github.io/Rushikesh_Portfolio/)

---

> **Note:** This project is designed to demonstrate real-world backend decision-making, emphasizing security, data integrity, and clean code standards.