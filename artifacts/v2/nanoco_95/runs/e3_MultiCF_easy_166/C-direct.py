import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]

    arcs = [
        (0,1),(1,0),(0,4),(4,0),(1,2),(2,1),(1,5),(5,1),
        (2,3),(3,2),(2,6),(6,2),(3,4),(4,3),(3,9),(9,3),
        (4,5),(5,4),(4,6),(6,4),(5,6),(6,5),(5,7),(7,5),
        (6,7),(7,6),(7,8),(8,7),(8,9),(9,8)
    ]

    # commodity definitions: (source, sink, demand)
    commodity_specs = [
        (1, 7, commodity_demand[0]),
        (0, 4, commodity_demand[1]),
    ]

    # build adjacency structures
    # out_arcs[node] = list of arc indices where arc[i][0] == node
    # in_arcs[node]  = list of arc indices where arc[i][1] == node
    out_arcs = {n: [] for n in range(num_nodes)}
    in_arcs  = {n: [] for n in range(num_nodes)}
    for idx, (u, v) in enumerate(arcs):
        out_arcs[u].append(idx)
        in_arcs[v].append(idx)

    model = gp.Model("mcf")
    model.setParam("OutputFlag", 0)

    # flow variables: x[k][a] = flow of commodity k on arc a
    x = {}
    for k in range(num_commodities):
        for a in range(num_arcs):
            x[k, a] = model.addVar(lb=0.0, name=f"x_{k}_{a}")

    model.update()

    # objective: minimize total cost
    model.setObjective(
        gp.quicksum(arc_cost[a] * x[k, a]
                    for k in range(num_commodities)
                    for a in range(num_arcs)),
        GRB.MINIMIZE
    )

    # flow conservation constraints
    for k in range(num_commodities):
        src, snk, demand = commodity_specs[k]
        for n in range(num_nodes):
            outflow = gp.quicksum(x[k, a] for a in out_arcs[n])
            inflow  = gp.quicksum(x[k, a] for a in in_arcs[n])
            if n == src:
                model.addConstr(outflow - inflow == demand, name=f"balance_{k}_{n}")
            elif n == snk:
                model.addConstr(inflow - outflow == demand, name=f"balance_{k}_{n}")
            else:
                model.addConstr(outflow - inflow == 0, name=f"balance_{k}_{n}")

    # capacity constraints (shared across commodities)
    for a in range(num_arcs):
        model.addConstr(
            gp.quicksum(x[k, a] for k in range(num_commodities)) <= arc_capacity[a],
            name=f"cap_{a}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}