import gurobipy as gp
from gurobipy import GRB

def solve(params):
    service_cost = params["service_cost"]
    travel_cost = params["travel_cost"]

    nodes = list(range(6))

    # Required edges (undirected) - structural constants
    required_edges = [(0,3),(0,4),(1,4),(2,3),(2,5),(3,4),(4,5)]

    # service_cost may be a dict keyed by edge tuple or a list
    sc = {}
    if isinstance(service_cost, dict):
        for idx, e in enumerate(required_edges):
            key = e if e in service_cost else str(e)
            val = service_cost.get(key, service_cost.get(str(e), list(service_cost.values())[idx]))
            sc[e] = val
            sc[(e[1], e[0])] = val
    else:
        for idx, e in enumerate(required_edges):
            sc[e] = service_cost[idx]
            sc[(e[1], e[0])] = service_cost[idx]

    # travel_cost may be a 2D list or a flat list
    tc = {}
    if isinstance(travel_cost, (list, tuple)) and len(travel_cost) == 6 and isinstance(travel_cost[0], (list, tuple)):
        # 2D
        for i in nodes:
            for j in nodes:
                tc[(i,j)] = travel_cost[i][j]
    else:
        # flat row-major, length should be 36
        flat = list(travel_cost)
        for i in nodes:
            for j in nodes:
                tc[(i,j)] = flat[i*6 + j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Service traversal vars: for each required edge, two directions
    x = {}
    for e in required_edges:
        u, v = e
        x[(u,v)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{u}_{v}")
        x[(v,u)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{v}_{u}")

    # Deadhead vars: directed, between all node pairs
    dh = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                dh[(i,j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"d_{i}_{j}")

    # Each required edge serviced at least once
    for e in required_edges:
        u, v = e
        model.addConstr(x[(u,v)] + x[(v,u)] >= 1, name=f"req_{u}_{v}")

    # Flow conservation at each node
    for node in nodes:
        out_service = gp.quicksum(x[(u,v)] for (u,v) in x if u == node)
        in_service  = gp.quicksum(x[(u,v)] for (u,v) in x if v == node)
        out_dead    = gp.quicksum(dh[(node,j)] for j in nodes if j != node)
        in_dead     = gp.quicksum(dh[(i,node)] for i in nodes if i != node)
        model.addConstr(out_service + out_dead == in_service + in_dead, name=f"flow_{node}")

    # Objective
    obj = (
        gp.quicksum(x[(u,v)] * sc[(u,v)] for (u,v) in x)
        + gp.quicksum(dh[(i,j)] * tc[(i,j)] for (i,j) in dh)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}