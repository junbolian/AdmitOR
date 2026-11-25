import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]
    distance_matrix = params["distance_matrix"]

    num_clients = len(demand)
    num_facilities = len(distance_matrix[0])

    # Precompute coverage sets: for each client i, which facilities j can cover it
    can_cover = {
        i: [j for j in range(num_facilities) if distance_matrix[i][j] <= coverage_radius]
        for i in range(num_clients)
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if facility j is opened
    y = model.addVars(num_facilities, vtype=GRB.BINARY, name="y")
    # x[i] = 1 if client i is covered
    x = model.addVars(num_clients, vtype=GRB.BINARY, name="x")

    # Maximize total covered demand
    model.setObjective(
        gp.quicksum(demand[i] * x[i] for i in range(num_clients)),
        GRB.MAXIMIZE
    )

    # Exactly num_stations facilities opened
    model.addConstr(gp.quicksum(y[j] for j in range(num_facilities)) == num_stations, name="cardinality")

    # Client i can only be covered if at least one covering facility is open
    for i in range(num_clients):
        if can_cover[i]:
            model.addConstr(
                x[i] <= gp.quicksum(y[j] for j in can_cover[i]),
                name=f"cover_{i}"
            )
        else:
            # No facility can cover this client
            model.addConstr(x[i] == 0, name=f"cover_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}