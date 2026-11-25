import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_hubs = 15

    raw_costs = params["hub_activation_costs"]
    if isinstance(raw_costs, dict):
        try:
            costs = [raw_costs[k] for k in range(1, n_hubs + 1)]
        except KeyError:
            costs = [raw_costs[str(k)] for k in range(1, n_hubs + 1)]
    else:
        costs = list(raw_costs)

    if len(costs) != n_hubs:
        raise ValueError("hub_activation_costs must contain exactly 15 entries")
    cost_values = [float(c) for c in costs]

    routes = [
        [2, 3, 4, 7, 11, 13],
        [10, 12, 15],
        [1, 5, 6, 8, 11, 12, 13, 14],
        [2, 3, 4, 6, 7, 10, 12, 14],
        [1, 2, 3, 10, 13],
        [1, 2, 3, 6, 8, 10, 11, 12, 14],
        [3, 4, 5, 7, 8, 10, 11, 13, 14],
        [1, 2, 3, 7, 9, 12, 13],
        [1, 4, 7, 10, 12, 13, 14],
        [1, 3, 4, 5, 7, 10, 11, 13, 14, 15],
        [1, 4, 7, 9, 13, 14],
        [3, 4, 6, 8, 10, 11, 12, 13, 14, 15],
        [1, 2, 4, 5, 7, 11, 13, 14],
        [1, 4, 5, 6, 9, 12, 14, 15],
        [2, 6, 7, 12, 13, 14],
        [1, 4, 8, 11, 12, 14, 15],
    ]

    model = gp.Model("hub_activation")
    model.setParam("OutputFlag", 0)

    hub_open = model.addVars(n_hubs, vtype=GRB.BINARY, name="hub_open")
    model.setObjective(
        gp.quicksum(cost_values[i] * hub_open[i] for i in range(n_hubs)),
        GRB.MINIMIZE,
    )

    for r, hubs in enumerate(routes, start=1):
        model.addConstr(
            gp.quicksum(hub_open[h - 1] for h in hubs) >= 1,
            name=f"route_coverage_{r}",
        )

    model.optimize()

    if model.status == GRB.Status.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.Status.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"not_optimal_{model.status}"}