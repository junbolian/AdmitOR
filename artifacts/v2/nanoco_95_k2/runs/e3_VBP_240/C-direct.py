import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_impressions = params["capacity_impressions"]
    capacity_cost = params["capacity_cost"]
    demand_impressions = params["demand_impressions"]
    demand_cost = params["demand_cost"]

    num_items = 9
    num_dims = 2
    capacities = [capacity_impressions, capacity_cost]
    demands = [[demand_impressions[i], demand_cost[i]] for i in range(num_items)]

    model = gp.Model("slot_allocation")
    model.Params.OutputFlag = 0

    y = model.addVars(num_items, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_items, num_items, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(y[j] for j in range(num_items)), GRB.MINIMIZE)

    for i in range(num_items):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_items)) == 1)

    for j in range(num_items):
        for d in range(num_dims):
            model.addConstr(
                gp.quicksum(x[i, j] * demands[i][d] for i in range(num_items))
                <= capacities[d] * y[j]
            )
        for i in range(num_items):
            model.addConstr(x[i, j] <= y[j])

    for j in range(num_items - 1):
        model.addConstr(y[j] >= y[j + 1])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}