import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    demand_commodity1 = params["demand_commodity1"]
    demand_commodity2 = params["demand_commodity2"]

    # Directed arcs in the order matching the capacity/cost lists
    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),
        (1,2),(2,1),(1,7),(7,1),
        (2,3),(3,2),(2,6),(6,2),(2,7),(7,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5),(6,7),(7,6),(7,8),(8,7)
    ]

    # Build lookup dicts from arc tuple -> capacity/cost
    cap = {arcs[idx]: arc_capacity[idx] for idx in range(len(arcs))}
    cost = {arcs[idx]: arc_cost[idx] for idx in range(len(arcs))}

    # Commodities: k -> (source, sink, demand)
    commodities = {
        1: (3, 2, demand_commodity1),
        2: (6, 1, demand_commodity2),
    }

    nodes = list(range(9))

    model = gp.Model("multi_commodity_flow")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow[k, i, j] = flow of commodity k on arc (i,j)
    flow = {}
    for k in commodities:
        for (i, j) in arcs:
            flow[k, i, j] = model.addVar(lb=0.0, name=f"flow_{k}_{i}_{j}")

    model.update()

    # Objective: minimize total logistics cost
    model.setObjective(
        gp.quicksum(
            cost[i, j] * flow[k, i, j]
            for k in commodities
            for (i, j) in arcs
        ),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    for k, (src, snk, dem) in commodities.items():
        for nd in nodes:
            out_flow = gp.quicksum(flow[k, nd, j] for (i, j) in arcs if i == nd)
            in_flow  = gp.quicksum(flow[k, i, nd] for (i, j) in arcs if j == nd)
            if nd == src:
                model.addConstr(out_flow - in_flow == dem, name=f"balance_k{k}_n{nd}")
            elif nd == snk:
                model.addConstr(in_flow - out_flow == dem, name=f"balance_k{k}_n{nd}")
            else:
                model.addConstr(out_flow - in_flow == 0, name=f"balance_k{k}_n{nd}")

    # Shared capacity constraints
    for (i, j) in arcs:
        model.addConstr(
            gp.quicksum(flow[k, i, j] for k in commodities) <= cap[i, j],
            name=f"cap_{i}_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}