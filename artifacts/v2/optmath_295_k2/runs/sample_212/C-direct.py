import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_budget = params["resource_budget"]
    production_capacities = params["production_capacities"]

    n = 43  # number of items (structural constant)

    model = gp.Model("manufacturing_resource_allocation")
    model.Params.OutputFlag = 0

    # Production quantity per item, bounded by individual capacity, non-negative.
    x = model.addVars(
        n,
        lb=0.0,
        ub=[production_capacities[i] for i in range(n)],
        name="x",
    )

    # Shared critical resource constraint.
    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n)) <= resource_budget,
        name="resource_budget",
    )

    # Maximize total profit.
    model.setObjective(
        gp.quicksum(profit_margins[i] * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "inf_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"status_{model.status}"}