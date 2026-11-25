import gurobipy as gp
from gurobipy import GRB


def solve(params):
    demand = list(params["demand"])
    T = len(demand)

    fixed_setup_cost = list(params["fixed_setup_cost"])
    variable_production_cost = list(params["variable_production_cost"])
    inventory_holding_cost = list(params["inventory_holding_cost"])
    backlogging_cost = list(params["backlogging_cost"])

    production_capacity = params["production_capacity"]
    if isinstance(production_capacity, (int, float)):
        capacity = [float(production_capacity)] * T
    else:
        capacity = [float(c) for c in production_capacity]

    model = gp.Model("production_inventory_backlogging")
    model.Params.OutputFlag = 0

    produce = model.addVars(T, vtype=GRB.BINARY, name="produce")
    quantity = model.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="quantity")
    inventory = model.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="inventory")
    backlog = model.addVars(T, lb=0.0, vtype=GRB.CONTINUOUS, name="backlog")

    for t in range(T):
        model.addConstr(quantity[t] <= capacity[t] * produce[t], name=f"capacity_{t}")

    for t in range(T):
        prev_inventory = inventory[t - 1] if t > 0 else 0.0
        prev_backlog = backlog[t - 1] if t > 0 else 0.0

        # Balance: net stock carried in plus production minus demand
        # equals net stock carried out, where net stock = inventory - backlog.
        model.addConstr(
            prev_inventory + quantity[t] + backlog[t]
            == demand[t] + inventory[t] + prev_backlog,
            name=f"balance_{t}",
        )

    # No inventory or backlog at the end of the last period.
    model.addConstr(inventory[T - 1] == 0, name="final_inventory")
    model.addConstr(backlog[T - 1] == 0, name="final_backlog")

    model.setObjective(
        gp.quicksum(
            fixed_setup_cost[t] * produce[t]
            + variable_production_cost[t] * quantity[t]
            + inventory_holding_cost[t] * inventory[t]
            + backlogging_cost[t] * backlog[t]
            for t in range(T)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"failed_status_{model.status}"}