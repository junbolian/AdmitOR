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
        fixed_cost_val = fixed_cost
        capacity_val = capacity
    else:
        facilities = [f"facility_{i}" for i in range(len(fixed_cost))]
        fixed_cost_val = {f: fixed_cost[i] for i, f in enumerate(facilities)}
        capacity_val = {f: capacity[i] for i, f in enumerate(facilities)}

    if isinstance(demand, dict):
        customers = list(demand.keys())
        demand_val = demand
    else:
        customers = [f"customer_{j}" for j in range(len(demand))]
        demand_val = {c: demand[j] for j, c in enumerate(customers)}

    # shipping_cost: rows = facilities, cols = customers
    # Could be dict of dicts, list of lists, etc.
    def get_shipping(f, c):
        fi = facilities.index(f)
        ci = customers.index(c)
        if isinstance(shipping_cost, dict):
            sc_row = shipping_cost[f] if f in shipping_cost else shipping_cost[list(shipping_cost.keys())[fi]]
            if isinstance(sc_row, dict):
                return sc_row[c] if c in sc_row else sc_row[list(sc_row.keys())[ci]]
            else:
                return sc_row[ci]
        else:
            row = shipping_cost[fi]
            if isinstance(row, dict):
                return row[c] if c in row else row[list(row.keys())[ci]]
            else:
                return row[ci]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open facility i
    open_var = {f: model.addVar(vtype=GRB.BINARY, name=f"open_{f}") for f in facilities}

    # Continuous variable: amount shipped from facility i to customer j
    ship = {
        (f, c): model.addVar(lb=0.0, name=f"ship_{f}_{c}")
        for f in facilities
        for c in customers
    }

    # Objective: minimize fixed costs + shipping costs
    obj = gp.quicksum(fixed_cost_val[f] * open_var[f] for f in facilities) + \
          gp.quicksum(get_shipping(f, c) * ship[f, c] for f in facilities for c in customers)
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand constraints: each customer's demand must be fully met
    for c in customers:
        model.addConstr(
            gp.quicksum(ship[f, c] for f in facilities) == demand_val[c],
            name=f"demand_{c}"
        )

    # Capacity constraints: total shipped from facility cannot exceed capacity if open
    for f in facilities:
        model.addConstr(
            gp.quicksum(ship[f, c] for c in customers) <= capacity_val[f] * open_var[f],
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