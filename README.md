**# eCommSupport-AI**

An AI-powered e-commerce customer support system built around the Model Context Protocol (MCP).

The project separates transactional commerce operations from semantic policy retrieval into independent MCP servers. An OpenAI customer support agent uses these MCP servers to retrieve authoritative business facts and policy evidence before generating customer-facing responses.

**## Architecture**

\`\`\`text

                    ┌─────────────────────────┐

                    │ Customer Support Agent  │

                    │   OpenAI Agents SDK     │

                    └────────────┬────────────┘

                                 │

                  ┌──────────────┴──────────────┐

                  │                             │

                  ▼                             ▼

        ┌─────────────────┐           ┌─────────────────┐

        │  Commerce MCP   │           │   Policy MCP    │

        │                 │           │                 │

        │ Orders          │           │ Policy Search   │

        │ Products        │           │ Returns         │

        │ Shipments       │           │ Warranty Terms  │

        │ Warranties      │           │ Adaptive RAG    │

        └────────┬────────┘           └────────┬────────┘

                 │                             │

                 ▼                             ▼

        ┌─────────────────┐           ┌─────────────────┐

        │      MySQL      │           │    Pinecone     │

        └─────────────────┘           └─────────────────┘

\`\`\`

The responsibilities are intentionally separated:

\`\`\`text

Commerce MCP

→ authoritative customer and transactional facts

Policy MCP

→ authoritative policy evidence

Customer Support Agent

→ tool selection, reasoning, and customer-facing response

\`\`\`

**## Project Structure**

\`\`\`text

eCommSupport-AI/

│

├── commerce\_mcp/

│   ├── repositories/

│   │   ├── order\_repository.py

│   │   ├── product\_repository.py

│   │   └── warranty\_repository.py

│   │

│   ├── services/

│   │   ├── order\_service.py

│   │   ├── product\_service.py

│   │   └── warranty\_service.py

│   │

│   ├── tests/

│   │   └── integration/

│   │

│   ├── db.py

│   ├── server.py

│   └── test\_client.py

│

├── policy\_mcp/

│   ├── ingestion/

│   │   ├── extract\_pdf.py

│   │   └── ...

│   │

│   ├── retrieval/

│   │   ├── simple\_retriever.py

│   │   ├── hyde\_retriever.py

│   │   ├── multi\_query\_retriever.py

│   │   └── adaptive\_retriever.py

│   │

│   ├── rag/

│   │   └── simple\_rag.py

│   │

│   ├── services/

│   │   └── policy\_service.py

│   │

│   ├── tests/

│   ├── server.py

│   └── test\_client.py

│

├── customerSupportAgent/

│   ├── \_\_init\_\_.py

│   ├── prompt.py

│   └── main.py

│

├── .env

├── docker-compose.yml

└── README.md

\`\`\`

**## Commerce MCP**

The Commerce MCP provides structured access to transactional e-commerce data stored in MySQL.

**### Available Tools**

**#### \`search\_products\`**

Search the active product catalog using structured filters such as category, brand, price range, and stock availability.

**#### \`get\_product\_details\`**

Retrieve authoritative information for a specific product.

**#### \`list\_customer\_orders\`**

List recent orders belonging to a customer.

**#### \`check\_order\_status\`**

Retrieve order and shipment status using a customer ID and customer-facing order number.

**#### \`get\_order\_details\`**

Retrieve an order and its itemized contents using a customer ID and customer-facing order number. The tool resolves order items and product information, including product ID, SKU, product name, quantity, unit price, and line total.

**#### \`get\_warranty\_details\`**

Retrieve warranty ownership, plan, status, and validity information

for the product purchased in a customer's order.

The tool accepts:

\- \`customer\_id\`

\- \`order\_number\`

The Commerce MCP resolves the corresponding order item and product

internally. The customer or support agent does not need to know the

internal \`product\_id\`.

The tool returns factual warranty ownership information such as:

\- product

\- warranty plan

\- warranty status

\- validity period

\- purchase information

Detailed warranty coverage rules are policy knowledge and are retrieved

through the Policy MCP rather than stored as Commerce MCP logic.

**#### \`place\_order\`**

Place a single-product order after customer confirmation.

The operation includes:

\- customer validation

\- shipping-address ownership validation

\- product availability validation

\- database-authoritative pricing

\- stock validation

\- inventory locking

\- order creation

\- order-item creation

\- initial shipment creation

\- shipping-address snapshot

\- inventory decrement

\- idempotency protection

The entire operation executes inside a database transaction.

Order placement currently supports one product per order.

**## Order Identifiers**

Orders use separate internal and external identifiers.

\`\`\`text

order\_id

    Internal MySQL primary key.

order\_number

    Customer-facing generated order identifier.

idempotency\_key

    Identifies a specific order-placement request and prevents

    duplicate orders when a request is retried.

\`\`\`

The calling application is responsible for generating and reusing the idempotency key for retries.

**## Database**

Commerce data is stored in MySQL.

Major entities include:

\`\`\`text

customers

customer\_addresses

products

orders

order\_items

shipments

shipment\_items

shipment\_status\_history

warranty\_plans

customer\_warranties

\`\`\`

Historical shipping addresses are stored as snapshots on shipments rather than relying on the customer's current address.

**## Policy MCP**

The Policy MCP retrieves relevant company policy evidence for the Customer Support Agent.

It does **\*\*not\*\*** generate the final customer-facing answer.

Instead:

\`\`\`text

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

\`\`\`

This keeps policy retrieval separate from final reasoning and avoids unnecessary nested answer generation.

**### Policy Ingestion**

The current ingestion pipeline is:

\`\`\`text

Policy PDF

    ↓

PDF text extraction

    ↓

Text chunking

    ↓

Embedding generation

    ↓

Pinecone

\`\`\`

Policy chunk metadata currently includes:

\- country

\- policy version

\- source document

Section/category metadata is not assumed unless it can be reliably derived from the source document.

**### Retrieval Strategies**

Three retrieval strategies have been implemented.

**#### Simple Semantic Retrieval**

The original customer query is embedded directly.

\`\`\`text

Customer query

    ↓

Embedding

    ↓

Pinecone similarity search

    ↓

Top-K policy chunks

\`\`\`

**#### HyDE Retrieval**

HyDE generates a hypothetical answer/document representation before retrieval.

\`\`\`text

Customer query

    ↓

LLM generates hypothetical answer

    ↓

Embedding

    ↓

Pinecone similarity search

    ↓

Top-K real policy chunks

\`\`\`

The hypothetical content is used **\*\*only for retrieval\*\***. It is not treated as real company policy and is not returned as authoritative evidence.

**#### Multi-Query Retrieval**

The customer query is rewritten into multiple semantic variations.

\`\`\`text

Customer query

    ↓

Multiple query variations

    ↓

Multiple embedding searches

    ↓

Merge + deduplicate results

    ↓

Top-K policy chunks

\`\`\`

Multi-Query is intended to improve retrieval coverage when a single query representation is insufficient.

**### Adaptive Retrieval**

The Policy MCP currently combines the three strategies through adaptive retrieval.

\`\`\`text

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

\`\`\`

The current similarity-score thresholds are provisional engineering heuristics.

They should eventually be calibrated using a policy retrieval evaluation dataset rather than treated as permanent values.

The adaptive retriever avoids automatically running every retrieval strategy for every request, reducing unnecessary latency and model/embedding calls.

**### Policy MCP Output**

Policy MCP returns evidence such as:

\`\`\`text

chunk\_id

text

similarity score

source document

policy version

retrieval strategy

\`\`\`

The Customer Support Agent is responsible for interpreting this evidence.

**## Customer Support Agent**

The main customer-facing agent is implemented using the OpenAI Agents SDK with native MCP integration.

The agent connects to both MCP servers:

\`\`\`text

Commerce MCP → http\://localhost:8001/mcp

Policy MCP   → http\://localhost:8002/mcp

\`\`\`

The Agents SDK exposes the MCP tools directly to the model and handles the tool execution loop.

The agent does not directly access MySQL or Pinecone.

**### Agent Flow**

\`\`\`text

Customer

    ↓

Customer Support Agent

    ↓

Determine required tools

    │

    ├── Commerce MCP

    │      ↓

    │   transactional facts

    │

    └── Policy MCP

           ↓

        policy evidence

    ↓

Combine retrieved information

    ↓

Customer-facing response

\`\`\`

**### Example: Order Status**

\`\`\`text

Customer:

"Where is order ORD-2026-000001 for customer 1?"

Agent

    ↓

Commerce MCP

    ↓

Order + shipment information

    ↓

Customer-facing status

\`\`\`

**### Example: General Policy Question**

\`\`\`text

Customer:

"What is the standard return period?"

Agent

    ↓

Policy MCP

    ↓

Relevant return-policy evidence

    ↓

Customer-facing answer

\`\`\`

**### Example: Customer-Specific Return Question**

The intended multi-tool workflow is:

\`\`\`text

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

\`\`\`

The agent is instructed not to invent transactional or policy information and to verify customer-specific facts through Commerce MCP.

**### Multi-Turn Sessions and Compaction**

The terminal agent supports multi-turn conversations. A session is created once when the application starts and reused across successive `Runner.run(...)` calls, allowing follow-up questions to reuse customer, order, product, warranty, and prior tool-result context without requiring the customer to repeat it.

Session history is backed by `SQLiteSession` and wrapped with `OpenAIResponsesCompactionSession`. As a conversation grows, the SDK can compact older history into a smaller representation while retaining the context needed for later turns.

Development diagnostics currently expose:

- MCP tool start/end events through `RunHooks`
- MCP tool results
- input, output, and total token usage per run
- stored session-item count and item types
- compaction items, which can be inspected to verify that history compaction occurred

This setup provides short-term conversational memory while controlling the growth of long-running session context.

**### Grounding and Troubleshooting Boundary**

The agent must ground transactional facts in Commerce MCP and policy claims in Policy MCP evidence. Product-specific troubleshooting, diagnostic, reset, disassembly, or repair instructions should not be invented when approved support documentation has not been retrieved. Product support/troubleshooting documentation is therefore a future RAG corpus expansion.

**## Running the System**

The current development setup runs the two MCP servers and Customer Support Agent as separate processes.

**### 1. Start Commerce MCP**

\`\`\`powershell

python -m commerce\_mcp.server

\`\`\`

Commerce MCP currently uses Streamable HTTP on port \`8001\`.

**### 2. Start Policy MCP**

\`\`\`powershell

python -m policy\_mcp.server

\`\`\`

Policy MCP currently uses Streamable HTTP on port \`8002\`.

**### 3. Start Customer Support Agent**

\`\`\`powershell

python -m customerSupportAgent.main

\`\`\`

The agent connects to both MCP servers and accepts customer queries from the terminal.

**## Testing MCP Servers**

The MCP servers can also be tested independently.

Commerce MCP:

\`\`\`powershell

python -m commerce\_mcp.test\_client

\`\`\`

Policy MCP:

\`\`\`powershell

python -m policy\_mcp.test\_client

\`\`\`

These clients discover the available MCP tools and invoke them directly.

**## Running Tests**

Run all tests:

\`\`\`powershell

python -m pytest -v

\`\`\`

Run Commerce MCP integration tests:

\`\`\`powershell

python -m pytest commerce\_mcp/tests/integration -v

\`\`\`

Run Policy adaptive-retrieval tests:

\`\`\`powershell

python -m pytest policy\_mcp/tests/test\_adaptive\_retriever.py -v -s

\`\`\`

Run deterministic adaptive-routing tests:

\`\`\`powershell

python -m pytest policy\_mcp/tests/test\_adaptive\_routing.py -v

\`\`\`

Adaptive routing tests cover:

\`\`\`text

Strong Simple retrieval

→ Simple selected

Weak Simple + strong HyDE

→ HyDE selected

Weak Simple + weak HyDE

→ Multi-Query selected

\`\`\`

\> Note: some Commerce MCP order-placement integration tests create orders and modify inventory. A dedicated test database or automatic test cleanup should be added later.

**## Environment Variables**

Configuration and credentials are loaded from \`.env\`.

Example:

\`\`\`text

DB\_HOST=localhost

DB\_PORT=3306

DB\_NAME=ecomm\_support

DB\_USER=\<username>

DB\_PASSWORD=\<password>

OPENAI\_API\_KEY=\<key>

PINECONE\_API\_KEY=\<key>

PINECONE\_INDEX\_NAME=\<index>

COMMERCE\_MCP\_URL=http\://localhost:8001/mcp

POLICY\_MCP\_URL=http\://localhost:8002/mcp

LANGSMITH\_TRACING=true

LANGSMITH\_PROJECT=ecomm-support-ai

LANGSMITH\_API\_KEY=\<key>

\`\`\`

Do not commit \`.env\` or real credentials to source control.

**## Current Status**

**### Commerce MCP**

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

- [x] Itemized order details (`get_order_details`)

- [x] Warranty details

- [x] Transactional order placement

- [x] Idempotency protection

- [x] Unit and integration testing

**### Policy MCP**

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

**### Customer Support Agent**

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

- [x] Customer confirmation flow for order placement

- [ ] Idempotency-key generation

- [x] Multi-turn conversation/session handling

- [x] SQLite-backed session history

- [x] Responses-based session compaction

- [x] Tool invocation logging with `RunHooks`

- [x] Token/session diagnostics

- [ ] Docker deployment

**## Known Issues / Next Steps**

The next major development phase is evaluation: retrieval quality, tool selection, multi-turn context retention, grounded answer quality, and efficiency.


**### Retrieval Evaluation**

The current adaptive retrieval thresholds are provisional.

A future evaluation dataset should compare:

\- Simple retrieval

\- HyDE retrieval

\- Multi-Query retrieval

\- Recall\@K

\- expected-chunk ranking

\- latency

\- model/embedding cost

The evaluation results should determine the final adaptive-routing thresholds and strategy.

**### Additional Planned Work**

\- Expand end-to-end multi-tool agent tests

\- Add customer confirmation flow for write operations

\- Generate and manage idempotency keys outside Commerce MCP

\- Complete/verify LangSmith tracing integration

\- Build agent and retrieval evaluation framework

\- Ingest detailed warranty-plan documents

\- Add approved product troubleshooting/support documentation to the RAG corpus

\- Containerize MCP servers and support agent

\- Add dedicated test database / automatic cleanup

**## Development Philosophy**

MCP servers expose controlled business capabilities rather than arbitrary database access.

The language model does not generate SQL or directly modify commerce data. Business operations flow through explicit MCP tools, service-layer validation, repository logic, and transactional database operations.

Structured commerce facts belong in MySQL.

Semantic policy knowledge is retrieved through Pinecone and the Policy MCP.

The Customer Support Agent acts as the reasoning and orchestration layer:

\`\`\`text

Commerce facts

      +

Policy evidence

      ↓

Customer Support Agent

      ↓

Grounded customer response

\`\`\`

This separation keeps transactional operations deterministic while allowing the language model to reason over verified business facts and retrieved policy evidence.
