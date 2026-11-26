import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_S_2 = params["edge_S_2"]
    edge_S_3 = params["edge_S_3"]
    edge_2_4 = params["edge_2_4"]
    edge_2_3 = params["edge_2_3"]
    edge_3_5 = params["edge_3_5"]
    edge_3_6 = params["edge_3_6"]
    edge_4_6 = params["edge_4_6"]
    edge_5_T = params["edge_5_T"]
    edge_6_7 = params["edge_6_7"]
    edge_7_T = params["edge_7_T"]

    # Directed edges with their weights (undirected graph => both directions)
    edges = {
        ("S", "2"): edge_S_2,
        ("2", "S"): edge_S_2,
        ("S", "3"): edge_S_3,
        ("3", "S"): edge_S_3,
        ("2", "4"): edge_2_4,
        ("4", "2"): edge_2_4,
        ("2", "3"): edge_2_3,
        ("3", "2"): edge_2_3,
        ("3", "5"): edge_3_5,
        ("5", "3"): edge_3_5,
        ("3", "6"): edge_3_6,
        ("6", "3"): edge_3_6,
        ("4", "6"): edge_4_6,
        ("6", "4"): edge_4_6,
        ("5", "T"): edge_5_T,
        ("T", "5"): edge_5_T,
        ("6", "7"): edge_6_7,
        ("7", "6"): edge_6_7,
        ("7", "T"): edge_7_T,
        ("T", "7"): edge_7_T,
    }

    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]
    source = "S"
    sink = "T"

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary flow variables on directed edges
    x = model.addVars(edges.keys(), vtype=GRB.BINARY, name="x")

    # Minimize total distance
    model.setObjective(
        gp.quicksum(edges[e] * x[e] for e in edges.keys()),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    for node in nodes:
        outflow = gp.quicksum(x[(i, j)] for (i, j) in edges.keys() if i == node)
        inflow = gp.quicksum(x[(i, j)] for (i, j) in edges.keys() if j == node)
        if node == source:
            model.addConstr(outflow - inflow == 1, name=f"flow_{node}")
        elif node == sink:
            model.addConstr(inflow - outflow == 1, name=f"flow_{node}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"flow_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}