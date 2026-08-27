# eCommSupport-AI

An AI-powered e-commerce customer support system built around the

**Model Context Protocol (MCP)**.

The project separates transactional commerce operations from semantic

policy retrieval into independent MCP servers. A customer support agent

built with the **OpenAI Agents SDK** uses these servers to retrieve

authoritative business facts and policy evidence before generating

customer-facing responses.

## Architecture

```text
Client / UI
    |
    v
FastAPI Customer Support API
    |
    | session_id
    v
Customer Support Agent
OpenAI Agents SDK
    |
    +------------------------+
    |                        |
    v                        v
Commerce MCP             Policy MCP
    |                        |
    v                        v
MySQL                    Pinecone
```

Responsibilities are intentionally separated:

- **FastAPI API** — exposes session-based HTTP endpoints for external clients.
- **Commerce MCP** — authoritative customer and transactional facts and controlled commerce operations.
- **Policy MCP** — authoritative policy evidence.
- **Customer Support Agent** — tool selection, reasoning, multi-turn context, and customer-facing responses.

The agent does not directly access MySQL or Pinecone. External clients interact with the FastAPI layer rather than calling MCP servers directly.

## Project Structure

```text
eCommSupport-AI/
|
├── commerce_mcp/
│   ├── repositories/
│   ├── services/
│   ├── tests/
│   ├── db.py
│   ├── server.py
│   └── test_client.py
|
├── policy_mcp/
│   ├── ingestion/
│   ├── retrieval/
│   ├── rag/
│   ├── services/
│   ├── tests/
│   ├── server.py
│   └── test_client.py
|
├── customerSupportAgent/
│   ├── __init__.py
│   ├── api.py
│   ├── context.py
│   ├── main.py
│   ├── prompt.py
│   └── service.py
|
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Commerce MCP

The Commerce MCP provides structured access to transactional e-commerce

data stored in MySQL.

### Available Tools

#### `search_products`

Search the active product catalog using structured filters such as

category, brand, price range, and stock availability.

#### `get_product_details`

Retrieve authoritative information for a specific product.

#### `list_customer_orders`

List recent orders belonging to a customer.

#### `check_order_status`

Retrieve order and shipment status using a customer ID and

customer-facing order number.

#### `get_order_details`

Retrieve an order and its itemized contents using a customer ID and

customer-facing order number.

The tool resolves order items and product information, including:

-   product ID

-   SKU

-   product name

-   quantity

-   unit price

-   line total

#### `get_warranty_details`

Retrieve purchased warranty information for a product in a customer's

order.

The tool uses the customer ID and order number to resolve the

corresponding order item and product internally. The customer does not

need to know the internal product ID.

It returns factual warranty information such as:

-   product

-   warranty plan

-   warranty status

-   validity period

-   warranty purchase price

Warranty coverage rules are policy knowledge and are retrieved through

Policy MCP rather than implemented as Commerce MCP business logic.

#### `list_customer_addresses`

List saved shipping addresses belonging to a customer.

This is used during checkout so the customer can select a saved address

without knowing an internal `address_id`. The current agent does not

create or modify customer addresses.

#### `place_order`

Place a single-product order after explicit customer confirmation.

The operation includes:

-   customer validation

-   shipping-address ownership validation

-   product availability validation

-   database-authoritative pricing

-   stock validation

-   inventory locking

-   order creation

-   order-item creation

-   initial shipment creation

-   shipping-address snapshot

-   inventory decrement

-   idempotency protection

The entire operation executes inside a database transaction.

Order placement currently supports one product per order.

## Order Identifiers

Orders use separate internal and external identifiers:

``` text

order_id

    Internal MySQL primary key.

order_number

    Customer-facing generated order identifier.

idempotency_key

    Identifies an order-placement request and prevents duplicate

    orders when the same request is retried.

```

The Commerce MCP enforces idempotency, while the calling application owns the idempotency-key lifecycle.

For `place_order`, the agent service uses an MCP tool metadata resolver to create a `PendingCheckout` when a checkout operation begins. The generated idempotency key is attached to the tool call and reused for retries of that same pending checkout. After a confirmed `ORDER_PLACED` result, the pending checkout is cleared so a later intentional purchase receives a new key.

## Database

Commerce data is stored in MySQL.

Major entities include:

``` text

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

Historical shipping addresses are stored as shipment snapshots rather

than relying on the customer's current saved address.

## Policy MCP

The Policy MCP retrieves relevant company policy evidence for the

Customer Support Agent. It does **not** generate the final

customer-facing answer.

``` text

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

This keeps retrieval separate from final reasoning and prevents

retrieved or generated intermediate text from being treated as the final

policy answer.

### Policy Ingestion

The current ingestion pipeline is:

``` text

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

-   country

-   policy version

-   source document

### Retrieval Strategies

The Policy MCP supports three retrieval strategies.

#### Simple Semantic Retrieval

``` text

Customer query

    ↓

Embedding

    ↓

Pinecone similarity search

    ↓

Top-K policy chunks

```

#### HyDE Retrieval

HyDE generates a hypothetical answer/document representation before

retrieval.

``` text

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

The hypothetical content is used **only for retrieval** and is never

treated as authoritative company policy.

#### Multi-Query Retrieval

``` text

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

### Adaptive Retrieval

The Policy MCP combines these strategies through adaptive routing:

``` text

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

The current similarity-score thresholds are provisional engineering

heuristics. They should be calibrated through retrieval evaluations

rather than treated as permanent values.

### Policy MCP Output

Policy MCP returns evidence including:

``` text

chunk_id

text

similarity score

source document

policy version

retrieval strategy

```

The Customer Support Agent is responsible for interpreting the retrieved

evidence.

## Customer Support Agent

The customer-facing agent is implemented with the **OpenAI Agents SDK**

and native MCP integration.

It connects to:

``` text

Commerce MCP → http\://localhost:8001/mcp

Policy MCP   → http\://localhost:8002/mcp

```

The agent does not directly access MySQL or Pinecone.

### Agent Responsibilities

The agent can:

-   select Commerce and Policy MCP tools autonomously

-   answer commerce-only questions

-   answer policy-only questions

-   combine Commerce facts with Policy evidence

-   maintain context across multiple conversation turns

-   reuse previously retrieved tool results when appropriate

-   require explicit customer confirmation before order placement

-   resolve saved shipping addresses without exposing internal address

    IDs

### Example Multi-Turn Flow

``` text

Customer:

"Where is order ORD-2026-000001?"

→ check_order_status

Customer:

"What is included in the order?"

→ get_order_details

Customer:

"Do I have a warranty on it?"

→ get_warranty_details

Customer:

"How much did I pay for the warranty?"

→ answer from existing session context

```

### Customer-Specific Return / Warranty Flow

``` text

Customer question

      ↓

Retrieve order/delivery facts

      ↓

Verify purchased warranty

      ↓

Retrieve applicable policy evidence

      ↓

Combine Commerce facts + Policy evidence

      ↓

Grounded customer-facing answer

```

The agent is instructed not to invent transactional or policy facts.

### Order Placement Flow

The current checkout flow is:

``` text

Customer purchase intent

      ↓

Product lookup / validation

      ↓

Quantity selection

      ↓

Retrieve saved customer addresses

      ↓

Customer selects saved address

      ↓

Explicit final confirmation

      ↓

place_order

```

Customers are not asked for internal product or address IDs.

New shipping addresses are intentionally outside the current agent

scope. Orders can only be placed using existing saved customer

addresses.

### Multi-Turn Sessions and Compaction

The terminal agent supports multi-turn conversations.

A session is created once when the application starts and reused across

successive `Runner.run(...)` calls. This allows follow-up questions to

reuse customer, order, product, warranty, and previous tool-result

context without requiring the customer to repeat it.

Session history is backed by `SQLiteSession` and wrapped with

`OpenAIResponsesCompactionSession`.

As the conversation grows, older history can be compacted into a smaller

representation while preserving useful context for later turns.

Development diagnostics expose:

-   MCP tool start/end events through `RunHooks`

-   MCP tool results

-   input, output, and total token usage per run

-   stored session-item count

-   session item types

-   compaction items

### API Sessions and Runtime State

The FastAPI layer exposes a session-based interface for clients.

```text
POST /sessions
    -> creates a server-side session
    -> returns session_id

POST /sessions/{session_id}/messages
    -> sends one customer turn
    -> reuses the same conversation session and SupportContext
```

A client sends one message at a time and keeps the returned `session_id` for subsequent turns.

Two kinds of state are intentionally separated:

```text
Conversation memory
    -> SQLiteSession
    -> OpenAIResponsesCompactionSession

Runtime application context
    -> SupportContext
        -> customer_id
        -> pending_checkout
            -> idempotency_key
```

`SupportContext` is not general long-term memory. It carries authenticated customer context and temporary checkout state required during agent execution. `pending_checkout` allows retries of the same order-placement operation to reuse the same idempotency key.

The current FastAPI implementation keeps active `SupportContext` objects in process memory. This is suitable for the current single-process project scope; a multi-worker production deployment would require shared persistent session/application state.

### Grounding and Troubleshooting Boundary

Transactional facts must come from Commerce MCP and policy claims must

be grounded in Policy MCP evidence.

The agent should not invent product-specific diagnostic, reset,

disassembly, repair, or troubleshooting procedures when approved support

documentation has not been retrieved.

Product support/troubleshooting documentation can be added to the RAG

corpus later if that capability is required.

## Running the System

The project supports both local development and a containerized deployment.

### Docker Compose

Start the complete stack from the project root:

```powershell
docker compose up -d
```

The Compose stack runs:

```text
mysql          -> 3306
commerce-mcp   -> 8001
policy-mcp     -> 8002
agent-api      -> 8080
```

Inside Docker, the agent uses Compose service names:

```text
COMMERCE_MCP_URL=http://commerce-mcp:8001/mcp
POLICY_MCP_URL=http://policy-mcp:8002/mcp
```

Check status:

```powershell
docker compose ps
```

Verify the API:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8080/health"
```

Create a customer session:

```powershell
$session = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/sessions" `
  -ContentType "application/json" `
  -Body '{"customer_id":1}'
```

Send a message:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/sessions/$($session.session_id)/messages" `
  -ContentType "application/json" `
  -Body '{"message":"Where is order ORD-2026-000001?"}'
```

Successive customer turns use the same `session_id`.

### Local Development

Start Commerce MCP:

```powershell
python -m commerce_mcp.server
```

Start Policy MCP:

```powershell
python -m policy_mcp.server
```

Start the API:

```powershell
uvicorn customerSupportAgent.api:app --reload --port 8080
```

The original terminal client remains available:

```powershell
python -m customerSupportAgent.main
```

## Testing MCP Servers

Commerce MCP:

``` powershell

python -m commerce_mcp.test_client

```

Policy MCP:

``` powershell

python -m policy_mcp.test_client

```

## Running Tests

Run all tests:

``` powershell

python -m pytest -v

```

Run Commerce MCP integration tests:

``` powershell

python -m pytest commerce_mcp/tests/integration -v

```

Run Policy adaptive-retrieval tests:

``` powershell

python -m pytest policy_mcp/tests/test_adaptive_retriever.py -v -s

```

Run deterministic adaptive-routing tests:

``` powershell

python -m pytest policy_mcp/tests/test_adaptive_routing.py -v

```

Adaptive routing tests cover:

``` text

Strong Simple retrieval

→ Simple selected

Weak Simple + strong HyDE

→ HyDE selected

Weak Simple + weak HyDE

→ Multi-Query selected

```

> **Note:** Some Commerce MCP order-placement integration tests create

> orders and modify inventory. A dedicated test database or automatic

> test cleanup should be added later.

## Environment Variables

Configuration and credentials are loaded from `.env`.

Example:

``` text

DB_HOST=localhost

DB_PORT=3306

DB_NAME=ecomm_support

DB_USER=\<username>

DB_PASSWORD=\<password>

OPENAI_API_KEY=\<key>

PINECONE_API_KEY=\<key>

PINECONE_INDEX_NAME=\<index>

COMMERCE_MCP_URL=http\://localhost:8001/mcp

POLICY_MCP_URL=http\://localhost:8002/mcp

LANGSMITH_TRACING=true

LANGSMITH_PROJECT=ecomm-support-ai

LANGSMITH_API_KEY=\<key>

```

Do not commit `.env` or real credentials to source control.

## Evaluation

The project includes agent-level evaluations covering representative customer-support scenarios:

- order status
- itemized order details
- warranty lookup
- policy-only questions
- purchase confirmation behavior
- damaged-item return/warranty reasoning

The evaluation framework checks tool selection and unnecessary tool calls. Selected cases also use an LLM judge for groundedness, correctness, completeness, and unsupported claims.

The final regression run completed with all evaluation cases passing after the application-managed idempotency and API/service refactoring.

Policy MCP also includes deterministic adaptive-routing tests for Simple, HyDE, and Multi-Query retrieval paths.

## Current Status

### Commerce MCP

- [x] MySQL schema and SQLAlchemy connection pooling
- [x] Product, order, address, shipment, and warranty capabilities
- [x] MCP Streamable HTTP server
- [x] Itemized order details and order/shipment status
- [x] Transactional single-product order placement
- [x] Saved-address checkout
- [x] Database transaction and inventory locking
- [x] Idempotency enforcement
- [x] Unit and integration testing

### Policy MCP

- [x] Policy PDF ingestion and chunking
- [x] Embeddings and Pinecone integration
- [x] Simple semantic retrieval
- [x] HyDE retrieval
- [x] Multi-Query retrieval
- [x] Adaptive retrieval
- [x] Policy evidence service
- [x] MCP Streamable HTTP server
- [x] Integration and deterministic routing tests

### Customer Support Agent and API

- [x] OpenAI Agents SDK integration
- [x] Native Commerce and Policy MCP integration
- [x] Autonomous and multi-tool selection
- [x] Grounded Commerce + Policy responses
- [x] Multi-turn conversation handling
- [x] SQLite-backed session history
- [x] Responses-based session compaction
- [x] Explicit checkout confirmation
- [x] Application-managed idempotency-key lifecycle
- [x] Runtime checkout state through `SupportContext`
- [x] FastAPI session and message endpoints
- [x] LangSmith tracing integration
- [x] Agent evaluation framework and regression evaluation
- [x] Docker Compose deployment

## Scope and Production Considerations

The implementation is complete for the current project scope.

The following are intentionally left as production hardening rather than project requirements:

- persistent/distributed API session and `SupportContext` storage for multiple workers
- authentication/authorization in front of the customer API
- production secret management
- dedicated test database or automatic cleanup for mutating integration tests
- CI/CD and deployment orchestration beyond Docker Compose
- long-term cross-session customer personalization/memory
- approved product troubleshooting/support documentation if that capability is added

## Development Philosophy

MCP servers expose controlled business capabilities rather than

arbitrary database access.

The language model does not generate SQL or directly modify commerce

data. Business operations flow through explicit MCP tools, service-layer

validation, repository logic, and transactional database operations.

Structured commerce facts belong in MySQL. Semantic policy knowledge is

retrieved through Pinecone and Policy MCP.

``` text

Commerce facts

      +

Policy evidence

      ↓

Customer Support Agent

      ↓

Grounded customer response

```

This separation keeps transactional operations deterministic while

allowing the language model to reason over verified business facts and

retrieved policy evidence.
