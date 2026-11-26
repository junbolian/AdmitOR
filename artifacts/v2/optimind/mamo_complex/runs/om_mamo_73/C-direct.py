import gurobipy as gp
from gurobipy import GRB
import ast

def solve(params):
    capacity_raw = params["capacity"]

    # Normalize keys: support tuple keys or string representations like "(0, 1)"
    arcs = {}
    for key, cap in capacity_raw.items():
        if isinstance(key, tuple):
            i, j = int(key[0]), int(key[1])
        elif isinstance(key, str):
            parsed = ast.literal_eval(key)
            i, j = int(parsed[0]), int(parsed[1])
        else:
            continue
        if cap > 0:
            arcs[(i, j)] = float(cap)

    source = 0
    sink = 8
    nodes = list(range(9))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each arc
    flow = {}
    for (i, j), cap in arcs.items():
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap, name=f"flow_{i}_{j}")

    model.update()

    # Flow conservation constraints for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"balance_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}