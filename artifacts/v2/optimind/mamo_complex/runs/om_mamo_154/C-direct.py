import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(capacities)          # 9
    n_stores = len(demands)              # 8
    total_demand = sum(demands[j] for j in range(n_stores))

    model = gp.Model("megamart")
    model.Params.OutputFlag = 0

    open_dc = model.addVars(n_centers, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS, lb=0, name="ship")

    model.setObjective(
        gp.quicksum(opening_costs[i] * open_dc[i] for i in range(n_centers))
        + gp.quicksum(transport_costs[i][j] * ship[i, j]
                      for i in range(n_centers) for j in range(n_stores)),
        GRB.MINIMIZE
    )

    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_centers)) == demands[j],
            name=f"demand_{j}"
        )

    for i in range(n_centers):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacities[i] * open_dc[i],
            name=f"capacity_{i}"
        )

    # feasibility sanity: total capacity of all centers must cover total demand
    if sum(capacities) < total_demand:
        return {"objective": None, "status": "infeasible"}

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed_{model.Status}"}