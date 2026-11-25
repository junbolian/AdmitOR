import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    demand_commodity_1 = params["demand_commodity_1"]
    demand_commodity_2 = params["demand_commodity_2"]

    # Directed arcs in order
    arcs = [
        (0,1),(1,0),(0,5),(5,0),(0,7),(7,0),(0,8),(8,0),(0,9),(9,0),
        (1,2),(2,1),(2,3),(3,2),(2,9),(9,2),(3,4),(4,3),(4,5),(5,4),
        (5,6),(6,5),(6,7),(7,6),(6,9),(9,6),(7,8),(8,7),(8,9),(9,8)
    ]

    capacity = {arcs[i]: arc_capacity[i] for i in range(len(arcs))}
    cost = {arcs[i]: arc_cost[i] for i in range(len(arcs))}

    # Commodity definitions: (source, sink, demand)
    commodities = {
        1: (5, 4, demand_commodity_1),
        2: (3, 0, demand_commodity_2),
    }

    nodes = list(range(10))

    model = gp.Model("cold_chain")
    model.setParam("OutputFlag", 0)

    # Flow variables: x[k, i, j] = flow of commodity k on arc (i,j)
    x = {}
    for k in commodities:
        for (i, j) in arcs:
            x[k, i, j] = model.addVar(lb=0.0, name=f"x_{k}_{i}_{j}")

    model.update()

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[k, i, j] for k in commodities for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    for k, (src, snk, dem) in commodities.items():
        for n in nodes:
            out_flow = gp.quicksum(x[k, i, j] for (i, j) in arcs if i == n)
            in_flow = gp.quicksum(x[k, i, j] for (i, j) in arcs if j == n)
            if n == src:
                model.addConstr(out_flow - in_flow == dem, name=f"flow_src_{k}_{n}")
            elif n == snk:
                model.addConstr(in_flow - out_flow == dem, name=f"flow_snk_{k}_{n}")
            else:
                model.addConstr(out_flow - in_flow == 0, name=f"flow_con_{k}_{n}")

    # Shared capacity constraints
    for (i, j) in arcs:
        model.addConstr(
            gp.quicksum(x[k, i, j] for k in commodities) <= capacity[i, j],
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
        return {"objective": None, "status": f"status_{model.Status}"}