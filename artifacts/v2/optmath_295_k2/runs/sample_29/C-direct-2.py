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

    # Binary variable: open facility i
    open_facility = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from facility i to customer j
    ship = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * open_facility[i] for i in facilities) +
        gp.quicksum(shipping_costs[i][j] * ship[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction: total shipped to each customer equals demand
    for j in customers:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity and activation: shipments from facility i cannot exceed capacity * open[i]
    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in customers) <= capacities[i] * open_facility[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}