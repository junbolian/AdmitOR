import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)

    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility j
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from facility j to customer i
    ship = model.addVars(customers, facilities, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[j] * open_facility[j] for j in facilities)
        + gp.quicksum(
            shipping_costs[i][j] * ship[i, j]
            for i in customers
            for j in facilities
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: each customer's demand must be exactly met
    for i in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in facilities) == demands[i],
            name=f"demand_{i}",
        )

    # Capacity limits: shipments from an open facility cannot exceed its capacity
    for j in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in customers) <= capacities[j] * open_facility[j],
            name=f"capacity_{j}",
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