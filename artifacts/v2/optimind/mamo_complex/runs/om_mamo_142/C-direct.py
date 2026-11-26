import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap_1_2 = params["cap_1_2"]
    cap_1_3 = params["cap_1_3"]
    cap_2_3 = params["cap_2_3"]
    cap_2_4 = params["cap_2_4"]
    cap_3_4 = params["cap_3_4"]

    # Edges and their capacities
    edges = [(1,2), (1,3), (2,3), (2,4), (3,4)]
    capacity = {
        (1,2): cap_1_2,
        (1,3): cap_1_3,
        (2,3): cap_2_3,
        (2,4): cap_2_4,
        (3,4): cap_3_4,
    }

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    f = model.addVars(edges, lb=0.0, name="f")

    # Capacity constraints
    for e in edges:
        model.addConstr(f[e] <= capacity[e], name=f"cap_{e[0]}_{e[1]}")

    # Flow conservation for intermediate nodes 2 and 3
    # Node 2: inflow from 1, outflow to 3 and 4
    model.addConstr(f[1,2] == f[2,3] + f[2,4], name="conservation_2")
    # Node 3: inflow from 1 and 2, outflow to 4
    model.addConstr(f[1,3] + f[2,3] == f[3,4], name="conservation_3")

    # Objective: maximize total flow into node 4
    model.setObjective(f[2,4] + f[3,4], GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}