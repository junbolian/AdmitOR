import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_stock = params["initial_stock"]
    required_supplies = params["required_supplies"]
    transfer_costs = params["transfer_costs"]

    n = len(initial_stock)
    hospitals = list(range(n))

    # Build list of (i, j) pairs from transfer_costs keys
    # transfer_costs is indexed by ordered pairs (i, j) where i != j
    # Determine pairs: assume transfer_costs is a dict with keys (i,j) or a 2D list/dict
    # We'll handle both dict-of-dict and flat dict with tuple keys

    # Normalize transfer_costs to a dict with (i,j) tuple keys
    cost = {}
    if isinstance(transfer_costs, dict):
        for key, val in transfer_costs.items():
            if isinstance(key, (list, tuple)) and len(key) == 2:
                cost[(int(key[0]), int(key[1]))] = val
            elif isinstance(key, str):
                # e.g. "0,1" or "(0,1)"
                cleaned = key.strip("() ")
                parts = cleaned.split(",")
                cost[(int(parts[0].strip()), int(parts[1].strip()))] = val
    elif isinstance(transfer_costs, (list, tuple)):
        # 2D list
        for i in range(len(transfer_costs)):
            for j in range(len(transfer_costs[i])):
                if i != j:
                    cost[(i, j)] = transfer_costs[i][j]

    pairs = list(cost.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units transferred from hospital i to hospital j
    x = model.addVars(pairs, lb=0.0, name="x")

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in pairs),
        GRB.MINIMIZE
    )

    # Flow balance: for each hospital h,
    # initial_stock[h] + inflow[h] - outflow[h] >= required_supplies[h]
    for h in hospitals:
        inflow = gp.quicksum(x[i, j] for (i, j) in pairs if j == h)
        outflow = gp.quicksum(x[i, j] for (i, j) in pairs if i == h)
        model.addConstr(
            initial_stock[h] + inflow - outflow >= required_supplies[h],
            name=f"balance_{h}"
        )

    # Cannot send more than available net supply out of a hospital
    # (non-negativity of remaining stock)
    for h in hospitals:
        inflow = gp.quicksum(x[i, j] for (i, j) in pairs if j == h)
        outflow = gp.quicksum(x[i, j] for (i, j) in pairs if i == h)
        model.addConstr(
            initial_stock[h] + inflow - outflow >= 0,
            name=f"nonneg_stock_{h}"
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