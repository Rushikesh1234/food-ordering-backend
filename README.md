# 🍔 Food Ordering Backend (UberEats-Style)
Scalable Food Ordering Backend (FastAPI, PostgreSQL, JWT, Redis, Kafka, RabbitMQ)

---

### This project demonstrates real-world backend system design, including:
- Strict order state machines
- Event-driven microservices
- Asynchronous processing with Kafka
- Driver assignment & acceptance flows

A **production-grade backend system** for a multi-restaurant food ordering platform, inspired by UberEats/Doordash/Zomato. Built using **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Kafka** following clean architecture and real-world backend engineering principles.

This repository represents **Phase 1 (MVP)** — a fully functional, secure, and scalable backend core.

---

## 🚀 Features

### 🔹 Phase 1 – Core Backend (Completed)
#### 👤 Authentication & Authorization
- **Secure Auth:** JWT-based authentication with password hashing via `bcrypt`.
- **RBAC:** Role-Based Access Control (Admin, Restaurant Owner, and Customer).
- **Session Security:** Protected routes using FastAPI dependencies.

#### 🏪 Multi-Restaurant Management
- **Independent Scoping:** Restaurants managed as unique entities.
- **Menu Ownership:** Menu items are strictly scoped and validated against specific restaurants.

#### 📋 Order Lifecycle & Logic
- **Business Logic Enforcement:** Backend-enforced price calculations (never trust the client).
- **Atomic Transactions:** Database integrity ensured via SQLAlchemy session management.
- **Validation:** Pydantic-driven data validation for every request.

### 🔹 Phase 2 – Event-Driven Architecture (Completed)
#### 🔄 End-to-End Order State Machine
A strict, backend-enforced order lifecycle to prevent invalid transitions:
```bash
CREATED
→ ACCEPTED
→ PREPARING
→ READY
→ ASSIGNED
→ PICKED_UP
→ DELIVERED
→ CANCELLED
```
- State transitions validated centrally
- Role-based authorization for each transition
- Prevents skipped or illegal order states

#### 🚗 Driver Assignment & Delivery Flow
- System-driven driver assignment when an order becomes READY
- Drivers can accept or reject assigned orders
- Automatic reassignment if a driver rejects
- Only the assigned driver can pick up and deliver an order

#### 📡 Kafka-Based Event Streaming (Scale Writes - Async writes)
- Kafka topic: order.events
- Events published after successful DB commits
- Used for side effects, not state mutation
**Kafka is used for:**
- Asynchronous notifications (driver, customer)
- Decoupling core order logic from external services
- Enabling horizontal scaling via consumer groups
**Order State Machine is used for:**
- Enforcing business correctness
- Preventing invalid or skipped order transitions
- Acting as the single source of truth for order lifecycle

#### 🧩 Independent Kafka Consumers
**Driver Notification Service**
- Listens for ASSIGNED events
- Notifies drivers of new delivery assignments
**Analytics / Notification–ready architecture**
- Consumers are decoupled and independently scalable

### 🔹 Phase 3 – Reliability & Data Consistency (Completed)
#### 📤 Transactional Outbox Pattern
- **Guaranteed Event Delivery:** Eliminated the "Dual-Write" problem by saving business data and event payloads in a single atomic PostgreSQL transaction.
- **CDC-Ready Architecture:** Used an `outbox` table to act as the source of truth for Kafka events, ensuring Kafka and the Database never get out of sync.
- **Debezium-Style Flow:** Events are persisted to the DB first, then streamed to Kafka, preventing "Ghost Events" if the message broker is down.

#### 🛡️ Distributed Idempotency (Redis)
- **Duplicate Prevention:** Implemented a Redis-backed idempotency layer for consumers.
- **Namespaced Processing:** Used service-specific prefixes (e.g., `driver_service:proc:{id}`) to allow multiple different services to process the same Kafka event without collision.
- **TTL-Based Locking:** Automatic cleanup of processed event IDs to manage Redis memory efficiently.

#### 🔄 Composable Transaction Management
- **Flush vs. Commit:** Refactored service layers to support "Unit of Work" patterns, allowing API routes and Kafka Consumers to control their own transaction boundaries.
---

## ⚙️ Key Architectural Patterns
- **Idempotency & Safety:** I implemented PUT for status updates combined with a central State Machine. This ensures that even if a network retry or a duplicate Kafka message occurs, the system remains in a consistent state and avoids duplicate side effects (like assigning two drivers to one order). State transitions are wrapped in database transactions to ensure that an order never reaches an 'In-Between' state (Atomic) if a system failure occurs during the update

- **Choreography vs. Orchestration:** The system uses an Event-Driven Choreography pattern. The Order Service doesn't "know" about the Notification or Driver Services. It simply broadcasts its state changes, allowing the system to be highly decoupled and independently scalable.

- **Event Enrichment:** Kafka events include an actor_role and context payload. This allows downstream consumers (like Notifications, Drivers) to make decisions instantly without having to perform expensive database lookups, significantly reducing system latency.

- **Reliability & Fault Tolerance**
  - **At-Least-Once Delivery**: Designed consumers to handle Kafka's "at-least-once" guarantee by implementing database-level checks (Idempotency) before processing.
  - **Sequential Ordering**: Used `order_id` as the **Kafka Partition Key** to ensure all events for a specific order are processed in the exact sequence they occurred, preventing race conditions.
  - **Consumer Groups**: Services are organized into unique `group_ids` for horizontal scaling, allowing multiple instances to share the load without double-processing.

- **Transactional Outbox Pattern:** To ensure 100% consistency between the Database and Kafka, I moved away from "Publish-then-Commit." The system now writes event payloads directly into a dedicated `outbox` table within the same transaction as the order update. This ensures that if the database write succeeds, the event is guaranteed to eventually reach Kafka.

- **Distributed Idempotency:** Using Redis as a distributed set, I implemented a "Check-and-Set" logic for all consumers. This ensures that even if Kafka redelivers a message (at-least-once delivery), the business logic (like assigning a driver) only executes exactly once, preventing race conditions and duplicate actions in a multi-instance production environment.

---

## 🏗 Project Architecture

The project follows **Clean Architecture + Event-Driven principles** principles to ensure testability and separation of concerns.

```bash
food-ordering-backend/
├── app/
│   ├── api/          # Route handlers (Controllers)
│   ├── core/         # Security (JWT, hashing) and Config
│   ├── db/           # Database session and connection setup
│   ├── models/       # SQLAlchemy ORM models (Data Layer)
│   ├── schemas/      # Pydantic models (Validation Layer)
│   ├── services/     # Business Logic, State Machine, & Consumers (Service Layer)
│   ├── events/       # Kafka producers & event schemas
├── main.py           # FastAPI entry point
├── .env.example      # Environment variable template
└── requirements.txt  # Project dependencies
```

---

## 🧩 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | FastAPI (Python) |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy 2.0 Composable Transactions (Flush/Commit/atomic)|
| **Authentication** | JWT (PyJWT) |
| **Validation** | Pydantic v2 |
| **Event Streaming** | Apache Kafka |
| **Architecture** | Clean + Event-Driven |
| **Caching/Idempotency** | Redis |
| **Consistency Pattern** | Transactional Outbox |

---

## 📦 Core Domain Models

- **User**: Handles identity and roles.
- **Restaurant**: The parent entity for menus and orders.
- **MenuItem**: Individual items linked to a restaurant with price snapshots.
- **Order**: The parent record for a transaction (user, restaurant, total).
- **OrderItem**: Line items capturing the price at the time of purchase to ensure historical accuracy.

---

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
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Start Kafka Infrastructure
Kafka requires Zookeeper.
```bash
# Start Zookeeper
zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka
kafka-server-start.sh config/server.properties
```

### 4. Start Kafka Consumers (Background Services)
For each consumers (app/services/), use separate terminals:
```bash
cd services/driver_service
pip install -r requirements.txt
python main.py
```
Consumers must run in the background to process events.

### 5. Start Redis Infrastructure
Start Redis (Required for Idempotency)
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

### 6. Run the API Server
```bash
uvicorn main:app --reload
```
---

## 🧪 End-to-End Flow (What You Can Test)
```mermaid
graph TD
  A[CREATED] --> B[ACCEPTED]
  B --> C[PREPARING]
  C --> D[READY]
  D --> E[ASSIGNED]
  E --> F[PICKED_UP]
  F --> G[DELIVERED]

  %% Failure States
  A --> X[CANCELLED]
  B --> X
  E --> X
  G --> Y[REFUNDED]

  style X fill:#f96,stroke:#333
  style Y fill:#f96,stroke:#333
```
---

## 🛣 Roadmap

- [ ] **Phase 4**: Dead Letter Queues (DLQ) for handling "Poison Pill" Kafka messages. RabbitMQ for delayed retries & timeouts (driver no-response handling or for long running processes).
- [ ] **Phase 5**: Elasticsearch for restaurant & menu search, Redis for caching & rate limiting, and Database Indexing (Focusing on Scaled Read).
- [ ] **Phase 6**: Geospatial Queries (PostGIS) (Moving the Driver Service from a simple "First Available" search to a "Nearest Distance" search using spatial indexing.)
- [ ] **Phase 7**: Database Migrations with Alembic.
- [ ] **Phase 8**: Containerization with Docker & Kubernetes.

---

## 👨‍💻 Author
**Rushikesh Khamkar** *Software Engineer (Backend / Systems)* [LinkedIn](https://www.linkedin.com/in/khamkar-rushikesh/) | [GitHub](https://github.com/Rushikesh1234) | [Portfolio](https://rushikesh1234.github.io/Rushikesh_Portfolio/)

---

## ⭐ Final Note:** 
This project is intentionally designed to showcase real backend engineering decisions, including data integrity, asynchronous workflows, and scalable system design — not just CRUD APIs.