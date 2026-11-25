import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]            # 4 x 2
    demand = params["demand"]            # 5 x 2
    cost = params["cost"]                # 4 x 5 x 2
    transport_capacity = params["transport_capacity"]  # 4 x 5

    n_origins = len(supply)
    n_dest = len(demand)
    n_prod = len(supply[0])

    model = gp.Model("multi_commodity_supply_chain")
    model.Params.OutputFlag = 0

    x = model.addVars(
        n_origins, n_dest, n_prod,
        lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x"
    )

    # Supply limits at each origin
    for i in range(n_origins):
        for p in range(n_prod):
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in range(n_dest)) <= supply[i][p],
                name=f"supply_{i}_{p}"
            )

    # Demand requirements at each destination
    for j in range(n_dest):
        for p in range(n_prod):
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in range(n_origins)) >= demand[j][p],
                name=f"demand_{j}_{p}"
            )

    # Combined transport capacity per origin-destination pair
    for i in range(n_origins):
        for j in range(n_dest):
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in range(n_prod)) <= transport_capacity[i][j],
                name=f"cap_{i}_{j}"
            )

    model.setObjective(
        gp.quicksum(
            cost[i][j][p] * x[i, j, p]
            for i in range(n_origins)
            for j in range(n_dest)
            for p in range(n_prod)
        ),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed: status {model.Status}"}