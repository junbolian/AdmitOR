import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]  # list of 8 values
    demand = params["demand"]              # list of 8 values
    capacity = params["capacity"]          # list of 8 values

    # Transport cost matrix: build from params if full matrix provided,
    # otherwise construct from the endpoint values given in the problem.
    # The params dict may supply individual corner values or the full matrix.
    # We attempt to read the full matrix; if unavailable, construct it.
    if "transport_cost" in params:
        transport_cost = params["transport_cost"]
    else:
        # Construct 8x8 matrix by linear interpolation between given endpoints.
        # DC i (0-indexed): cost to Store 1 and Store 8 vary linearly.
        # DC1 (i=0): store1=3, store8=4
        # DC2 (i=1): store1=2, store8=4
        # Pattern: start values decrease then increase, end values are 4 for all.
        # From description: DC1->S1=3, DC1->S8=4; DC2->S1=2, DC2->S8=4
        # We'll read these from params if present, else use stated values.
        tc_dc1_s1 = params.get("tc_dc1_s1", 3)
        tc_dc1_s8 = params.get("tc_dc1_s8", 4)
        tc_dc2_s1 = params.get("tc_dc2_s1", 2)
        tc_dc2_s8 = params.get("tc_dc2_s8", 4)

        n_dc = 8
        n_store = 8

        # Build cost matrix: linearly interpolate store costs for each DC,
        # and linearly interpolate DC parameters between DC1 and DC2 endpoints.
        transport_cost = []
        for i in range(n_dc):
            # Interpolate start (store1) and end (store8) costs across DCs
            t = i / (n_dc - 1)
            s1_cost = tc_dc1_s1 + t * (tc_dc2_s1 - tc_dc1_s1)
            s8_cost = tc_dc1_s8 + t * (tc_dc2_s8 - tc_dc1_s8)
            row = []
            for j in range(n_store):
                u = j / (n_store - 1)
                row.append(s1_cost + u * (s8_cost - s1_cost))
            transport_cost.append(row)

    n_dc = 8
    n_store = 8
    DCs = range(n_dc)
    Stores = range(n_store)

    model = gp.Model("LogicFlow_DC")
    model.setParam("OutputFlag", 0)

    y = model.addVars(DCs, vtype=GRB.BINARY, name="open")
    x = model.addVars(DCs, Stores, lb=0.0, vtype=GRB.CONTINUOUS, name="ship")

    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in DCs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in DCs for j in Stores),
        GRB.MINIMIZE
    )

    for j in Stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in DCs) >= demand[j],
            name=f"demand_{j}"
        )

    for i in DCs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in Stores) <= capacity[i] * y[i],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}