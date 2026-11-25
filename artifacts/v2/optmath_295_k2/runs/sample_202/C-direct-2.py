import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_facilities = 6
    num_customers = 9

    fixed_costs = [params[f"fixed_cost_{i}"] for i in range(num_facilities)]
    demands = [params[f"demand_{j}"] for j in range(num_customers)]
    capacities = [params[f"capacity_{i}"] for i in range(num_facilities)]
    shipping_costs = [
        [params[f"shipping_cost_{i}_{j}"] for j in range(num_customers)]
        for i in range(num_facilities)
    ]

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Binary open/close decision for each facility
    open_facility = model.addVars(num_facilities, vtype=GRB.BINARY, name="open")

    # Continuous shipment from facility i to customer j
    ship = model.addVars(num_facilities, num_customers, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * open_facility[i] for i in range(num_facilities))
        + gp.quicksum(
            shipping_costs[i][j] * ship[i, j]
            for i in range(num_facilities)
            for j in range(num_customers)
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: each customer's demand must be met exactly
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}",
        )

    # Capacity and linking: shipments from facility i cannot exceed capacity if open,
    # and must be zero if closed
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers))
            <= capacities[i] * open_facility[i],
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