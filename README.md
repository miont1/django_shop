# 🍺 Hop & Barley — Homebrewing E-Commerce Store & REST API

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-6.0.6-green.svg)](https://www.djangoproject.com/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checker](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](http://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-82%20passed-success.svg)](https://docs.pytest.org/)

**Hop & Barley** is a feature-rich Django-based e-commerce platform dedicated to homebrewing supplies (ingredients, hops, malts, yeast, and brewing kits). The project combines a modern HTML5/CSS3 Web Storefront, an Analytics-rich Custom Django Admin Dashboard, and a RESTful API powered by Django REST Framework & SimpleJWT with Swagger documentation.

---

## 📌 Features Overview

### 🛒 Web Storefront
- **Product Catalog & Search:** Paginated catalog (12 items per page), full-text keyword search, price range filtering, category filtering, and sorting (price ascending/descending, newest).
- **Product Detail & Reviews:** Detailed product page with stock availability, average star ratings, customer review submission with eligibility validation (only verified purchasers can leave reviews), and login redirection preserving `?next=`.
- **Session-Based Cart:** Add, remove, and adjust item quantities with real-time total price calculation and inventory stock validation.
- **Checkout & Orders:** Multi-field checkout form (`first_name`, `middle_name`, `last_name`, `email`, `phone`, `address`) with custom Ukrainian phone validation, mock payment method choice (*Credit/Debit Card*, *Cash on Delivery*), and atomic database transactions (`transaction.atomic()`).
- **User Accounts:** Custom `User` model using email authentication, user profile management, order history view, password change, and password reset via email workflow.

### ⚙️ Custom Admin Dashboard
- **Product & Category Admin:** Inline editing, stock level indicators, category filtering, and aggregated metrics (average ratings, total units sold).
- **Orders Admin:** Inline order items breakdown, total sales calculation, custom actions (`mark_as_paid`, `mark_as_shipped`, `mark_as_delivered`, `mark_as_cancelled`), and direct status inline dropdown editing.
- **User Admin:** Revenue generated per user, total order count, custom user detail fieldsets (`middle_name`, `phone`, `city`, `address`).

### 🌐 REST API & JWT Authentication
- **Full REST API Coverage:** Endpoints for Products, Categories, Reviews, Cart, User Registration, and Orders.
- **JWT Token Authentication:** Secure endpoint authentication using SimpleJWT (`POST /api/v1/token/` & `/api/v1/token/refresh/`).
- **Interactive API Documentation:** OpenAPI schema and interactive Swagger UI at `/api/docs/swagger/`.

---

## 🏗️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend Framework** | Django 6.0.6 |
| **Programming Language** | Python 3.14.3 |
| **REST API** | Django REST Framework (DRF) + `drf-nested-routers` |
| **API Security** | `djangorestframework-simplejwt` |
| **API Documentation** | `drf-spectacular` (OpenAPI 3.0 / Swagger UI) |
| **Database** | PostgreSQL 16 / SQLite (for local development) |
| **Testing** | Pytest + `pytest-django` (82 unit tests) |
| **Linters & Typing** | `ruff` (formatting & linting) + `mypy` (static type checking) |
| **Containerization** | Docker & Docker Compose |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) |

---

## 📁 Project Structure

```text
django_shop/
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions CI workflow
├── django_shop/
│   ├── apps/
│   │   ├── cart/               # Cart logic (session cart & REST API)
│   │   ├── orders/             # Order processing, services, & REST API
│   │   ├── products/           # Product catalog, categories, reviews & REST API
│   │   └── users/              # Custom User model, profile, authentication & REST API
│   ├── config/
│   │   ├── api_urls.py         # Consolidated REST API URL router
│   │   ├── settings.py         # Django settings configuration
│   │   ├── urls.py             # Global URL patterns
│   │   └── wsgi.py / asgi.py
│   ├── media/                  # User uploads & product images
│   ├── static/                 # Static CSS, JS, and UI assets
│   ├── pyproject.toml          # Ruff, Mypy, & Pytest configuration
│   └── manage.py
├── .env_example                # Template for environment variables
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Multi-container setup (Django + PostgreSQL)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) **OR** Python 3.14+ installed locally.

---

### Option A: Running with Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/django_shop.git
   cd django_shop
   ```

2. **Set up Environment Variables:**
   Copy `.env_example` to `.env`:
   ```bash
   cp .env_example .env
   ```

3. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Admin Dashboard:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
   - **Swagger API Docs:** [http://127.0.0.1:8000/api/docs/swagger/](http://127.0.0.1:8000/api/docs/swagger/)

5. **Create a Superuser (Optional):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

---

### Option B: Running Locally

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env_example .env
   ```

4. **Run migrations & start the development server:**
   ```bash
   cd django_shop
   python manage.py migrate
   python manage.py runserver
   ```

---

## 🔑 REST API Reference & JWT Workflow

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/users/register/` | Register new user & receive JWT tokens | No |
| `POST` | `/api/token/` | Obtain Access and Refresh JWT Tokens | No |
| `POST` | `/api/token/refresh/` | Refresh expired Access Token | No |

### Products & Reviews Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/products/` | List all active products | No |
| `GET` | `/api/v1/products/{id}/` | Retrieve product details | No |
| `GET` | `/api/v1/products/{id}/reviews/` | List product reviews | No |
| `POST` | `/api/v1/products/{id}/reviews/` | Submit a review (Verified buyers only) | Yes (JWT) |

### Cart & Orders Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/cart/` | View current cart items | Session/JWT |
| `POST` | `/api/v1/cart/` | Add/update item in cart | Session/JWT |
| `GET` | `/api/v1/orders/` | List user's past orders | Yes (JWT) |
| `POST` | `/api/v1/orders/` | Create order from cart | Optional (Guest / JWT) |
| `GET` | `/api/v1/orders/{id}/` | View specific order details | Yes (JWT) |

---

### Example HTTP Request with JWT Token

#### 1. Obtain Token Pair:
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"email": "buyer@example.com", "password": "Password123!"}'
```
**Response:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
}
```

#### 2. Access Protected Orders Endpoint:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/ \
     -H "Authorization: Bearer <your_access_token>"
```

---

## 🧪 Testing & Code Quality

### Running Unit Tests
All 82 unit tests cover models, views, services, forms, and API endpoints:
```bash
python -m pytest
```

### Static Analysis & Linting
Run Ruff for linting and code formatting:
```bash
ruff check .
```

Run Mypy for static type checking:
```bash
mypy .
```

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
