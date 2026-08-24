# eCommSupport-AI

An AI-powered e-commerce customer support system built around the Model Context Protocol (MCP).

The project separates transactional commerce operations from semantic policy retrieval into independent MCP servers. An OpenAI customer support agent uses these MCP servers to retrieve authoritative business facts and policy evidence before generating customer-facing responses.

## Architecture

```text
                    ┌─────────────────────────┐
                    │ Customer Support Agent  │
                    │   OpenAI Agents SDK     │
                    └────────────┬────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │                             │
                  ▼                             ▼
        ┌─────────────────┐           ┌─────────────────┐
        │  Commerce MCP   │           │   Policy MCP    │
        │                 │           │                 │
        │ Orders          │           │ Policy Search   │
        │ Products        │           │ Returns         │
        │ Shipments       │           │ Warranty Terms  │
        │ Warranties      │           │ Adaptive RAG    │
        └────────┬────────┘           └────────┬────────┘
                 │                             │
                 ▼                             ▼
        ┌─────────────────┐           ┌─────────────────┐
        │      MySQL      │           │    Pinecone     │
        └─────────────────┘           └─────────────────┘
```

The responsibilities are intentionally separated:

```text
Commerce MCP
→ authoritative customer and transactional facts

Policy MCP
→ authoritative policy evidence

Customer Support Agent
→ tool selection, reasoning, and customer-facing response
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
├── policy_mcp/
│   ├── ingestion/
│   │   ├── extract_pdf.py
│   │   └── ...
│   │
│   ├── retrieval/
│   │   ├── simple_retriever.py
│   │   ├── hyde_retriever.py
│   │   ├── multi_query_retriever.py
│   │   └── adaptive_retriever.py
│   │
│   ├── rag/
│   │   └── simple_rag.py
│   │
│   ├── services/
│   │   └── policy_service.py
│   │
│   ├── tests/
│   ├── server.py
│   └── test_client.py
│
├── customerSupportAgent/
│   ├── __init__.py
│   ├── prompt.py
│   └── main.py
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

Retrieve warranty ownership, plan, status, and validity information
for the product purchased in a customer's order.

The tool accepts:

- `customer_id`
- `order_number`

The Commerce MCP resolves the corresponding order item and product
internally. The customer or support agent does not need to know the
internal `product_id`.

The tool returns factual warranty ownership information such as:

- product
- warranty plan
- warranty status
- validity period
- purchase information

Detailed warranty coverage rules are policy knowledge and are retrieved
through the Policy MCP rather than stored as Commerce MCP logic.

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

Order placement currently supports one product per order.

## Order Identifiers

Orders use separate internal and external identifiers.

```text
order_id
    Internal MySQL primary key.

order_number
    Customer-facing generated order identifier.

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

## Policy MCP

The Policy MCP retrieves relevant company policy evidence for the Customer Support Agent.

It does **not** generate the final customer-facing answer.

Instead:

```text
Customer question
      ↓
Policy MCP
      ↓
Policy retrieval
      ↓
Relevant policy chunks + source metadata
      ↓
Customer Support Agent
      ↓
Final answer
```

This keeps policy retrieval separate from final reasoning and avoids unnecessary nested answer generation.

### Policy Ingestion

The current ingestion pipeline is:

```text
Policy PDF
    ↓
PDF text extraction
    ↓
Text chunking
    ↓
Embedding generation
    ↓
Pinecone
```

Policy chunk metadata currently includes:

- country
- policy version
- source document

Section/category metadata is not assumed unless it can be reliably derived from the source document.

### Retrieval Strategies

Three retrieval strategies have been implemented.

#### Simple Semantic Retrieval

The original customer query is embedded directly.

```text
Customer query
    ↓
Embedding
    ↓
Pinecone similarity search
    ↓
Top-K policy chunks
```

#### HyDE Retrieval

HyDE generates a hypothetical answer/document representation before retrieval.

```text
Customer query
    ↓
LLM generates hypothetical answer
    ↓
Embedding
    ↓
Pinecone similarity search
    ↓
Top-K real policy chunks
```

The hypothetical content is used **only for retrieval**. It is not treated as real company policy and is not returned as authoritative evidence.

#### Multi-Query Retrieval

The customer query is rewritten into multiple semantic variations.

```text
Customer query
    ↓
Multiple query variations
    ↓
Multiple embedding searches
    ↓
Merge + deduplicate results
    ↓
Top-K policy chunks
```

Multi-Query is intended to improve retrieval coverage when a single query representation is insufficient.

### Adaptive Retrieval

The Policy MCP currently combines the three strategies through adaptive retrieval.

```text
Simple Retrieval
      ↓
Strong enough?
 ├── Yes → return evidence
 └── No
       ↓
      HyDE
       ↓
Strong enough?
 ├── Yes → return evidence
 └── No
       ↓
   Multi-Query
       ↓
   return evidence
```

The current similarity-score thresholds are provisional engineering heuristics.

They should eventually be calibrated using a policy retrieval evaluation dataset rather than treated as permanent values.

The adaptive retriever avoids automatically running every retrieval strategy for every request, reducing unnecessary latency and model/embedding calls.

### Policy MCP Output

Policy MCP returns evidence such as:

```text
chunk_id
text
similarity score
source document
policy version
retrieval strategy
```

The Customer Support Agent is responsible for interpreting this evidence.

## Customer Support Agent

The main customer-facing agent is implemented using the OpenAI Agents SDK with native MCP integration.

The agent connects to both MCP servers:

```text
Commerce MCP → http://localhost:8001/mcp
Policy MCP   → http://localhost:8002/mcp
```

The Agents SDK exposes the MCP tools directly to the model and handles the tool execution loop.

The agent does not directly access MySQL or Pinecone.

### Agent Flow

```text
Customer
    ↓
Customer Support Agent
    ↓
Determine required tools
    │
    ├── Commerce MCP
    │      ↓
    │   transactional facts
    │
    └── Policy MCP
           ↓
        policy evidence
    ↓
Combine retrieved information
    ↓
Customer-facing response
```

### Example: Order Status

```text
Customer:
"Where is order ORD-2026-000001 for customer 1?"

Agent
    ↓
Commerce MCP
    ↓
Order + shipment information
    ↓
Customer-facing status
```

### Example: General Policy Question

```text
Customer:
"What is the standard return period?"

Agent
    ↓
Policy MCP
    ↓
Relevant return-policy evidence
    ↓
Customer-facing answer
```

### Example: Customer-Specific Return Question

The intended multi-tool workflow is:

```text
Customer
    ↓
Retrieve order/delivery facts
    ↓
Verify purchased warranty
    ↓
Retrieve relevant policy evidence
    ↓
Combine commerce facts + policy evidence
    ↓
Customer-facing answer
```

The agent is instructed not to invent transactional or policy information and to verify customer-specific facts through Commerce MCP.

## Running the System

The current development setup runs the two MCP servers and Customer Support Agent as separate processes.

### 1. Start Commerce MCP

```powershell
python -m commerce_mcp.server
```

Commerce MCP currently uses Streamable HTTP on port `8001`.

### 2. Start Policy MCP

```powershell
python -m policy_mcp.server
```

Policy MCP currently uses Streamable HTTP on port `8002`.

### 3. Start Customer Support Agent

```powershell
python -m customerSupportAgent.main
```

The agent connects to both MCP servers and accepts customer queries from the terminal.

## Testing MCP Servers

The MCP servers can also be tested independently.

Commerce MCP:

```powershell
python -m commerce_mcp.test_client
```

Policy MCP:

```powershell
python -m policy_mcp.test_client
```

These clients discover the available MCP tools and invoke them directly.

## Running Tests

Run all tests:

```powershell
python -m pytest -v
```

Run Commerce MCP integration tests:

```powershell
python -m pytest commerce_mcp/tests/integration -v
```

Run Policy adaptive-retrieval tests:

```powershell
python -m pytest policy_mcp/tests/test_adaptive_retriever.py -v -s
```

Run deterministic adaptive-routing tests:

```powershell
python -m pytest policy_mcp/tests/test_adaptive_routing.py -v
```

Adaptive routing tests cover:

```text
Strong Simple retrieval
→ Simple selected

Weak Simple + strong HyDE
→ HyDE selected

Weak Simple + weak HyDE
→ Multi-Query selected
```

> Note: some Commerce MCP order-placement integration tests create orders and modify inventory. A dedicated test database or automatic test cleanup should be added later.

## Environment Variables

Configuration and credentials are loaded from `.env`.

Example:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecomm_support
DB_USER=<username>
DB_PASSWORD=<password>

OPENAI_API_KEY=<key>
PINECONE_API_KEY=<key>
PINECONE_INDEX_NAME=<index>

COMMERCE_MCP_URL=http://localhost:8001/mcp
POLICY_MCP_URL=http://localhost:8002/mcp
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

- [x] Policy PDF
- [x] PDF text extraction
- [x] Policy chunking
- [x] Embeddings
- [x] Pinecone integration
- [x] Simple semantic retrieval
- [x] HyDE retrieval
- [x] Multi-Query retrieval
- [x] Adaptive retrieval
- [x] Policy evidence service
- [x] MCP Streamable HTTP server
- [x] Policy search tool
- [x] Integration testing
- [x] Deterministic adaptive-routing tests

### Customer Support Agent

- [x] OpenAI Agents SDK integration
- [x] Native MCP integration
- [x] Commerce MCP integration
- [x] Policy MCP integration
- [x] Autonomous tool selection
- [x] Commerce-only query handling
- [x] Policy-only query handling
- [x] Multi-tool query handling
- [x] Order-based warranty lookup
- [x] Warranty verification from customer ID + order number
- [ ] Detailed warranty-policy document ingestion
- [ ] Retrieval evaluation framework
- [ ] Customer confirmation flow for order placement
- [ ] Idempotency-key generation
- [ ] Conversation/session handling
- [ ] Docker deployment

## Known Issues / Next Steps

### Order-to-Warranty Lookup

Current agent testing exposed an API-contract issue for customer-specific return and warranty questions.

For example:

```text
"I am customer 1. Can I return the laptop from
order ORD-2026-000001? It is damaged."
```

The agent can retrieve the order and relevant policy evidence, but the current Commerce MCP tool contract may not provide enough information for the agent to resolve the purchased warranty directly from the known order.

The customer should not be required to provide an internal `product_id` when the order is already known.

This flow needs to be improved:

```text
customer_id + order_number
        ↓
order
        ↓
order item
        ↓
product
        ↓
purchased warranty
```

A Commerce MCP capability or existing tool contract will be updated to support this lookup cleanly.

### Retrieval Evaluation

The current adaptive retrieval thresholds are provisional.

A future evaluation dataset should compare:

- Simple retrieval
- HyDE retrieval
- Multi-Query retrieval
- Recall@K
- expected-chunk ranking
- latency
- model/embedding cost

The evaluation results should determine the final adaptive-routing thresholds and strategy.

### Additional Planned Work

- Fix order-to-warranty resolution
- Expand end-to-end multi-tool agent tests
- Add customer confirmation flow for write operations
- Generate and manage idempotency keys outside Commerce MCP
- Add conversation/session handling
- Add observability and tracing
- Containerize MCP servers and support agent
- Add dedicated test database / automatic cleanup

## Development Philosophy

MCP servers expose controlled business capabilities rather than arbitrary database access.

The language model does not generate SQL or directly modify commerce data. Business operations flow through explicit MCP tools, service-layer validation, repository logic, and transactional database operations.

Structured commerce facts belong in MySQL.

Semantic policy knowledge is retrieved through Pinecone and the Policy MCP.

The Customer Support Agent acts as the reasoning and orchestration layer:

```text
Commerce facts
      +
Policy evidence
      ↓
Customer Support Agent
      ↓
Grounded customer response
```

This separation keeps transactional operations deterministic while allowing the language model to reason over verified business facts and retrieved policy evidence.