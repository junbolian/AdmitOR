import gurobipy as gp
from gurobipy import GRB

def solve(params):
    rack_power_cap = params["rack_power_capacity"]
    rack_cooling_cap = params["rack_cooling_capacity"]
    server_power = params["server_power_demand"]    # list of 10 values
    server_cooling = params["server_cooling_demand"]  # list of 10 values

    n_servers = 10
    # Upper bound on racks needed: at most one per server
    n_racks = n_servers

    servers = range(n_servers)
    racks = range(n_racks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if rack j is powered on
    y = model.addVars(racks, vtype=GRB.BINARY, name="y")

    # x[i,j] = 1 if server i is assigned to rack j
    x = model.addVars(servers, racks, vtype=GRB.BINARY, name="x")

    # Objective: minimize number of active racks
    model.setObjective(gp.quicksum(y[j] for j in racks), GRB.MINIMIZE)

    # Each server assigned to exactly one rack
    for i in servers:
        model.addConstr(gp.quicksum(x[i, j] for j in racks) == 1, name=f"assign_{i}")

    # Power capacity per rack
    for j in racks:
        model.addConstr(
            gp.quicksum(server_power[i] * x[i, j] for i in servers) <= rack_power_cap * y[j],
            name=f"power_{j}"
        )

    # Cooling capacity per rack
    for j in racks:
        model.addConstr(
            gp.quicksum(server_cooling[i] * x[i, j] for i in servers) <= rack_cooling_cap * y[j],
            name=f"cooling_{j}"
        )

    # Symmetry breaking: rack j can only be used if rack j-1 is used
    for j in range(1, n_racks):
        model.addConstr(y[j] <= y[j - 1], name=f"sym_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}