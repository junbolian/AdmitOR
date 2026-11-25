import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # open[i] = 1 if facility i is opened
    open_fac = model.addVars(num_facilities, vtype=GRB.BINARY, name="open")
    # ship[i, j] = units shipped from facility i to customer j
    ship = model.addVars(num_facilities, num_customers, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * open_fac[i] for i in range(num_facilities))
        + gp.quicksum(
            shipping_costs[i][j] * ship[i, j]
            for i in range(num_facilities)
            for j in range(num_customers)
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: each customer's demand must be fully met
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}",
        )

    # Capacity limits and facility activation
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers))
            <= capacities[i] * open_fac[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}