import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = 4
    n_outlets = 4

    model = gp.Model("supplyco_distribution")
    model.Params.OutputFlag = 0

    open_var = model.addVars(n_centers, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_centers, n_outlets, vtype=GRB.CONTINUOUS, lb=0, name="ship")

    # Meet demand at each outlet
    for j in range(n_outlets):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_centers)) == demands[j],
            name=f"demand_{j}",
        )

    # Capacity and linking: shipments only from open centers
    for i in range(n_centers):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_outlets)) <= capacities[i] * open_var[i],
            name=f"capacity_{i}",
        )

    model.setObjective(
        gp.quicksum(opening_costs[i] * open_var[i] for i in range(n_centers))
        + gp.quicksum(
            transport_costs[i][j] * ship[i, j]
            for i in range(n_centers)
            for j in range(n_outlets)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"failed: status {model.Status}"}