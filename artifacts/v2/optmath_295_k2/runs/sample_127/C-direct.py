import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_ordering_costs = params["fixed_ordering_costs"]
    variable_ordering_costs = params["variable_ordering_costs"]
    inventory_holding_costs = params["inventory_holding_costs"]
    demand = params["demand"]
    order_capacity = params["order_capacity"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    T = 14  # planning horizon (periods 1..14)

    model = gp.Model("lot_sizing")
    model.Params.OutputFlag = 0

    # Decision variables
    x = model.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="x")      # order quantity
    y = model.addVars(T, vtype=GRB.BINARY, name="y")                  # order placed?
    inv = model.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="inv")  # end-of-period inventory

    # Objective: minimize total fixed + variable ordering + holding costs
    model.setObjective(
        gp.quicksum(fixed_ordering_costs[t] * y[t] for t in range(T))
        + gp.quicksum(variable_ordering_costs[t] * x[t] for t in range(T))
        + gp.quicksum(inventory_holding_costs[t] * inv[t] for t in range(T)),
        GRB.MINIMIZE,
    )

    # Inventory balance: prev_inv + x[t] = demand[t] + inv[t]
    for t in range(T):
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        model.addConstr(prev_inv + x[t] == demand[t] + inv[t], name=f"balance_{t}")

    # Required ending inventory at end of period 14
    model.addConstr(inv[T - 1] == final_inventory, name="final_inventory")

    # Order-capacity linking: order only if y[t]=1, bounded by capacity
    for t in range(T):
        model.addConstr(x[t] <= order_capacity * y[t], name=f"cap_{t}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    status_map = {
        GRB.INFEASIBLE: "infeasible",
        GRB.UNBOUNDED: "unbounded",
        GRB.INF_OR_UNBD: "infeasible_or_unbounded",
    }
    reason = status_map.get(model.status, f"status_{model.status}")
    return {"objective": None, "status": reason}