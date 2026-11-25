import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_weights = params["edge_weights"]
    station_capacities = params["station_capacities"]

    edges = [
        (0, 6), (0, 8), (1, 3), (1, 6), (1, 7), (1, 9),
        (2, 6), (2, 8), (2, 9), (3, 7), (4, 5), (4, 7),
        (4, 8), (4, 9), (5, 6), (5, 9), (6, 8)
    ]

    n_edges = len(edges)
    n_stations = 10

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_edges, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(edge_weights[i] * x[i] for i in range(n_edges)),
        GRB.MAXIMIZE
    )

    for s in range(n_stations):
        incident = [i for i, (u, v) in enumerate(edges) if u == s or v == s]
        if incident:
            model.addConstr(
                gp.quicksum(x[i] for i in incident) <= station_capacities[s],
                name=f"cap_{s}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}