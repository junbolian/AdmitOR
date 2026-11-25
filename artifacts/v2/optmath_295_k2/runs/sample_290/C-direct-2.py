import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]        # list of length num_facilities
    capacity = params["capacity"]            # list of length num_facilities
    demand = params["demand"]                # list of length num_customers
    transport_cost = params["transport_cost"] # dict keyed by (i,j) or list-of-lists or flat list
    num_facilities = params["num_facilities"] # int
    num_customers = params["num_customers"]  # int

    F = range(num_facilities)
    C = range(num_customers)

    # Normalize transport_cost to a callable tc(i, j)
    if isinstance(transport_cost, dict):
        # Keys may be (i, j) tuples or "i,j" strings
        sample_key = next(iter(transport_cost))
        if isinstance(sample_key, (tuple, list)):
            def tc(i, j):
                return transport_cost[(i, j)]
        else:
            # Try string keys like "0,1"
            def tc(i, j):
                return transport_cost[f"{i},{j}"]
    elif isinstance(transport_cost, (list, tuple)):
        first = transport_cost[0]
        if isinstance(first, (list, tuple)):
            # 2D list
            def tc(i, j):
                return transport_cost[i][j]
        else:
            # Flat list, row-major: index = i * num_customers + j
            def tc(i, j):
                return transport_cost[i * num_customers + j]
    else:
        raise ValueError(f"Unsupported transport_cost type: {type(transport_cost)}")

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if facility i is open
    y = model.addVars(F, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from facility i to customer j
    x = model.addVars(F, C, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize fixed costs + transportation costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in F) +
        gp.quicksum(tc(i, j) * x[i, j] for i in F for j in C),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be exactly met
    for j in C:
        model.addConstr(
            gp.quicksum(x[i, j] for i in F) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from facility i <= capacity[i] if open, else 0
    for i in F:
        model.addConstr(
            gp.quicksum(x[i, j] for j in C) <= capacity[i] * y[i],
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