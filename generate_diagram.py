"""
Generate the workflow diagram for the Beaver's Choice Paper Company Multi-Agent System.
This script creates workflow_diagram.png showing agents, tools, data flow, and helper function mappings.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 16))
ax.set_xlim(0, 20)
ax.set_ylim(0, 16)
ax.axis('off')
fig.patch.set_facecolor('white')

# =====================================================================
# Title
# =====================================================================
ax.text(10, 15.5, "Beaver's Choice Paper Company\nMulti-Agent System Workflow",
        fontsize=18, fontweight='bold', ha='center', va='center',
        color='#1a1a2e')

# =====================================================================
# Color scheme
# =====================================================================
ORCH_COLOR = '#4361ee'
INV_COLOR = '#2a9d8f'
QUOTE_COLOR = '#e76f51'
SALES_COLOR = '#9b5de5'
TOOL_BG = '#f0f0f0'
ARROW_COLOR = '#555555'
CUSTOMER_COLOR = '#f4a261'

# =====================================================================
# Helper to draw agent boxes
# =====================================================================
def draw_agent_box(ax, x, y, w, h, label, sublabel, color):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(box)
    ax.text(x + w/2, y + h*0.65, label, fontsize=12, fontweight='bold',
            ha='center', va='center', color='white')
    ax.text(x + w/2, y + h*0.3, sublabel, fontsize=8,
            ha='center', va='center', color='white', style='italic')

def draw_tool_box(ax, x, y, w, h, tool_name, helper_funcs):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                         facecolor=TOOL_BG, edgecolor='#999999', linewidth=1.5)
    ax.add_patch(box)
    ax.text(x + w/2, y + h*0.62, tool_name, fontsize=8, fontweight='bold',
            ha='center', va='center', color='#333333')
    ax.text(x + w/2, y + h*0.25, helper_funcs, fontsize=6.5,
            ha='center', va='center', color='#666666', style='italic')

def draw_arrow(ax, x1, y1, x2, y2, label='', color=ARROW_COLOR, style='->', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.15, label, fontsize=7, ha='center', va='bottom',
                color=color, fontweight='bold')

# =====================================================================
# Customer input box
# =====================================================================
cust_box = FancyBboxPatch((7.5, 14.0), 5, 0.9, boxstyle="round,pad=0.15",
                          facecolor=CUSTOMER_COLOR, edgecolor='white', linewidth=2, alpha=0.9)
ax.add_patch(cust_box)
ax.text(10, 14.45, "Customer Request (text input)", fontsize=11, fontweight='bold',
        ha='center', va='center', color='white')

# =====================================================================
# ORCHESTRATOR AGENT (top center)
# =====================================================================
draw_agent_box(ax, 7.0, 11.5, 6, 1.8, "ORCHESTRATOR AGENT",
               "Parses requests  |  Delegates tasks  |  Composes responses", ORCH_COLOR)

# Arrow from customer to orchestrator
draw_arrow(ax, 10, 14.0, 10, 13.3, "Customer request", ORCH_COLOR, '->')

# =====================================================================
# INVENTORY AGENT (left)
# =====================================================================
draw_agent_box(ax, 0.5, 7.5, 5.5, 1.5, "INVENTORY AGENT",
               "Stock checks  |  Reorder decisions  |  Delivery estimates", INV_COLOR)

# Inventory tools
draw_tool_box(ax, 0.3, 5.5, 2.6, 0.85, "check_inventory", "get_all_inventory()")
draw_tool_box(ax, 3.2, 5.5, 2.6, 0.85, "check_item_stock", "get_stock_level()")
draw_tool_box(ax, 0.3, 4.2, 2.6, 0.85, "check_delivery_date", "get_supplier_delivery_date()")
draw_tool_box(ax, 3.2, 4.2, 2.6, 0.85, "reorder_stock", "create_transaction()\nget_cash_balance()")

# Arrows: Orchestrator -> Inventory
draw_arrow(ax, 7.0, 12.2, 5.0, 9.0, "1. Check availability", INV_COLOR)

# Arrows: Inventory -> Tools
draw_arrow(ax, 2.0, 7.5, 1.6, 6.35, '', INV_COLOR, '->')
draw_arrow(ax, 4.5, 7.5, 4.5, 6.35, '', INV_COLOR, '->')
draw_arrow(ax, 2.0, 7.5, 1.6, 5.05, '', INV_COLOR, '->')
draw_arrow(ax, 4.5, 7.5, 4.5, 5.05, '', INV_COLOR, '->')

# =====================================================================
# QUOTING AGENT (center)
# =====================================================================
draw_agent_box(ax, 7.25, 7.5, 5.5, 1.5, "QUOTING AGENT",
               "Historical quote lookup  |  Bulk discount pricing", QUOTE_COLOR)

# Quoting tools
draw_tool_box(ax, 7.25, 5.5, 2.6, 0.85, "search_quotes", "search_quote_history()")
draw_tool_box(ax, 10.15, 5.5, 2.6, 0.85, "calculate_quote", "paper_supplies catalog\n+ discount logic")

# Arrows: Orchestrator -> Quoting
draw_arrow(ax, 10, 11.5, 10, 9.0, "2. Generate quote", QUOTE_COLOR)

# Arrows: Quoting -> Tools
draw_arrow(ax, 8.5, 7.5, 8.55, 6.35, '', QUOTE_COLOR, '->')
draw_arrow(ax, 11.5, 7.5, 11.45, 6.35, '', QUOTE_COLOR, '->')

# =====================================================================
# SALES AGENT (right)
# =====================================================================
draw_agent_box(ax, 14.0, 7.5, 5.5, 1.5, "SALES AGENT",
               "Finalize transactions  |  Cash verification  |  Reports", SALES_COLOR)

# Sales tools
draw_tool_box(ax, 13.8, 5.5, 2.6, 0.85, "finalize_sale", "create_transaction()\nget_stock_level()")
draw_tool_box(ax, 16.7, 5.5, 2.6, 0.85, "check_cash_balance", "get_cash_balance()")
draw_tool_box(ax, 14.8, 4.2, 3.5, 0.85, "get_financial_report", "generate_financial_report()")

# Arrows: Orchestrator -> Sales
draw_arrow(ax, 13.0, 12.2, 15.5, 9.0, "3. Finalize sale", SALES_COLOR)

# Arrows: Sales -> Tools
draw_arrow(ax, 15.5, 7.5, 15.1, 6.35, '', SALES_COLOR, '->')
draw_arrow(ax, 17.5, 7.5, 18.0, 6.35, '', SALES_COLOR, '->')
draw_arrow(ax, 16.5, 7.5, 16.55, 5.05, '', SALES_COLOR, '->')

# =====================================================================
# Database (bottom center)
# =====================================================================
db_box = FancyBboxPatch((7.5, 2.2), 5, 1.3, boxstyle="round,pad=0.15",
                        facecolor='#264653', edgecolor='white', linewidth=2, alpha=0.9)
ax.add_patch(db_box)
ax.text(10, 2.95, "SQLite Database", fontsize=11, fontweight='bold',
        ha='center', va='center', color='white')
ax.text(10, 2.55, "transactions  |  inventory  |  quotes  |  quote_requests",
        fontsize=7, ha='center', va='center', color='#aaddcc')

# Arrows from tools to database
draw_arrow(ax, 1.6, 4.2, 7.8, 3.5, '', '#264653', '->', 1.0)
draw_arrow(ax, 4.5, 4.2, 8.0, 3.5, '', '#264653', '->', 1.0)
draw_arrow(ax, 8.55, 5.5, 8.8, 3.5, '', '#264653', '->', 1.0)
draw_arrow(ax, 15.1, 4.2, 12.2, 3.5, '', '#264653', '->', 1.0)
draw_arrow(ax, 18.0, 5.5, 12.5, 3.5, '', '#264653', '->', 1.0)
draw_arrow(ax, 16.55, 4.2, 12.3, 3.5, '', '#264653', '->', 1.0)

# =====================================================================
# Customer response (bottom left)
# =====================================================================
resp_box = FancyBboxPatch((0.5, 2.2), 5.5, 1.3, boxstyle="round,pad=0.15",
                          facecolor=CUSTOMER_COLOR, edgecolor='white', linewidth=2, alpha=0.9)
ax.add_patch(resp_box)
ax.text(3.25, 2.95, "Customer Response (text output)", fontsize=10, fontweight='bold',
        ha='center', va='center', color='white')
ax.text(3.25, 2.55, "Quote + rationale  |  Fulfillment status  |  Delivery date",
        fontsize=7, ha='center', va='center', color='white')

# Arrow from orchestrator to response
draw_arrow(ax, 7.0, 11.8, 3.25, 3.5, "4. Final response", ORCH_COLOR, '->', 2.0)

# =====================================================================
# Legend
# =====================================================================
ax.text(14.5, 2.5, "Legend:", fontsize=9, fontweight='bold', color='#333')

legend_items = [
    (ORCH_COLOR, "Orchestrator Agent"),
    (INV_COLOR, "Inventory Agent"),
    (QUOTE_COLOR, "Quoting Agent"),
    (SALES_COLOR, "Sales Agent"),
    ('#999999', "Tool (helper function)"),
    ('#264653', "Database"),
]
for i, (color, label) in enumerate(legend_items):
    y_pos = 2.2 - i * 0.3
    ax.plot(14.7, y_pos, 's', color=color, markersize=8)
    ax.text(15.1, y_pos, label, fontsize=7.5, va='center', color='#333')

# =====================================================================
# Helper function summary
# =====================================================================
ax.text(0.5, 1.5, "All 7 Required Helper Functions Used:",
        fontsize=9, fontweight='bold', color='#333')
funcs_text = (
    "create_transaction() [Inventory + Sales]  |  get_all_inventory() [Inventory]  |  "
    "get_stock_level() [Inventory + Sales]  |  get_supplier_delivery_date() [Inventory]\n"
    "get_cash_balance() [Inventory + Sales]  |  generate_financial_report() [Sales]  |  "
    "search_quote_history() [Quoting]"
)
ax.text(0.5, 0.9, funcs_text, fontsize=7.5, color='#555', va='center')

# =====================================================================
# Framework note
# =====================================================================
ax.text(0.5, 0.3, "Framework: smolagents (HuggingFace)  |  Model: gpt-4o-mini  |  Max agents: 4 (within 5-agent limit)",
        fontsize=7.5, color='#888', va='center', style='italic')

plt.tight_layout()
plt.savefig("/Users/evgeny.ponomarenko/Documents/Projects/Trainings/Multi Agent Systems/workflow_diagram.png",
            dpi=150, bbox_inches='tight', facecolor='white')
print("Saved workflow_diagram.png")
