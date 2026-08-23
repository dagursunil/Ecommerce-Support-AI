# eCommSupport-AI

An AI-powered e-commerce customer support system built around the Model Context Protocol (MCP).

The project separates transactional commerce operations from knowledge/policy retrieval into independent MCP servers. An AI support agent will use these MCP servers to answer customer questions and perform approved commerce operations.

## Architecture

```text
                    ┌─────────────────────┐
                    │   Support Agent     │
                    │      / Client       │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │  Commerce MCP   │         │   Policy MCP    │
        │                 │         │                 │
        │ Orders          │         │ Policies        │
        │ Products        │         │ Warranty Terms  │
        │ Shipments       │         │ Returns         │
        │ Warranties      │         │ RAG             │
        └────────┬────────┘         └────────┬────────┘
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │      MySQL      │         │    Pinecone     │
        └─────────────────┘         └─────────────────┘
```

## Project Structure

```text
eCommSupport-AI/
│
├── commerce_mcp/
│   ├── repositories/
│   │   ├── order_repository.py
│   │   ├── product_repository.py
│   │   └── warranty_repository.py
│   │
│   ├── services/
│   │   ├── order_service.py
│   │   ├── product_service.py
│   │   └── warranty_service.py
│   │
│   ├── tests/
│   │   └── integration/
│   │
│   ├── db.py
│   ├── server.py
│   └── test_client.py
│
├── policy_mcp/             # Planned
│
├── .env
├── docker-compose.yml
└── README.md
```

## Commerce MCP

The Commerce MCP provides structured access to transactional e-commerce data stored in MySQL.

### Available Tools

#### `search_products`

Search the active product catalog using structured filters such as category, brand, price range, and stock availability.

#### `get_product_details`

Retrieve authoritative information for a specific product.

#### `list_customer_orders`

List recent orders belonging to a customer.

#### `check_order_status`

Retrieve order and shipment status using a customer ID and customer-facing order number.

#### `get_warranty_details`

Retrieve warranty ownership, plan, status, and validity information for a product purchased by a customer.

Warranty coverage rules themselves will be handled by the Policy MCP.

#### `place_order`

Place a single-product order after customer confirmation.

The operation includes:

- customer validation
- shipping-address ownership validation
- product availability validation
- database-authoritative pricing
- stock validation
- inventory locking
- order creation
- order-item creation
- initial shipment creation
- shipping-address snapshot
- inventory decrement
- idempotency protection

The entire operation executes inside a database transaction.

## Order Identifiers

Orders use separate internal and external identifiers.

```text
order_id
    Internal MySQL primary key.

order_number
    Customer-facing random order identifier.

idempotency_key
    Identifies a specific order-placement request and prevents
    duplicate orders when a request is retried.
```

The calling application is responsible for generating and reusing the idempotency key for retries.

## Database

Commerce data is stored in MySQL.

Major entities include:

```text
customers
customer_addresses
products
orders
order_items
shipments
shipment_items
shipment_status_history
warranty_plans
customer_warranties
```

Historical shipping addresses are stored as snapshots on shipments rather than relying on the customer's current address.

## Running Commerce MCP

Activate the Python virtual environment and start the MCP server from the project root:

```powershell
python -m commerce_mcp.server
```

The Commerce MCP server currently uses Streamable HTTP on port `8001`.

## Testing the MCP Server

With the Commerce MCP server running, open another terminal and run:

```powershell
python -m commerce_mcp.test_client
```

This client can discover the available MCP tools and invoke them directly.

## Running Tests

Run all tests:

```powershell
python -m pytest -v
```

Run Commerce MCP integration tests:

```powershell
python -m pytest commerce_mcp/tests/integration -v
```

The integration tests use the real MySQL development database.

> Note: some order-placement integration tests create orders and modify inventory. A dedicated test database or automatic test cleanup should be added later.

## Environment Variables

Database credentials are loaded from `.env`.

Example:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecomm_support
DB_USER=<username>
DB_PASSWORD=<password>
```

Do not commit `.env` or real credentials to source control.

## Current Status

### Commerce MCP

- [x] MySQL schema
- [x] SQLAlchemy connection pooling
- [x] Product repository/service
- [x] Order repository/service
- [x] Warranty repository/service
- [x] MCP Streamable HTTP server
- [x] Product search
- [x] Product details
- [x] Customer order listing
- [x] Order/shipment status
- [x] Warranty details
- [x] Transactional order placement
- [x] Idempotency protection
- [x] Unit and integration testing

### Policy MCP

- [ ] Policy document ingestion
- [ ] Embeddings
- [ ] Pinecone integration
- [ ] Policy retrieval
- [ ] Warranty coverage retrieval
- [ ] Return/refund policy retrieval
- [ ] MCP tools

### Support Agent

- [ ] Agent orchestration
- [ ] Commerce MCP integration
- [ ] Policy MCP integration
- [ ] Customer confirmation flow
- [ ] Idempotency-key generation
- [ ] Docker deployment

## Development Philosophy

MCP servers expose controlled business capabilities rather than arbitrary database access.

The language model does not generate SQL or directly modify commerce data. Business operations flow through explicit MCP tools, service-layer validation, repository logic, and transactional database operations.

Structured commerce facts belong in MySQL. Semantic policy and support knowledge will be retrieved through the Policy MCP and vector search.