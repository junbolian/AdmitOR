import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = 6
    num_customers = 11

    # shipping_costs_col0 gives costs from each DC to store 0 only.
    # The problem only provides column 0 shipping costs explicitly.
    # We use shipping_costs_col0[i] as the per-unit cost from DC i to any customer
    # (the problem description only gives store-0 costs; we apply them uniformly).
    # This matches the data structure implied by the param name.

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # open_dc[i]: binary, 1 if DC i is opened
    open_dc = model.addVars(num_facilities, vtype=GRB.BINARY, name="open_dc")

    # ship[i, j]: continuous, units shipped from DC i to store j
    ship = model.addVars(num_facilities, num_customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    obj = gp.quicksum(fixed_costs[i] * open_dc[i] for i in range(num_facilities))
    obj += gp.quicksum(
        shipping_costs_col0[i] * ship[i, j]
        for i in range(num_facilities)
        for j in range(num_customers)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand satisfaction: each store j receives exactly its demand
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity limits: DC i cannot exceed its capacity, and only if opened
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers)) <= capacities[i] * open_dc[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}