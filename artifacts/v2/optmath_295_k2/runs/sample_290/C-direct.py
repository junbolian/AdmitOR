import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    num_facilities = params["num_facilities"]
    num_customers = params["num_customers"]

    facilities = range(num_facilities)
    customers = range(num_customers)

    # Normalize transport_cost into a callable tc(i, j)
    # It may be: a 2D list, a flat 1D list (diagonal only), or a dict with (i,j) or "i,j" keys
    def get_tc(i, j):
        if isinstance(transport_cost, dict):
            # Try tuple key first, then string key
            if (i, j) in transport_cost:
                return transport_cost[(i, j)]
            key_str = f"{i},{j}"
            if key_str in transport_cost:
                return transport_cost[key_str]
            # Fallback: diagonal value if available, else large number
            if (i, i) in transport_cost:
                return transport_cost[(i, i)]
            return 999
        elif isinstance(transport_cost, list):
            if len(transport_cost) == 0:
                return 999
            first = transport_cost[0]
            if isinstance(first, list):
                # 2D list
                return transport_cost[i][j]
            else:
                # 1D list: treat as diagonal (transport_cost[i] = cost for facility i)
                # For off-diagonal, use the facility's diagonal cost as proxy
                if i < len(transport_cost):
                    return transport_cost[i]
                return 999
        else:
            return 999

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if facility i is opened
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")

    # x[i, j] = units shipped from facility i to customer j
    x = model.addVars(facilities, customers, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize fixed costs + transportation costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in facilities) +
        gp.quicksum(get_tc(i, j) * x[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be exactly met
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipped from facility i <= capacity[i] * y[i]
    for i in facilities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in customers) <= capacity[i] * y[i],
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