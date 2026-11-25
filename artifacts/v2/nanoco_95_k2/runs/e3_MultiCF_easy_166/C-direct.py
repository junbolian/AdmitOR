import gurobipy as gp
from gurobipy import GRB


def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_costs = params["arc_costs"]
    commodity_sources = params["commodity_sources"]
    commodity_sinks = params["commodity_sinks"]
    commodity_demands = params["commodity_demands"]

    num_nodes = 10
    num_commodities = 2

    arcs = [
        (0, 1), (1, 0), (0, 4), (4, 0), (1, 2), (2, 1),
        (1, 5), (5, 1), (2, 3), (3, 2), (2, 6), (6, 2),
        (3, 4), (4, 3), (3, 9), (9, 3), (4, 5), (5, 4),
        (4, 6), (6, 4), (5, 6), (6, 5), (5, 7), (7, 5),
        (6, 7), (7, 6), (7, 8), (8, 7), (8, 9), (9, 8),
    ]

    arc_index = {a: i for i, a in enumerate(arcs)}
    out_arcs = {n: [] for n in range(num_nodes)}
    in_arcs = {n: [] for n in range(num_nodes)}
    for (i, j) in arcs:
        out_arcs[i].append((i, j))
        in_arcs[j].append((i, j))

    model = gp.Model("multi_commodity_flow")
    model.Params.OutputFlag = 0

    x = {}
    for k in range(num_commodities):
        for a in arcs:
            x[k, a] = model.addVar(
                lb=0.0,
                ub=arc_capacities[arc_index[a]],
                obj=arc_costs[arc_index[a]],
                name=f"x_{k}_{a[0]}_{a[1]}",
            )

    model.ModelSense = GRB.MINIMIZE

    for k in range(num_commodities):
        src = commodity_sources[k]
        snk = commodity_sinks[k]
        d = commodity_demands[k]
        for n in range(num_nodes):
            out_flow = gp.quicksum(x[k, a] for a in out_arcs[n])
            in_flow = gp.quicksum(x[k, a] for a in in_arcs[n])
            if n == src:
                model.addConstr(out_flow - in_flow == d, name=f"src_balance_{k}_{n}")
            elif n == snk:
                model.addConstr(out_flow - in_flow == -d, name=f"snk_balance_{k}_{n}")
            else:
                model.addConstr(out_flow - in_flow == 0, name=f"flow_balance_{k}_{n}")

    for a in arcs:
        model.addConstr(
            gp.quicksum(x[k, a] for k in range(num_commodities))
            <= arc_capacities[arc_index[a]],
            name=f"cap_{a[0]}_{a[1]}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}