# 🍺 Hop & Barley — Homebrewing E-Commerce Store & REST API

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-6.0.6-green.svg)](https://www.djangoproject.com/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checker](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](http://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-96%20passed-success.svg)](https://docs.pytest.org/)
[![Package Manager](https://img.shields.io/badge/package%20manager-uv-blueviolet.svg)](https://docs.astral.sh/uv/)
[![Payments](https://img.shields.io/badge/payments-Stripe%20Checkout-635bff.svg)](https://docs.stripe.com/)

**Hop & Barley** is a feature-rich Django-based e-commerce platform dedicated to homebrewing supplies (ingredients, hops, malts, yeast, and brewing kits). The project combines a modern HTML5/CSS3 Web Storefront, **Stripe Checkout** online card payments (with webhook & session verification), an Analytics-rich Custom Django Admin Dashboard, and a RESTful API powered by Django REST Framework & SimpleJWT with Swagger documentation.

---

## 💳 Stripe Payment Integration

The storefront supports real online card payments via **Stripe Checkout (Hosted Page)** alongside **Cash on Delivery**:

- **Hosted Checkout Flow:** When a customer selects **Credit / Debit Card (Stripe)** at `/orders/create/`, the backend creates a `stripe.checkout.Session` (in `USD`, amounts calculated server-side in cents from DB prices), stores `stripe_session_id` on `Order`, reserves product stock atomically, and redirects the customer to Stripe's hosted payment page.
- **Hybrid Confirmation & Idempotency:** Payment confirmation works reliably both in production and locally:
  - **Webhook (`/orders/webhook/stripe/`):** Verifies the `Stripe-Signature` header via `STRIPE_WEBHOOK_SECRET` and processes `checkout.session.completed` (marking the order `PAID`) and `checkout.session.expired` (marking the order `CANCELLED` and restoring stock in a single atomic SQL update).
  - **Success URL Verification (`/orders/success/<order_id>/`):** Validates `session_id` directly against the Stripe API (`Session.retrieve`) so payments confirm immediately on redirect even in local development without running a webhook tunnel.
  - **Idempotent Transitions & Deferred Emails:** `mark_order_as_paid` uses `transaction.atomic()` + `select_for_update()` so duplicate redirects/webhooks never trigger duplicate updates or emails. Card order confirmation emails are deferred until payment succeeds (`CASH` orders send emails on creation).
- **Retry & Order Cancellation:** Returning from Stripe via `cancel_url` (`/orders/cancel/<order_id>/`) keeps the order `PENDING` with options to **Try Paying Again** (`/orders/pay/<order_id>/`) or **Cancel Order** (`/orders/cancel-order/<order_id>/`, which restores stock immediately and expires the open Stripe session).

### Stripe Environment & Local Webhook Testing

Add your test/live keys to `.env` (see [`.env_example`](.env_example)):
```env
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

To test webhooks locally with [Stripe CLI](https://docs.stripe.com/stripe-cli):
```powershell
stripe login
stripe listen --events checkout.session.completed,checkout.session.expired --forward-to http://127.0.0.1:8000/orders/webhook/stripe/
```
Copy the printed `whsec_...` signing secret into `.env` (`STRIPE_WEBHOOK_SECRET`) and restart your server/container (`docker compose restart web`).

---

## 📌 Features Overview

### 🛒 Web Storefront
- **Product Catalog & Search:** Paginated catalog (12 items per page), full-text keyword search, price range filtering, category filtering, and sorting (price ascending/descending, newest).
- **Product Detail & Reviews:** Detailed product page with stock availability, average star ratings, customer review submission with eligibility validation (only verified purchasers can leave reviews), and login redirection preserving `?next=`.
- **Session-Based Cart:** Add, remove, and adjust item quantities with real-time total price calculation and inventory stock validation.
- **Checkout & Orders:** Multi-field checkout form (`first_name`, `middle_name`, `last_name`, `email`, `phone`, `address`) prefilled for authenticated users, Ukrainian phone validation, payment method selection (*Credit / Debit Card (Stripe)*, *Cash on Delivery*), atomic stock reservation (`transaction.atomic()`), and retry/cancel support.
- **User Accounts:** Custom `User` model using email authentication, user profile management, order history view, password change, and password reset via email workflow.

### ⚙️ Custom Admin Dashboard
- **Product & Category Admin:** Inline editing, stock level indicators, category filtering, and aggregated metrics (average ratings, total units sold).
- **Orders Admin:** Inline order items breakdown, total sales calculation, filtering by status and payment method, search by `stripe_session_id`, custom actions (`mark_as_paid`, `mark_as_shipped`, `mark_as_delivered`, `mark_as_cancelled`), and direct status inline dropdown editing.
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
| **Programming Language** | Python 3.14 |
| **Payments** | Stripe Checkout (`stripe` Python SDK) |
| **REST API** | Django REST Framework (DRF) + `drf-nested-routers` |
| **API Security** | `djangorestframework-simplejwt` |
| **API Documentation** | `drf-spectacular` (OpenAPI 3.0 / Swagger UI) |
| **Database** | PostgreSQL 16 / SQLite (for local development) |
| **Package Manager** | `uv` (`pyproject.toml` & `uv.lock`) |
| **Testing** | Pytest + `pytest-django` (96 unit tests) |
| **Linters & Typing** | `ruff` (formatting & linting) + `mypy` (static type checking) |
| **Containerization** | Docker & Docker Compose (`uv` + Gunicorn `gthread`) |
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
│   └── manage.py
├── .env_example                # Template for environment variables
├── .dockerignore               # Docker ignore rules (prevents host .venv copying)
├── Dockerfile                  # Container build instructions (Astral uv + /opt/venv)
├── docker-compose.yml          # Multi-container setup (Django + PostgreSQL)
├── pyproject.toml              # Unified uv, dependencies, Ruff, Mypy & Pytest configuration
├── uv.lock                     # Locked dependencies for reproducible builds
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

### Option B: Running Locally with uv (Recommended)

1. **Install dependencies and sync environment:**
   ```bash
   uv sync
   ```

2. **Configure environment variables:**
   ```bash
   cp .env_example .env
   ```

3. **Run migrations & start the development server:**
   ```bash
   cd django_shop
   uv run python manage.py migrate
   uv run python manage.py populate_db   # (Optional) seed categories and sample products
   uv run python manage.py runserver
   ```

---

### Option C: Running Locally with pip

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

3. **Configure environment variables & run:**
   ```bash
   cp .env_example .env
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
All 96 unit tests cover models, views, services, Stripe integration, forms, and API endpoints:
```bash
uv run pytest
# or: python -m pytest
```

### Static Analysis & Linting
Run Ruff for linting and code formatting:
```bash
uv run ruff check .
```

Run Mypy for static type checking:
```bash
uv run mypy .
```

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
