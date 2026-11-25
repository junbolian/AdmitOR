import gurobipy as gp
from gurobipy import GRB

def solve(params):
    vm_demands = params["vm_demands"]
    server_capacity = params["server_capacity"]

    n_vms = len(vm_demands)
    # Upper bound on servers needed: each VM on its own server
    n_servers = n_vms

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if VM i is assigned to server j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_servers)]
         for i in range(n_vms)]

    # y[j] = 1 if server j is powered on
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}")
         for j in range(n_servers)]

    # Objective: minimize number of powered-on servers
    model.setObjective(gp.quicksum(y[j] for j in range(n_servers)), GRB.MINIMIZE)

    # Each VM must be assigned to exactly one server
    for i in range(n_vms):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_servers)) == 1,
            name=f"assign_vm_{i}"
        )

    # Capacity constraint per server
    for j in range(n_servers):
        model.addConstr(
            gp.quicksum(vm_demands[i] * x[i][j] for i in range(n_vms)) <= server_capacity * y[j],
            name=f"capacity_{j}"
        )

    # Symmetry breaking: servers used in order
    for j in range(n_servers - 1):
        model.addConstr(y[j] >= y[j + 1], name=f"symmetry_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}