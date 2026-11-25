import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    variable_cost = params["variable_cost"]

    num_facilities = len(fixed_cost)
    num_customers = len(demand)

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    y = model.addVars(num_facilities, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_facilities, num_customers, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in range(num_facilities))
        + gp.quicksum(
            variable_cost[i][j] * x[i, j]
            for i in range(num_facilities)
            for j in range(num_customers)
        ),
        GRB.MINIMIZE,
    )

    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demand[j],
            name=f"demand_{j}",
        )

    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_customers)) <= capacity[i] * y[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"status_{model.status}"}