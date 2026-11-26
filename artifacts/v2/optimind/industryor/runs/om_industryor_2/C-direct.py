import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sales_price = params["sales_price"]
    raw_material_cost = params["raw_material_cost"]
    outsourcing_cost = params["outsourcing_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backorder_cost = params["backorder_cost"]
    labor_hours_per_unit = params["labor_hours_per_unit"]
    regular_hours_per_worker = params["regular_hours_per_worker"]
    regular_wage_per_hour = params["regular_wage_per_hour"]
    max_overtime_hours_per_worker = params["max_overtime_hours_per_worker"]
    overtime_wage_per_hour = params["overtime_wage_per_hour"]
    hiring_cost = params["hiring_cost"]
    firing_cost = params["firing_cost"]
    initial_workforce = params["initial_workforce"]
    initial_inventory = params["initial_inventory"]
    terminal_min_inventory = params["terminal_min_inventory"]
    demand = params["demand"]

    T = 6  # months: 0..5 (Jan..Jun)

    model = gp.Model("foldable_tables")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[t]: in-house production in month t
    x = model.addVars(T, name="x", lb=0.0)
    # o[t]: outsourced units in month t
    o = model.addVars(T, name="o", lb=0.0)
    # w[t]: workforce at end of month t (after hiring/firing)
    w = model.addVars(T, name="w", lb=0.0)
    # h[t]: workers hired at start of month t
    h = model.addVars(T, name="h", lb=0.0)
    # f[t]: workers fired at start of month t
    f = model.addVars(T, name="f", lb=0.0)
    # ot[t]: total overtime hours used in month t
    ot = model.addVars(T, name="ot", lb=0.0)
    # inv[t]: ending inventory at end of month t
    inv = model.addVars(T, name="inv", lb=0.0)
    # back[t]: ending backorders at end of month t
    back = model.addVars(T, name="back", lb=0.0)
    # sold[t]: units sold (demand fulfilled) in month t
    sold = model.addVars(T, name="sold", lb=0.0)

    # Workforce balance constraints
    for t in range(T):
        if t == 0:
            model.addConstr(w[t] == initial_workforce + h[t] - f[t], name=f"workforce_{t}")
        else:
            model.addConstr(w[t] == w[t-1] + h[t] - f[t], name=f"workforce_{t}")

    # Labor capacity constraints
    for t in range(T):
        # Regular hours available: w[t] * regular_hours_per_worker
        # Overtime hours: ot[t] <= w[t] * max_overtime_hours_per_worker
        model.addConstr(ot[t] <= w[t] * max_overtime_hours_per_worker, name=f"max_ot_{t}")
        # Production requires labor: x[t] * labor_hours_per_unit <= regular_hours + overtime
        model.addConstr(
            x[t] * labor_hours_per_unit <= w[t] * regular_hours_per_worker + ot[t],
            name=f"labor_cap_{t}"
        )

    # Inventory balance and demand fulfillment
    # inv[t] - back[t] = inv[t-1] - back[t-1] + x[t] + o[t] - demand[t]
    # inv[t] >= 0, back[t] >= 0, and inv[t] * back[t] = 0 (complementarity via standard LP)
    # Since both inv and back are >= 0, the balance ensures at most one is positive.
    for t in range(T):
        prev_inv = initial_inventory if t == 0 else inv[t-1]
        prev_back = 0.0 if t == 0 else back[t-1]
        model.addConstr(
            inv[t] - back[t] == prev_inv - prev_back + x[t] + o[t] - demand[t],
            name=f"inv_balance_{t}"
        )

    # Units sold: sold[t] = demand[t] - (back[t] - prev_back) where net backorder change matters
    # Actually, sold[t] = demand satisfied this month
    # Revenue is based on units sold. Units sold = current demand + previous backorders - new backorders
    # = demand[t] + prev_back - back[t]
    for t in range(T):
        prev_back = 0.0 if t == 0 else back[t-1]
        model.addConstr(
            sold[t] == demand[t] + prev_back - back[t],
            name=f"sold_{t}"
        )
        # sold cannot be negative
        model.addConstr(sold[t] >= 0, name=f"sold_nonneg_{t}")

    # Terminal conditions
    model.addConstr(inv[T-1] >= terminal_min_inventory, name="terminal_inv")
    model.addConstr(back[T-1] == 0.0, name="terminal_back")

    # Objective: maximize total net profit
    # Revenue: sum of sold[t] * sales_price
    # Costs:
    #   raw material: x[t] * raw_material_cost
    #   outsourcing: o[t] * outsourcing_cost
    #   regular labor: w[t] * regular_hours_per_worker * regular_wage_per_hour (paid regardless)
    #   overtime labor: ot[t] * overtime_wage_per_hour
    #   hiring: h[t] * hiring_cost
    #   firing: f[t] * firing_cost
    #   inventory holding: inv[t] * inventory_holding_cost
    #   backorder: back[t] * backorder_cost

    revenue = gp.quicksum(sold[t] * sales_price for t in range(T))

    total_cost = gp.quicksum(
        x[t] * raw_material_cost
        + o[t] * outsourcing_cost
        + w[t] * regular_hours_per_worker * regular_wage_per_hour
        + ot[t] * overtime_wage_per_hour
        + h[t] * hiring_cost
        + f[t] * firing_cost
        + inv[t] * inventory_holding_cost
        + back[t] * backorder_cost
        for t in range(T)
    )

    model.setObjective(revenue - total_cost, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}