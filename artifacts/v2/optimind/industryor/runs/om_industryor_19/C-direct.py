import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    tables_per_order_A = params["tables_per_order_A"]
    tables_per_order_B = params["tables_per_order_B"]
    tables_per_order_C = params["tables_per_order_C"]
    min_tables = params["min_tables"]
    max_tables = params["max_tables"]
    min_tables_B_if_A = params["min_tables_B_if_A"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Number of orders from each supplier (non-negative integers)
    orders_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="orders_A")
    orders_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="orders_B")
    orders_C = model.addVar(vtype=GRB.INTEGER, lb=0, name="orders_C")

    # Binary indicators: whether any order is placed with each supplier
    y_A = model.addVar(vtype=GRB.BINARY, name="y_A")
    y_B = model.addVar(vtype=GRB.BINARY, name="y_B")

    # Total tables
    tables_A = orders_A * tables_per_order_A
    tables_B = orders_B * tables_per_order_B
    tables_C = orders_C * tables_per_order_C

    # Objective: minimize total cost
    model.setObjective(
        cost_A * tables_A + cost_B * tables_B + cost_C * tables_C,
        GRB.MINIMIZE
    )

    # Total tables constraints
    total_tables = tables_A + tables_B + tables_C
    model.addConstr(total_tables >= min_tables, name="min_tables")
    model.addConstr(total_tables <= max_tables, name="max_tables")

    # Big-M for linking orders to binary indicators
    # Max orders from A: max_tables / tables_per_order_A
    M_A = max_tables / tables_per_order_A
    M_B = max_tables / tables_per_order_B

    # y_A = 1 iff orders_A >= 1
    model.addConstr(orders_A <= M_A * y_A, name="y_A_upper")
    model.addConstr(orders_A >= y_A, name="y_A_lower")

    # y_B = 1 iff orders_B >= 1
    model.addConstr(orders_B <= M_B * y_B, name="y_B_upper")
    model.addConstr(orders_B >= y_B, name="y_B_lower")

    # If any order from A, then tables from B >= min_tables_B_if_A
    # tables_B >= min_tables_B_if_A * y_A
    model.addConstr(tables_B >= min_tables_B_if_A * y_A, name="min_B_if_A")

    # If any order from B, then must order from C (orders_C >= 1)
    model.addConstr(orders_C >= y_B, name="C_if_B")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}