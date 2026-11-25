import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cpu_capacity = params["cpu_capacity"]
    mem_capacity = params["mem_capacity"]
    cpu_demand = params["cpu_demand"]  # list of 10 values
    mem_demand = params["mem_demand"]  # list of 10 values

    n_vms = 10
    # Upper bound on servers needed: at most one per VM
    n_servers = n_vms

    vms = range(n_vms)
    servers = range(n_servers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if VM i is assigned to server j
    x = model.addVars(n_vms, n_servers, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if server j is active
    y = model.addVars(n_servers, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of active servers
    model.setObjective(gp.quicksum(y[j] for j in servers), GRB.MINIMIZE)

    # Each VM must be assigned to exactly one server
    for i in vms:
        model.addConstr(gp.quicksum(x[i, j] for j in servers) == 1, name=f"assign_{i}")

    # CPU capacity constraints per server
    for j in servers:
        model.addConstr(
            gp.quicksum(cpu_demand[i] * x[i, j] for i in vms) <= cpu_capacity * y[j],
            name=f"cpu_{j}"
        )

    # Memory capacity constraints per server
    for j in servers:
        model.addConstr(
            gp.quicksum(mem_demand[i] * x[i, j] for i in vms) <= mem_capacity * y[j],
            name=f"mem_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}