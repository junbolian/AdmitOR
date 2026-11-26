import gurobipy as gp
from gurobipy import GRB

def solve(params):
    purchase_price = params["purchase_price"]  # list of 4: [Winter, Spring, Summer, Autumn]
    sale_price = params["sale_price"]          # list of 4: [Winter, Spring, Summer, Autumn]
    max_sales = params["max_sales"]            # list of 4: [Winter, Spring, Summer, Autumn]
    storage_capacity = params["storage_capacity"]  # scalar (10,000 m³)
    a = params["storage_cost_a"]               # yuan/m³
    b = params["storage_cost_b"]               # yuan/m³/quarter

    # Quarters: 0=Winter, 1=Spring, 2=Summer, 3=Autumn
    quarters = [0, 1, 2, 3]
    quarter_names = ["Winter", "Spring", "Summer", "Autumn"]

    # Units: prices are in 10,000 yuan per 10,000 m³, which equals 1 yuan/m³ = 1 unit/unit.
    # Quantities (purchase, sale, storage) are in 10,000 m³.
    # Storage cost is in yuan/m³ = 10,000 yuan / 10,000 m³, so same unit as price when
    # multiplied by quantity in 10,000 m³.
    # Profit in 10,000 yuan.

    # Decision variables:
    # x[i] = amount purchased in quarter i (10,000 m³)
    # s[i] = amount sold in quarter i (10,000 m³)
    # inv[i][j] = amount stored from quarter i, sold in quarter j (j > i), in 10,000 m³
    #   storage time = j - i quarters
    # All timber purchased in quarter i is either sold in quarter i or stored and sold in a later quarter.
    # By end of autumn (quarter 3), all inventory must be sold.

    model = gp.Model("timber")
    model.setParam("OutputFlag", 0)

    # x[i]: purchase in quarter i
    x = model.addVars(4, lb=0.0, name="x")

    # s[i][j]: amount bought in quarter i and sold in quarter j (j >= i)
    # For j > i, it incurs storage cost with u = j - i quarters
    s = {}
    for i in quarters:
        for j in range(i, 4):
            s[i, j] = model.addVar(lb=0.0, name=f"s_{i}_{j}")

    # Constraint 1: What's bought in quarter i equals sum of all s[i,j] for j >= i
    for i in quarters:
        model.addConstr(
            x[i] == gp.quicksum(s[i, j] for j in range(i, 4)),
            name=f"purchase_balance_{i}"
        )

    # Constraint 2: Total sales in quarter j must not exceed max_sales[j]
    for j in quarters:
        model.addConstr(
            gp.quicksum(s[i, j] for i in range(0, j + 1)) <= max_sales[j],
            name=f"max_sales_{j}"
        )

    # Constraint 3: Warehouse capacity — inventory held at any point in time
    # At end of quarter j (before sales in j+1), inventory is sum of s[i,k] for i<=j, k>j
    # Actually, we track inventory at the start of each quarter after purchases.
    # At start of quarter j (after purchasing x[j]), inventory includes:
    #   - all units bought in previous quarters not yet sold: sum_{i<j} sum_{k>=j} s[i,k]
    #   - units just purchased in quarter j: x[j]
    # So total at start of quarter j = sum_{i<=j} sum_{k>=j} s[i,k]
    for j in quarters:
        model.addConstr(
            gp.quicksum(s[i, k] for i in range(0, j + 1) for k in range(j, 4)) <= storage_capacity,
            name=f"warehouse_{j}"
        )

    # Storage cost for s[i,j] with j > i:
    # u = j - i quarters of storage
    # cost = (a + b*u) yuan/m³ × (s[i,j] × 10,000 m³) / 10,000 = (a + b*u) × s[i,j]
    # (since a,b in yuan/m³ and s in 10,000 m³, cost in 10,000 yuan)

    # Revenue: sale_price[j] * total_sold_in_j (in 10,000 yuan)
    # Cost: purchase_price[i] * x[i] + storage costs (in 10,000 yuan)

    revenue = gp.quicksum(
        sale_price[j] * gp.quicksum(s[i, j] for i in range(0, j + 1))
        for j in quarters
    )

    purchase_cost = gp.quicksum(purchase_price[i] * x[i] for i in quarters)

    storage_cost_expr = gp.quicksum(
        (a + b * (j - i)) * s[i, j]
        for i in quarters
        for j in range(i + 1, 4)
    )

    # Objective: maximize profit = revenue - purchase_cost - storage_cost
    model.setObjective(revenue - purchase_cost - storage_cost_expr, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}