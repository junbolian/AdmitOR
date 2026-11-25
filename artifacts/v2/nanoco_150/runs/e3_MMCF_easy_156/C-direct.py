import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    demands = params["demands"]

    # Directed arc list (30 arcs)
    arcs = [
        (0,1),(1,0),(0,4),(4,0),
        (1,2),(2,1),(1,5),(5,1),
        (2,3),(3,2),(2,6),(6,2),
        (3,4),(4,3),(3,9),(9,3),
        (4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5),(5,7),(7,5),
        (6,7),(7,6),(7,8),(8,7),
        (8,9),(9,8)
    ]

    num_arcs = len(arcs)
    num_nodes = 10

    # Commodities: (source, sink, demand)
    # commodity 0: node 1 -> node 7, demand = demands[0]
    # commodity 1: node 0 -> node 4, demand = demands[1]
    commodities = [
        (1, 7, demands[0]),
        (0, 4, demands[1]),
    ]
    num_commodities = len(commodities)

    cap = {arcs[i]: capacities[i] for i in range(num_arcs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[k][a] = flow of commodity k on arc a
    f = {}
    for k in range(num_commodities):
        for a in arcs:
            f[k, a] = model.addVar(lb=0.0, name=f"f_{k}_{a[0]}_{a[1]}")

    # Congestion variable (minimax)
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    for k in range(num_commodities):
        src, snk, dem = commodities[k]
        for nd in range(num_nodes):
            out_flow = gp.quicksum(f[k, a] for a in arcs if a[0] == nd)
            in_flow  = gp.quicksum(f[k, a] for a in arcs if a[1] == nd)
            if nd == src:
                model.addConstr(out_flow - in_flow == dem)
            elif nd == snk:
                model.addConstr(in_flow - out_flow == dem)
            else:
                model.addConstr(out_flow - in_flow == 0)

    # Capacity constraints and congestion definition
    for a in arcs:
        c = cap[a]
        total_flow = gp.quicksum(f[k, a] for k in range(num_commodities))
        # Capacity: total flow <= capacity
        model.addConstr(total_flow <= c)
        # Congestion: z >= total_flow / capacity
        model.addConstr(z >= total_flow / c)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}