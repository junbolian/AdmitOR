import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply_demand = params["supply_demand"]
    costs = params["costs"]
    capacities = params["capacities"]

    n = len(supply_demand)

    # For city i, destinations are all k in 0..n-1 excluding i (ordered 0..5)
    dests = [[k for k in range(n) if k != i] for i in range(n)]

    model = gp.Model("transportation")
    model.modelSense = GRB.MINIMIZE

    # Decision variables: x[i, j] = flow from city i to city j
    x = {}
    for i in range(n):
        for pos, j in enumerate(dests[i]):
            x[i, j] = model.addVar(
                lb=0,
                ub=capacities[i][pos],
                obj=costs[i][pos],
                name=f"x_{i}_{j}",
            )

    # Flow balance: flow_in - flow_out = supply_demand[k]
    # (positive demand => net inflow; negative => net outflow)
    for k in range(n):
        flow_in = gp.quicksum(x[i, k] for i in range(n) if i != k)
        flow_out = gp.quicksum(x[k, j] for j in dests[k])
        model.addConstr(flow_in - flow_out == supply_demand[k], name=f"balance_{k}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}