import pandas as pd
import numpy as np
import os
import time
import json
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

# === REVIEW: generate_sample_inventory ===
# Purpose: Creates a reproducible random subset (40%) of the paper_supplies catalog to simulate
#   realistic partial inventory. Only ~18 of 46 items will be stocked.
# Assigns each selected item a random stock quantity (200-800) and a minimum reorder level (50-150).
# Used by: init_database() to seed the initial inventory table.
# Returns: DataFrame with columns: item_name, category, unit_price, current_stock, min_stock_level
# Agent usage: Not directly used as an agent tool - called during DB initialization only.
# Key insight: Because only 40% of items are stocked, many customer requests for unstocked items
#   will result in partial fulfillment or rejection - this is expected behavior.
def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

# === REVIEW: init_database ===
# Purpose: Full database setup - creates all tables and seeds initial data.
# Steps: (1) Creates empty 'transactions' table for stock orders and sales
#   (2) Loads quote_requests.csv (400 records) into 'quote_requests' table
#   (3) Loads quotes.csv (108 records) into 'quotes' table with metadata extraction
#   (4) Generates random inventory subset via generate_sample_inventory()
#   (5) Seeds initial cash balance of $50,000 as a sales transaction
#   (6) Records initial stock orders for each inventory item
# Used by: run_test_scenarios() at startup (must pass db_engine argument).
# Returns: The initialized SQLAlchemy engine.
# Agent usage: Not an agent tool - one-time initialization at program start.
# NOTE: run_test_scenarios() has a bug on line 616 - calls init_database() without db_engine param.
def init_database(db_engine: Engine, seed: int = 137) -> Engine:
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

# === REVIEW: create_transaction ===
# Purpose: Records a single transaction (stock purchase or customer sale) in the database.
# Parameters: item_name, transaction_type ('stock_orders' or 'sales'), quantity, price, date.
# Returns: Integer ID of the newly created transaction row.
# Validation: Raises ValueError if transaction_type is not 'stock_orders' or 'sales'.
# Side effects: Modifies the 'transactions' table in the SQLite database.
# Agent usage: CRITICAL - used by TWO agent tools:
#   - Inventory Agent's reorder_stock tool (transaction_type='stock_orders')
#   - Sales Agent's finalize_sale tool (transaction_type='sales')
# Rubric: B8 requires this function to be used in at least one tool definition.
def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

# === REVIEW: get_all_inventory ===
# Purpose: Retrieves a snapshot of ALL items with positive stock as of a specific date.
# Calculates net stock per item: SUM(stock_orders) - SUM(sales) up to as_of_date.
# Returns: Dict[str, int] mapping item names to their current stock quantities.
#   Only items with stock > 0 are included in the result.
# Agent usage: Used by Inventory Agent's check_inventory tool to give a full stock overview.
# Rubric: B9 requires this function to be used in at least one tool definition.
def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

# === REVIEW: get_stock_level ===
# Purpose: Retrieves the net stock level of a SINGLE specific item as of a given date.
# Calculates: SUM(stock_orders units) - SUM(sales units) for the item up to as_of_date.
# Returns: Single-row DataFrame with columns 'item_name' and 'current_stock'.
#   Returns 0 if the item has no transactions (COALESCE handles NULL case).
# Agent usage: Used by TWO agent tools:
#   - Inventory Agent's check_item_stock tool (to check individual item availability)
#   - Sales Agent's finalize_sale tool (to verify stock before completing a sale)
# Rubric: B10 requires this function to be used in at least one tool definition.
def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

# === REVIEW: get_supplier_delivery_date ===
# Purpose: Estimates when a supplier delivery would arrive based on order quantity.
# Delivery lead time tiers: <=10 units = same day, 11-100 = +1 day,
#   101-1000 = +4 days, >1000 = +7 days.
# Parameters: input_date_str (ISO YYYY-MM-DD), quantity (number of units).
# Returns: Estimated delivery date as ISO format string (YYYY-MM-DD).
# Fallback: If date parsing fails, uses current date as base.
# Agent usage: Used by Inventory Agent's check_delivery_date tool to estimate
#   when restocked items would arrive from the supplier.
# Rubric: B11 requires this function to be used in at least one tool definition.
def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

# === REVIEW: get_cash_balance ===
# Purpose: Calculates the company's net cash balance as of a given date.
# Formula: SUM(sales prices) - SUM(stock_orders prices) for all transactions up to as_of_date.
# Initial balance: Starts at $50,000 (seeded as a sales transaction in init_database).
# Returns: Float representing available cash. Returns 0.0 if no transactions or on error.
# Agent usage: Used by TWO agent tools:
#   - Inventory Agent's reorder_stock tool (to verify cash before placing stock orders)
#   - Sales Agent's check_cash_balance tool (to report current financial position)
# Rubric: B12 requires this function to be used in at least one tool definition.
def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


# === REVIEW: generate_financial_report ===
# Purpose: Generates a comprehensive financial report including cash, inventory valuation,
#   total assets, per-item inventory breakdown, and top 5 selling products by revenue.
# Internally calls: get_cash_balance() and get_stock_level() for each inventory item.
# Returns: Dict with keys: as_of_date, cash_balance, inventory_value, total_assets,
#   inventory_summary (list of dicts), top_selling_products (list of top 5 dicts).
# Agent usage: Used by Sales Agent's get_financial_report tool to provide
#   post-transaction financial snapshots and final reporting.
# Rubric: B13 requires this function to be used in at least one tool definition.
def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


# === REVIEW: search_quote_history ===
# Purpose: Searches historical quotes for matches based on keyword terms.
# Searches both the original customer request text (quote_requests.response) and
#   the quote explanation text (quotes.quote_explanation) using LIKE matching.
# Returns: List[Dict] with up to 'limit' results (default 5), each containing:
#   original_request, total_amount, quote_explanation, job_type, order_size, event_type, order_date.
# Joins quotes table with quote_requests table on request_id/id.
# Agent usage: Used by Quoting Agent's search_quotes tool to find similar past quotes
#   and inform pricing decisions based on historical patterns.
# Rubric: B14 requires this function to be used in at least one tool definition.
def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# =====================================================================
# Environment setup and model initialization
# =====================================================================
dotenv.load_dotenv()

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)


# =====================================================================
# Item name matching utility
# Maps customer descriptions to exact catalog names using fuzzy matching
# =====================================================================

# Build a lookup of exact catalog item names
CATALOG_ITEMS = {p["item_name"].lower(): p["item_name"] for p in paper_supplies}
CATALOG_PRICES = {p["item_name"]: p["unit_price"] for p in paper_supplies}


def match_item_name(requested_name: str) -> str:
    """Match a customer's item description to the closest catalog item name.

    Tries exact match first, then partial/fuzzy match.
    Returns the exact catalog name or None if no match found.
    """
    lower_name = requested_name.strip().lower()

    # Exact match
    if lower_name in CATALOG_ITEMS:
        return CATALOG_ITEMS[lower_name]

    # Partial match: check if requested name contains a catalog name or vice versa
    best_match = None
    best_score = 0
    for catalog_lower, catalog_exact in CATALOG_ITEMS.items():
        # Check if catalog name is contained in the request
        if catalog_lower in lower_name:
            score = len(catalog_lower)
            if score > best_score:
                best_score = score
                best_match = catalog_exact
        # Check if request is contained in the catalog name
        elif lower_name in catalog_lower:
            score = len(lower_name)
            if score > best_score:
                best_score = score
                best_match = catalog_exact

    # Word overlap matching as fallback
    if best_match is None:
        request_words = set(lower_name.split())
        for catalog_lower, catalog_exact in CATALOG_ITEMS.items():
            catalog_words = set(catalog_lower.split())
            overlap = len(request_words & catalog_words)
            if overlap > best_score:
                best_score = overlap
                best_match = catalog_exact

    return best_match if best_score > 0 else None


# =====================================================================
# Tool definitions for agents
# Each tool wraps one or more of the 7 required helper functions.
# =====================================================================


# --- Tools for Inventory Agent ---

@tool
def check_inventory(as_of_date: str) -> str:
    """Check the complete inventory of all items currently in stock as of a given date.
    Returns a formatted list of item names and their stock quantities.

    Args:
        as_of_date: Date string in ISO format (YYYY-MM-DD) for inventory snapshot.
    """
    inventory = get_all_inventory(as_of_date)
    if not inventory:
        return "No items currently in stock."
    result = "Current inventory as of {}:\n".format(as_of_date)
    for item_name, qty in sorted(inventory.items()):
        result += "  - {}: {} units\n".format(item_name, qty)
    result += "\nTotal items in stock: {}".format(len(inventory))
    return result


@tool
def check_item_stock(item_name: str, as_of_date: str) -> str:
    """Check the stock level of a specific item as of a given date.
    Uses fuzzy matching to find the closest catalog item name.

    Args:
        item_name: The name of the paper item to check (will be matched to catalog).
        as_of_date: Date string in ISO format (YYYY-MM-DD).
    """
    matched_name = match_item_name(item_name)
    if matched_name is None:
        return "{}: NOT FOUND IN CATALOG. This item does not exist in our product line.".format(item_name)
    stock_df = get_stock_level(matched_name, as_of_date)
    stock_level = int(stock_df["current_stock"].iloc[0])
    if stock_level > 0:
        return "{} (catalog name: '{}'): {} units in stock as of {}".format(
            item_name, matched_name, stock_level, as_of_date
        )
    else:
        return "{} (catalog name: '{}'): OUT OF STOCK (0 units) as of {}".format(
            item_name, matched_name, as_of_date
        )


@tool
def check_delivery_date(order_date: str, quantity: int) -> str:
    """Estimate when a supplier delivery would arrive based on order date and quantity.
    Delivery times: <=10 units same day, 11-100 +1 day, 101-1000 +4 days, >1000 +7 days.

    Args:
        order_date: The date the order would be placed, in ISO format (YYYY-MM-DD).
        quantity: Number of units to order from the supplier.
    """
    delivery_date = get_supplier_delivery_date(order_date, quantity)
    return "Estimated delivery date for {} units ordered on {}: {}".format(
        quantity, order_date, delivery_date
    )


@tool
def reorder_stock(item_name: str, quantity: int, unit_price: float, order_date: str) -> str:
    """Place a stock reorder with the supplier for a specific item.
    Creates a stock_orders transaction that increases inventory and decreases cash.
    Checks cash balance before ordering. Uses fuzzy matching for item names.

    Args:
        item_name: The name of the item to reorder (will be matched to catalog).
        quantity: Number of units to order.
        unit_price: The cost per unit from the supplier.
        order_date: Date string in ISO format (YYYY-MM-DD).
    """
    matched_name = match_item_name(item_name)
    if matched_name is None:
        return "CANNOT REORDER: '{}' not found in catalog.".format(item_name)
    total_cost = quantity * unit_price
    cash = get_cash_balance(order_date)
    if total_cost > cash:
        return "CANNOT REORDER: Insufficient cash. Need ${:.2f}, have ${:.2f}".format(
            total_cost, cash
        )
    txn_id = create_transaction(matched_name, "stock_orders", quantity, total_cost, order_date)
    return "Reorder placed: {} units of {} at ${:.2f} total. Transaction ID: {}".format(
        quantity, matched_name, total_cost, txn_id
    )


# --- Tools for Quoting Agent ---

@tool
def search_quotes(search_terms: str) -> str:
    """Search historical quote records for similar past orders.
    Use comma-separated keywords related to the job type, event type, order size, or item types.

    Args:
        search_terms: Comma-separated keyword strings to search for in quote history (e.g. 'cardstock, ceremony, large').
    """
    terms_list = [t.strip() for t in search_terms.split(",") if t.strip()]
    results = search_quote_history(terms_list, limit=5)
    if not results:
        return "No matching historical quotes found for terms: {}".format(search_terms)
    output = "Found {} historical quotes:\n".format(len(results))
    for i, q in enumerate(results, 1):
        output += (
            "\n  Quote {}:\n"
            "    Amount: ${}\n"
            "    Job type: {}\n"
            "    Order size: {}\n"
            "    Event type: {}\n"
            "    Explanation: {}\n"
        ).format(
            i, q["total_amount"], q["job_type"],
            q["order_size"], q["event_type"],
            q["quote_explanation"][:300]
        )
    return output


@tool
def calculate_quote(items_json: str) -> str:
    """Calculate a price quote for a list of items with quantities.
    Applies bulk discounts based on total quantity ordered.
    Uses fuzzy matching to resolve item names to catalog entries.

    Args:
        items_json: JSON string of items list, each with 'item_name' and 'quantity' keys.
            Example: '[{"item_name": "A4 paper", "quantity": 500}, {"item_name": "Cardstock", "quantity": 300}]'
    """
    items = json.loads(items_json)
    total_units = sum(item["quantity"] for item in items)

    # Bulk discount tiers based on historical quote patterns
    if total_units > 5000:
        discount = 0.15
    elif total_units > 1000:
        discount = 0.10
    elif total_units > 500:
        discount = 0.05
    else:
        discount = 0.0

    breakdown = []
    subtotal = 0.0
    matched_items = []
    for item in items:
        name = item["item_name"]
        qty = item["quantity"]
        matched_name = match_item_name(name)
        if matched_name and matched_name in CATALOG_PRICES:
            unit_price = CATALOG_PRICES[matched_name]
            line_total = qty * unit_price
            subtotal += line_total
            breakdown.append("  {} ({}): {} x ${:.2f} = ${:.2f}".format(
                name, matched_name, qty, unit_price, line_total
            ))
            matched_items.append({"catalog_name": matched_name, "quantity": qty, "line_total": line_total})
        else:
            breakdown.append("  {}: ITEM NOT IN CATALOG - cannot quote".format(name))

    discount_amount = subtotal * discount
    total = round(subtotal - discount_amount, 2)

    result = "Quote breakdown:\n" + "\n".join(breakdown)
    result += "\n\nSubtotal: ${:.2f}".format(subtotal)
    if discount > 0:
        result += "\nBulk discount ({:.0f}%): -${:.2f}".format(discount * 100, discount_amount)
    result += "\nTotal: ${:.2f}".format(total)
    return result


# --- Tools for Sales Agent ---

@tool
def finalize_sale(item_name: str, quantity: int, sale_price: float, sale_date: str) -> str:
    """Finalize a sale by recording it as a sales transaction.
    Decreases inventory of the item and increases cash balance.
    Verifies stock availability before completing the sale.
    Uses fuzzy matching to resolve item names to catalog entries.

    Args:
        item_name: The name of the item being sold (will be matched to catalog).
        quantity: Number of units sold.
        sale_price: Total sale price for the entire quantity (not per unit).
        sale_date: Date string in ISO format (YYYY-MM-DD).
    """
    matched_name = match_item_name(item_name)
    if matched_name is None:
        return "SALE REJECTED: '{}' not found in catalog.".format(item_name)
    stock_df = get_stock_level(matched_name, sale_date)
    current_stock = int(stock_df["current_stock"].iloc[0])
    if current_stock < quantity:
        return "SALE REJECTED: Insufficient stock for {}. Have {} units, need {}.".format(
            matched_name, current_stock, quantity
        )
    txn_id = create_transaction(matched_name, "sales", quantity, sale_price, sale_date)
    return "Sale completed: {} units of {} for ${:.2f}. Transaction ID: {}".format(
        quantity, matched_name, sale_price, txn_id
    )


@tool
def check_cash_balance(as_of_date: str) -> str:
    """Check the current cash balance of the company as of a given date.

    Args:
        as_of_date: Date string in ISO format (YYYY-MM-DD).
    """
    balance = get_cash_balance(as_of_date)
    return "Cash balance as of {}: ${:.2f}".format(as_of_date, balance)


@tool
def get_financial_report(as_of_date: str) -> str:
    """Generate a complete financial report including cash balance, inventory value,
    total assets, and top-selling products.

    Args:
        as_of_date: Date string in ISO format (YYYY-MM-DD).
    """
    report = generate_financial_report(as_of_date)
    result = "Financial Report as of {}:\n".format(report["as_of_date"])
    result += "  Cash Balance: ${:.2f}\n".format(report["cash_balance"])
    result += "  Inventory Value: ${:.2f}\n".format(report["inventory_value"])
    result += "  Total Assets: ${:.2f}\n".format(report["total_assets"])
    if report["top_selling_products"]:
        result += "  Top Selling Products:\n"
        for p in report["top_selling_products"]:
            result += "    - {}: ${:.2f} revenue\n".format(
                p.get("item_name", "N/A"), p.get("total_revenue", 0)
            )
    return result


# =====================================================================
# Agent creation
# =====================================================================

# Worker Agent 1: Inventory Agent
# Handles stock checks, availability assessment, reorder decisions, delivery estimates
inventory_agent = ToolCallingAgent(
    tools=[check_inventory, check_item_stock, check_delivery_date, reorder_stock],
    model=model,
    max_steps=10,
    name="inventory_agent",
    description=(
        "Specialist agent for checking paper supply inventory levels, "
        "assessing stock availability for specific items, estimating supplier "
        "delivery dates, and placing restock orders when needed. "
        "IMPORTANT: Always use the date provided in the task for all tool calls. "
        "Start by calling check_inventory with the provided date to see all available items."
    ),
)

# Worker Agent 2: Quoting Agent
# Searches historical quotes and calculates prices with bulk discounts
quoting_agent = ToolCallingAgent(
    tools=[search_quotes, calculate_quote],
    model=model,
    max_steps=10,
    name="quoting_agent",
    description=(
        "Specialist agent for generating price quotes based on historical "
        "quote data and applying appropriate bulk discounts. Provide this agent "
        "with the list of items, quantities, job type, and event type."
    ),
)

# Worker Agent 3: Sales Agent
# Finalizes transactions, verifies cash, generates financial reports
sales_agent = ToolCallingAgent(
    tools=[finalize_sale, check_cash_balance, get_financial_report],
    model=model,
    max_steps=10,
    name="sales_agent",
    description=(
        "Specialist agent for finalizing sales transactions by recording them "
        "in the database. Also checks cash balance and generates financial "
        "reports. Use after a quote is ready to complete the sale."
    ),
)

# Orchestrator Agent: Manages the overall workflow
# Delegates to inventory, quoting, and sales agents
ORCHESTRATOR_PROMPT = """You are the customer service coordinator for Beaver's Choice Paper Company.

Your job is to process customer requests for paper supplies by coordinating with your specialist team.

CRITICAL DATE HANDLING:
- Each customer request contains "(Date of request: YYYY-MM-DD)" at the end.
- You MUST extract this date and pass it to ALL agents in your task descriptions.
- ALL inventory checks, quotes, and sales MUST use this exact date.

WORKFLOW FOR EACH REQUEST:
1. Extract the request date from the customer message.
2. Ask the inventory_agent to check full inventory using check_inventory with the request date. ALWAYS include the request date in your task message, e.g.: "Check inventory as of 2025-04-01. The customer needs..."
3. Compare the customer's requested items against available inventory items.
4. For items that ARE in stock with sufficient quantity, ask the quoting_agent to generate a quote. Include the request date.
5. MANDATORY: Ask the sales_agent to finalize the sale for EACH available item individually using the finalize_sale tool. Include the exact item name, quantity, total sale price, and the request date. You MUST wait for the sales_agent to confirm the sale was completed before proceeding.
6. ONLY AFTER the sales_agent confirms each sale, compose a professional customer-facing response.

SALE VERIFICATION:
- Do NOT claim a sale was completed unless the sales_agent explicitly confirms it with a Transaction ID.
- If the sales_agent reports a rejection (e.g., insufficient stock), report that item as unavailable to the customer.
- If no items can be sold, do NOT claim any sale was made. Inform the customer that the order cannot be fulfilled.

ITEM NAME MATCHING:
Our catalog uses these exact names. Map customer requests to these:
- "A4 paper", "Letter-sized paper", "Cardstock", "Colored paper", "Glossy paper"
- "Matte paper", "Recycled paper", "Eco-friendly paper", "Poster paper", "Banner paper"
- "Kraft paper", "Construction paper", "Wrapping paper", "Glitter paper"
- "Decorative paper", "Letterhead paper", "Legal-size paper", "Crepe paper"
- "Photo paper", "Uncoated paper", "Butcher paper", "Heavyweight paper"
- "Standard copy paper", "Bright-colored paper", "Patterned paper"
- "Paper plates", "Paper cups", "Paper napkins", "Disposable cups", "Table covers"
- "Envelopes", "Sticky notes", "Notepads", "Invitation cards", "Flyers"
- "Party streamers", "Decorative adhesive tape (washi tape)", "Paper party bags"
- "Name tags with lanyards", "Presentation folders"
- "Large poster paper (24x36 inches)", "Rolls of banner paper (36-inch width)"
- "100 lb cover stock", "80 lb text paper", "250 gsm cardstock", "220 gsm poster paper"

If a customer asks for "construction paper" use "Construction paper".
If they ask for "cardstock" use "Cardstock".
If they ask for "A4 glossy paper" these are TWO items: "A4 paper" and "Glossy paper".
Only items in inventory can be sold - check inventory FIRST.

IMPORTANT RULES:
- Only sell items confirmed as in-stock by the inventory agent.
- If an item is not in inventory, politely inform the customer it is unavailable.
- Always provide a rationale for pricing (mention bulk discounts when applied).
- Include delivery date estimates when fulfilling orders.
- If only some items can be fulfilled, explain what can and cannot be supplied with reasons.
- Be polite, professional, and transparent.
- NEVER expose internal profit margins, supplier costs, or system error messages.
- Always complete the FULL workflow: inventory check -> quote -> finalize sale.
- Always sign off as "Beaver's Choice Paper Company" - never use placeholders like "[Your Name]".
"""

orchestrator_agent = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, sales_agent],
    max_steps=15,
    instructions=ORCHESTRATOR_PROMPT,
    name="orchestrator_agent",
    description="Main orchestrator that coordinates inventory, quoting, and sales agents.",
)


def process_customer_request(request_text: str) -> str:
    """Process a single customer request through the multi-agent system.

    Args:
        request_text: The full customer request text including date context.

    Returns:
        str: The customer-facing response from the orchestrator.
    """
    try:
        response = orchestrator_agent.run(request_text)
        return str(response)
    except Exception as e:
        print(f"  [Agent Error: {type(e).__name__}: {e}]")
        return (
            "We apologize, but we were unable to fully process your request at this time. "
            "Please contact our sales team directly for assistance."
        )


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = round(report["cash_balance"], 2)
    current_inventory = round(report["inventory_value"], 2)

    # Multi-agent system is initialized at module level (orchestrator_agent).
    # No additional initialization needed here.

    results = []
    for req_num, (_, row) in enumerate(quote_requests_sample.iterrows(), start=1):
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {req_num} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        # Process the customer request through the multi-agent system
        response = process_customer_request(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = round(report["cash_balance"], 2)
        current_inventory = round(report["inventory_value"], 2)

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": req_num,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(2)  # Rate limit buffer for multiple LLM calls per request

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
