import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_facility = model.addVars(num_facilities, vtype=GRB.BINARY, name="open")
    ship = model.addVars(num_facilities, num_customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_costs[i] * open_facility[i] for i in range(num_facilities)) +
        gp.quicksum(shipping_costs[i][j] * ship[i, j]
                    for i in range(num_facilities)
                    for j in range(num_customers)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: total shipped to each customer equals demand
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity and facility activation: shipments from facility i cannot exceed capacity * open[i]
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers)) <= capacities[i] * open_facility[i],
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