import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model("facility_location")
    model.Params.OutputFlag = 0

    # y[i] = 1 if facility i is open
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from facility i to customer j
    x = model.addVars(facilities, customers, lb=0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * y[i] for i in facilities)
        + gp.quicksum(
            shipping_costs[i][j] * x[i, j] for i in facilities for j in customers
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: every customer's demand must be fully met
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for i in facilities) == demands[j],
            name=f"demand_{j}",
        )

    # Capacity + activation: total shipped from facility i cannot exceed its capacity,
    # and if facility i is closed (y[i]=0) no shipments are allowed
    for i in facilities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in customers) <= capacities[i] * y[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}