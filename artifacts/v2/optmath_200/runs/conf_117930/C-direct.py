import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # Arc set (structural, not parametrized)
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 2), (1, 3),
    ]

    # Read all numeric quantities from params
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (0, 5): params["cost_0_5"],
        (0, 6): params["cost_0_6"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
    }
    supply0 = params["node_0_supply"]
    demand6 = params["node_6_demand"]

    model = gp.Model("logistics")

    # Binary decision variables for each arc
    x = {}
    for (i, j) in arcs:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"arc_{i}_{j}")

    model.update()

    # Flow balance constraints
    for n in range(7):
        out_flow = gp.quicksum(x[i, j] for (i, j) in arcs if i == n)
        in_flow = gp.quicksum(x[i, j] for (i, j) in arcs if j == n)
        if n == 0:
            # node_0: out - in = supply0
            model.addConstr(out_flow - in_flow == supply0, name=f"balance_{n}")
        elif n == 6:
            # node_6: in - out = demand6
            model.addConstr(in_flow - out_flow == demand6, name=f"balance_{n}")
        else:
            # intermediate nodes: in = out
            model.addConstr(in_flow - out_flow == 0, name=f"balance_{n}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}