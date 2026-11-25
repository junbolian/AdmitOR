import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    # Handle both dict and list inputs
    if isinstance(fixed_cost, dict):
        facilities = list(fixed_cost.keys())
        fixed_cost_val = {f: fixed_cost[f] for f in facilities}
    else:
        facilities = [f"facility_{i}" for i in range(len(fixed_cost))]
        fixed_cost_val = {f: fixed_cost[i] for i, f in enumerate(facilities)}

    if isinstance(capacity, dict):
        capacity_val = {f: capacity[f] for f in facilities}
    else:
        capacity_val = {f: capacity[i] for i, f in enumerate(facilities)}

    if isinstance(demand, dict):
        customers = list(demand.keys())
        demand_val = {c: demand[c] for c in customers}
    else:
        customers = [f"customer_{i}" for i in range(len(demand))]
        demand_val = {c: demand[i] for i, c in enumerate(customers)}

    # shipping_cost can be a list of lists or dict of dicts
    def get_shipping(f, c):
        fi = facilities.index(f)
        ci = customers.index(c)
        if isinstance(shipping_cost, dict):
            row = shipping_cost[f]
            if isinstance(row, dict):
                return row[c]
            else:
                return row[ci]
        else:
            row = shipping_cost[fi]
            if isinstance(row, dict):
                return row[c]
            else:
                return row[ci]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: open_var[f] = 1 if facility f is opened
    open_var = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous variables: ship_var[f, c] = units shipped from facility f to customer c
    ship_var = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost_val[f] * open_var[f] for f in facilities) +
        gp.quicksum(get_shipping(f, c) * ship_var[f, c] for f in facilities for c in customers),
        GRB.MINIMIZE
    )

    # Demand constraints: each customer's demand must be fully met
    for c in customers:
        model.addConstr(
            gp.quicksum(ship_var[f, c] for f in facilities) == demand_val[c],
            name=f"demand_{c}"
        )

    # Capacity constraints: total shipped from facility cannot exceed capacity
    for f in facilities:
        model.addConstr(
            gp.quicksum(ship_var[f, c] for c in customers) <= capacity_val[f] * open_var[f],
            name=f"capacity_{f}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}