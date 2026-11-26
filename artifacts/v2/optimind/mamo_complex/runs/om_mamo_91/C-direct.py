import gurobipy as gp
from gurobipy import GRB

def solve(params):
    w_S_2 = params["w_S_2"]
    w_S_3 = params["w_S_3"]
    w_2_S = params["w_2_S"]
    w_2_4 = params["w_2_4"]
    w_2_3 = params["w_2_3"]
    w_3_S = params["w_3_S"]
    w_3_2 = params["w_3_2"]
    w_3_5 = params["w_3_5"]
    w_3_6 = params["w_3_6"]
    w_4_2 = params["w_4_2"]
    w_4_6 = params["w_4_6"]
    w_5_3 = params["w_5_3"]
    w_5_T = params["w_5_T"]
    w_6_3 = params["w_6_3"]
    w_6_4 = params["w_6_4"]
    w_6_7 = params["w_6_7"]
    w_7_6 = params["w_7_6"]
    w_7_T = params["w_7_T"]
    w_T_5 = params["w_T_5"]
    w_T_7 = params["w_T_7"]

    # Directed edges: (from, to, weight)
    edges = [
        ("S", "2", w_S_2),
        ("S", "3", w_S_3),
        ("2", "S", w_2_S),
        ("2", "4", w_2_4),
        ("2", "3", w_2_3),
        ("3", "S", w_3_S),
        ("3", "2", w_3_2),
        ("3", "5", w_3_5),
        ("3", "6", w_3_6),
        ("4", "2", w_4_2),
        ("4", "6", w_4_6),
        ("5", "3", w_5_3),
        ("5", "T", w_5_T),
        ("6", "3", w_6_3),
        ("6", "4", w_6_4),
        ("6", "7", w_6_7),
        ("7", "6", w_7_6),
        ("7", "T", w_7_T),
        ("T", "5", w_T_5),
        ("T", "7", w_T_7),
    ]

    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]
    source = "S"
    sink = "T"

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if edge is on the path
    x = {}
    for (i, j, w) in edges:
        x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(w * x[(i, j)] for (i, j, w) in edges),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    edge_dict = {(i, j): w for (i, j, w) in edges}

    for node in nodes:
        outflow = gp.quicksum(x[(i, j)] for (i, j, w) in edges if i == node)
        inflow = gp.quicksum(x[(i, j)] for (i, j, w) in edges if j == node)

        if node == source:
            model.addConstr(outflow - inflow == 1, name=f"flow_{node}")
        elif node == sink:
            model.addConstr(outflow - inflow == -1, name=f"flow_{node}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"flow_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}