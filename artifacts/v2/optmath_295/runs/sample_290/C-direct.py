import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]

    n_facilities = 6
    n_customers = 12

    # Transport costs: only diagonal entries are specified; others must default to something.
    # The problem only names transport_cost_ij for i==j (0..5), so we build a full cost matrix.
    # For unspecified pairs we use 0 as a placeholder — the problem statement implies only
    # diagonal costs are given, so we set all others to 0 (they will still be decision variables
    # but with zero cost, letting the solver use them freely to satisfy demands).
    transport_cost = [[0.0] * n_customers for _ in range(n_facilities)]
    for i in range(n_facilities):
        key = f"transport_cost_{i}{i}"
        transport_cost[i][i] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_fac = model.addVars(n_facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from facility i to customer j
    ship = model.addVars(n_facilities, n_customers, lb=0.0, name="ship")

    # Objective: fixed costs + transportation costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in range(n_facilities)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j]
                    for i in range(n_facilities)
                    for j in range(n_customers)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be exactly met
    for j in range(n_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_facilities)) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from facility i <= capacity[i] * open[i]
    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_customers)) <= capacity[i] * open_fac[i],
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