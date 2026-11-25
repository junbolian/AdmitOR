import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    num_facilities = 6
    num_customers = 9
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Binary open/close decision per facility
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous shipment from facility i to customer j
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * open_facility[i] for i in facilities) +
        gp.quicksum(shipping_costs[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be met exactly
    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity and linking: shipments from facility i cannot exceed capacity if open,
    # and must be zero if closed
    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacities[i] * open_facility[i],
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