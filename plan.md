# Plan: Beaver's Choice Paper Company Multi-Agent System

## Context

Build a multi-agent system (max 5 agents) for a paper supply company. The requirements prescribe 6 sequential steps that we must follow in order.

---

## Requirements & Success Criteria Checklist

Every item below must be satisfied before submission. References are to `requirements.md` rubric sections.

### A. Agent Workflow Diagram
- [ ] A1. Diagram includes ALL agents (max 5)
- [ ] A2. Each agent has explicitly defined, non-overlapping responsibilities
- [ ] A3. Orchestration logic and data flow between agents is clear
- [ ] A4. Tools are depicted and associated with specific agents
- [ ] A5. Each tool's purpose AND the specific helper function(s) it uses are specified in the diagram
- [ ] A6. Diagram shows data input/output interactions between agents and tools

### B. Multi-Agent System Implementation
- [ ] B1. Architecture matches the submitted workflow diagram
- [ ] B2. Orchestrator agent manages task delegation
- [ ] B3. Distinct worker agent for **inventory management** (checking stock, reorder needs)
- [ ] B4. Distinct worker agent for **quoting** (generating prices, considering discounts)
- [ ] B5. Distinct worker agent for **sales finalization** (processing orders, updating DB)
- [ ] B6. Uses one of: smolagents, pydantic-ai, or npcsh
- [ ] B7. Tools defined per framework conventions (`@tool` decorator for smolagents)
- [ ] B8. `create_transaction` used in at least one tool
- [ ] B9. `get_all_inventory` used in at least one tool
- [ ] B10. `get_stock_level` used in at least one tool
- [ ] B11. `get_supplier_delivery_date` used in at least one tool
- [ ] B12. `get_cash_balance` used in at least one tool
- [ ] B13. `generate_financial_report` used in at least one tool
- [ ] B14. `search_quote_history` used in at least one tool

### C. Evaluation and Reflection
- [ ] C1. System evaluated using FULL `quote_requests_sample.csv` (all 20 requests)
- [ ] C2. Results submitted in `test_results.csv`
- [ ] C3. At least 3 requests result in cash balance change
- [ ] C4. At least 3 quote requests successfully fulfilled
- [ ] C5. NOT all requests fulfilled (reasons provided/implied for unfulfilled)
- [ ] C6. Reflection report explains the workflow diagram and agent roles
- [ ] C7. Reflection report discusses evaluation results, identifying strengths
- [ ] C8. Reflection report includes at least 2 distinct improvement suggestions

### D. Industry Best Practices
- [ ] D1. Customer-facing outputs contain all info relevant to the request
- [ ] D2. Outputs include rationale for pricing decisions (discounts, unfulfilled reasons)
- [ ] D3. No sensitive internal data exposed (profit margins, error messages, PII)
- [ ] D4. Descriptive variable/function names, consistent snake_case convention
- [ ] D5. Comments and docstrings at appropriate places
- [ ] D6. Logic broken into modular components

### E. Submission Deliverables
- [ ] E1. Workflow diagram (image file)
- [ ] E2. Single Python source file
- [ ] E3. Detailed documentation/reflection report
- [ ] E4. `test_results.csv`

---

## Step 1: Draft Agent Workflow Diagram

**Goal**: Create a visual workflow diagram showing agents, tools, data flow, and orchestration logic.
**Satisfies**: A1-A6, E1

### Architecture (4 agents)

**Orchestrator Agent** (manager)
- Receives customer requests, parses intent
- Delegates to specialist agents
- Composes final customer-facing response
- No direct tools - delegates everything

**Inventory Agent** (worker)
- Tools: `check_inventory` (uses `get_all_inventory`), `check_item_stock` (uses `get_stock_level`), `check_delivery_date` (uses `get_supplier_delivery_date`), `reorder_stock` (uses `create_transaction` + `get_cash_balance`)
- Responsibilities: stock availability checks, reorder decisions, delivery estimates

**Quoting Agent** (worker)
- Tools: `search_quotes` (uses `search_quote_history`), `calculate_quote` (uses `paper_supplies` price catalog)
- Responsibilities: historical quote lookup, price calculation with bulk discounts

**Sales Agent** (worker)
- Tools: `finalize_sale` (uses `create_transaction` + `get_stock_level`), `check_cash_balance` (uses `get_cash_balance`), `get_financial_report` (uses `generate_financial_report`)
- Responsibilities: finalize transactions, verify cash, generate reports

### Diagram deliverable
- Create using **matplotlib** (programmatic, no external tools needed)
- Shows: agents as boxes, tools as rounded boxes, arrows for data flow, helper function labels on each tool
- Save as `workflow_diagram.png`

---

## Step 2: Review Starter Code

**Goal**: Add review comments directly into `project_starter.py` for each helper function.
**Satisfies**: D5 (comments at appropriate places)

Requirements.md says: *"Spend at least 30 minutes reviewing the starter file. Write brief descriptions for each function provided to ensure you thoroughly understand their purpose and usage within your system."*

Add a **review comment block** above each function in the code:

```python
# === REVIEW: generate_sample_inventory ===
# Purpose: Creates a reproducible random subset (40%) of the paper_supplies catalog.
# Assigns each selected item a random stock quantity (200-800) and min reorder level (50-150).
# Used by: init_database() to seed the initial inventory table.
# Returns: DataFrame with columns: item_name, category, unit_price, current_stock, min_stock_level
# Agent usage: Not directly used as a tool - called during DB initialization only.
```

Functions to review and annotate:
1. `generate_sample_inventory()` (line 74) - Seeds inventory; not an agent tool
2. `init_database()` (line 129) - Creates all DB tables and initial state; called once at startup
3. `create_transaction()` (line 242) - Records stock_orders/sales; **used by Inventory + Sales agents**
4. `get_all_inventory()` (line 295) - Full stock snapshot as of date; **used by Inventory agent**
5. `get_stock_level()` (line 332) - Single item stock; **used by Inventory + Sales agents**
6. `get_supplier_delivery_date()` (line 371) - Delivery estimate by qty tier; **used by Inventory agent**
7. `get_cash_balance()` (line 415) - Net cash balance; **used by Inventory + Sales agents**
8. `generate_financial_report()` (line 453) - Full financial report; **used by Sales agent**
9. `search_quote_history()` (line 524) - Keyword search on historical quotes; **used by Quoting agent**

**Known bug**: Line 616 calls `init_database()` without required `db_engine` parameter - will fix in Step 4.

**Key insight**: Only ~18 of 46 items are stocked (seed=137). Many test requests ask for unstocked items, naturally producing partial/rejected orders (satisfies C5).

---

## Step 3: Select Agent Framework

**Choice**: **smolagents** with **gpt-4o-mini** (confirmed by user)
**Satisfies**: B6

- Minimal boilerplate, fits single-file constraint
- `@tool` decorator for wrapping helper functions
- `ManagedAgent` for built-in multi-agent orchestration
- `OpenAIServerModel` works with existing `OPENAI_API_KEY`
- Install: `pip install 'smolagents[openai]'`

---

## Step 4: Implement the System

**Goal**: Code agents and tools in `project_starter.py` at the marked placeholder sections.
**Satisfies**: B1-B14, D4, D5, D6, E2

### 4a. Add imports and model setup
- smolagents imports + `dotenv.load_dotenv()` + model initialization

### 4b. Define 9 tool functions
- 4 inventory tools, 2 quoting tools, 3 sales tools
- Each wraps required helper functions with validation and formatted output
- Each tool has docstring and type hints (D4, D5)

### 4c. Create agents
- 3 worker `ToolCallingAgent`s (max_steps=5)
- 3 `ManagedAgent` wrappers with descriptive names
- 1 orchestrator `ToolCallingAgent` (max_steps=10) with system prompt
- Orchestrator prompt enforces: rationale in outputs (D2), no internal data leakage (D3)

### 4d. Integrate into run_test_scenarios()
- Fix `init_database()` bug (add `db_engine` param)
- Wire `process_customer_request()` into the test loop

All 7 required helper functions covered:
| Helper Function | Tool | Agent | Checklist |
|---|---|---|---|
| `create_transaction` | `reorder_stock`, `finalize_sale` | Inventory, Sales | B8 |
| `get_all_inventory` | `check_inventory` | Inventory | B9 |
| `get_stock_level` | `check_item_stock`, `finalize_sale` | Inventory, Sales | B10 |
| `get_supplier_delivery_date` | `check_delivery_date` | Inventory | B11 |
| `get_cash_balance` | `reorder_stock`, `check_cash_balance` | Inventory, Sales | B12 |
| `generate_financial_report` | `get_financial_report` | Sales | B13 |
| `search_quote_history` | `search_quotes` | Quoting | B14 |

---

## Step 5: Test and Evaluate

**Goal**: Run against `quote_requests_sample.csv` (20 requests), produce `test_results.csv`.
**Satisfies**: C1-C5, E4

- Run: `python project_starter.py`
- Verify C1: All 20 requests from `quote_requests_sample.csv` processed
- Verify C2: `test_results.csv` generated
- Verify C3: >= 3 requests changed cash balance
- Verify C4: >= 3 quotes successfully fulfilled
- Verify C5: Not all requests fulfilled
- Fix any agent failures and re-run

---

## Step 6: Reflect and Document

**Goal**: Write comprehensive report.
**Satisfies**: C6-C8, E3

1. **C6 - Architecture explanation**: Why 4 agents, role of each, decision-making rationale, reference to diagram
2. **C7 - Evaluation results**: Discuss test_results.csv, identify specific strengths
3. **C8 - Improvement suggestions**: At least 2 distinct suggestions (e.g., fuzzy item matching, customer negotiation agent)

Save as `design_document.md`.

---

## Critical Files

| File | Action |
|---|---|
| [project_starter.py](project_starter.py) | Modify - all agent code + review comments |
| [quote_requests_sample.csv](quote_requests_sample.csv) | Read - 20 test requests |
| [quotes.csv](quotes.csv) | Read - 108 historical quotes |
| [quote_requests.csv](quote_requests.csv) | Read - 400 historical requests |
| [requirements.txt](requirements.txt) | Modify - add smolagents |
| `workflow_diagram.png` | Create - agent workflow diagram |
| `test_results.csv` | Generated - evaluation output |
| `design_document.md` | Create - reflection report |
