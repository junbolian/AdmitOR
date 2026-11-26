import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    # supply/demand are lists ordered by district: index 0 = D1, ..., 3 = D4
    cost = {
        (0, 1): params["cost_1_to_2"],
        (0, 2): params["cost_1_to_3"],
        (0, 3): params["cost_1_to_4"],
        (1, 0): params["cost_2_to_1"],
        (1, 2): params["cost_2_to_3"],
        (1, 3): params["cost_2_to_4"],
        (2, 0): params["cost_3_to_1"],
        (2, 1): params["cost_3_to_2"],
        (2, 3): params["cost_3_to_4"],
        (3, 0): params["cost_4_to_1"],
        (3, 1): params["cost_4_to_2"],
        (3, 2): params["cost_4_to_3"],
    }

    districts = [0, 1, 2, 3]
    arcs = list(cost.keys())

    model = gp.Model("food_distribution")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, lb=0.0, name="x")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for i, j in arcs), GRB.MINIMIZE)

    for idx in districts:
        outflow = gp.quicksum(x[idx, j] for j in districts if (idx, j) in cost)
        inflow = gp.quicksum(x[j, idx] for j in districts if (j, idx) in cost)
        net_supply = supply[idx] - demand[idx]
        model.addConstr(outflow - inflow == net_supply, name=f"balance_{idx}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}