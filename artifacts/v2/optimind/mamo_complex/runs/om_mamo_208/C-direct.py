import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap = {
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 4): params["capacity_3_4"],
    }

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(cap.keys(), lb=0.0, name="flow")

    # Capacity constraints
    for edge, c in cap.items():
        model.addConstr(flow[edge] <= c, name=f"cap_{edge[0]}_{edge[1]}")

    # Flow conservation for intermediate nodes 2 and 3
    # Node 2: inflow = outflow
    model.addConstr(
        flow[1, 2] == flow[2, 3] + flow[2, 4],
        name="conservation_2"
    )
    # Node 3: inflow = outflow
    model.addConstr(
        flow[1, 3] + flow[2, 3] == flow[3, 4],
        name="conservation_3"
    )

    # Maximize total flow into node 4
    model.setObjective(flow[2, 4] + flow[3, 4], GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}