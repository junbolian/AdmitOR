import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weeks = list(range(1, 8))
    n = len(weeks)

    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    capacity = params["capacity"]
    resource_A = params["resource_A"]
    resource_B = params["resource_B"]
    limit_A = params["limit_A"]
    limit_B = params["limit_B"]

    model = gp.Model("production_inventory")
    model.Params.OutputFlag = 0

    x_A = model.addVars(weeks, lb=0, vtype=GRB.CONTINUOUS, name="x_A")
    x_B = model.addVars(weeks, lb=0, vtype=GRB.CONTINUOUS, name="x_B")
    I_A = model.addVars(weeks, lb=0, vtype=GRB.CONTINUOUS, name="I_A")
    I_B = model.addVars(weeks, lb=0, vtype=GRB.CONTINUOUS, name="I_B")
    y_A = model.addVars(weeks, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(weeks, vtype=GRB.BINARY, name="y_B")

    model.setObjective(
        gp.quicksum(prod_cost_A[i] * x_A[weeks[i]] + prod_cost_B[i] * x_B[weeks[i]] for i in range(n))
        + gp.quicksum(setup_cost_A[i] * y_A[weeks[i]] + setup_cost_B[i] * y_B[weeks[i]] for i in range(n))
        + gp.quicksum(hold_cost_A[i] * I_A[weeks[i]] + hold_cost_B[i] * I_B[weeks[i]] for i in range(n)),
        GRB.MINIMIZE,
    )

    for i in range(n):
        t = weeks[i]
        if i == 0:
            model.addConstr(I_A[t] == x_A[t] - demand_A[i])
            model.addConstr(I_B[t] == x_B[t] - demand_B[i])
        else:
            prev = weeks[i - 1]
            model.addConstr(I_A[t] == I_A[prev] + x_A[t] - demand_A[i])
            model.addConstr(I_B[t] == I_B[prev] + x_B[t] - demand_B[i])

    for i in range(n):
        t = weeks[i]
        model.addConstr(resource_A * x_A[t] + resource_B * x_B[t] <= capacity[i])
        model.addConstr(x_A[t] <= limit_A[i] * y_A[t])
        model.addConstr(x_B[t] <= limit_B[i] * y_B[t])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "not_optimal"}