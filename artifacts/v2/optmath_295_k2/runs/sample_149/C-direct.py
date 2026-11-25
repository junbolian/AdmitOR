import gurobipy as gp
from gurobipy import GRB


def solve(params):
    T = 5
    periods = list(range(T))

    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    resource_use_A = params["resource_use_A"]
    resource_use_B = params["resource_use_B"]
    resource_capacity = params["resource_capacity"]
    max_prod_A = params["max_prod_A"]
    max_prod_B = params["max_prod_B"]

    model = gp.Model("lot_sizing")
    model.Params.OutputFlag = 0

    # Production quantities
    x_A = model.addVars(periods, lb=0, name="x_A")
    x_B = model.addVars(periods, lb=0, name="x_B")
    # Setup binaries
    y_A = model.addVars(periods, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(periods, vtype=GRB.BINARY, name="y_B")
    # Ending inventory
    inv_A = model.addVars(periods, lb=0, name="inv_A")
    inv_B = model.addVars(periods, lb=0, name="inv_B")

    # Inventory balance: cumulative production - cumulative demand = ending inventory
    for t in periods:
        model.addConstr(
            gp.quicksum(x_A[s] for s in range(t + 1)) - demand_A[t] == inv_A[t],
            name=f"balance_A_{t}",
        )
        model.addConstr(
            gp.quicksum(x_B[s] for s in range(t + 1)) - demand_B[t] == inv_B[t],
            name=f"balance_B_{t}",
        )

    # No inventory carried past the planning horizon
    model.addConstr(inv_A[T - 1] == 0, name="end_inv_A")
    model.addConstr(inv_B[T - 1] == 0, name="end_inv_B")

    # Setup linking (big-M): production requires setup; max production = remaining demand
    for t in periods:
        model.addConstr(x_A[t] <= max_prod_A[t] * y_A[t], name=f"setup_A_{t}")
        model.addConstr(x_B[t] <= max_prod_B[t] * y_B[t], name=f"setup_B_{t}")

    # Shared resource capacity per period
    for t in periods:
        model.addConstr(
            resource_use_A * x_A[t] + resource_use_B * x_B[t] <= resource_capacity[t],
            name=f"resource_{t}",
        )

    # Objective: production + setup + holding costs
    model.setObjective(
        gp.quicksum(
            prod_cost_A[t] * x_A[t]
            + setup_cost_A[t] * y_A[t]
            + hold_cost_A[t] * inv_A[t]
            for t in periods
        )
        + gp.quicksum(
            prod_cost_B[t] * x_B[t]
            + setup_cost_B[t] * y_B[t]
            + hold_cost_B[t] * inv_B[t]
            for t in periods
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}