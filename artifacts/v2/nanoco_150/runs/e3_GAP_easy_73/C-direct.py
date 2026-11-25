import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [
        params["capacity_T1"],
        params["capacity_T2"],
        params["capacity_T3"],
    ]
    usage = [
        params["usage_T1"],
        params["usage_T2"],
        params["usage_T3"],
    ]
    cost = [
        params["cost_T1"],
        params["cost_T2"],
        params["cost_T3"],
    ]

    num_towers = 3
    num_packets = 7
    towers = range(num_towers)
    packets = range(num_packets)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[t, p] = 1 if packet p is assigned to tower t
    x = model.addVars(towers, packets, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[t][p] * x[t, p] for t in towers for p in packets),
        GRB.MINIMIZE,
    )

    # Each packet assigned to exactly one tower
    for p in packets:
        model.addConstr(gp.quicksum(x[t, p] for t in towers) == 1, name=f"assign_p{p}")

    # Bandwidth capacity constraints
    for t in towers:
        model.addConstr(
            gp.quicksum(usage[t][p] * x[t, p] for p in packets) <= capacity[t],
            name=f"capacity_t{t}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}