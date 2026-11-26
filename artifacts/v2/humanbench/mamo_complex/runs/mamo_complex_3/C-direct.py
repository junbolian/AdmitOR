import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]      # list of length 9
    transport_costs = params["transport_costs"]  # list of lists, possibly partial per row
    demands = params["demands"]                  # list of length 7
    capacities = params["capacities"]            # list of length 9

    num_dc = 9
    num_stores = 7

    DCs = range(num_dc)
    Stores = range(num_stores)

    # Build a safe transport cost lookup; missing entries default to 0
    def tc(i, j):
        row = transport_costs[i] if i < len(transport_costs) else []
        if isinstance(row, dict):
            return row.get(j, 0)
        return row[j] if j < len(row) else 0

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if distribution center i is opened
    y = model.addVars(DCs, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from DC i to store j
    x = model.addVars(DCs, Stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in DCs) +
        gp.quicksum(tc(i, j) * x[i, j] for i in DCs for j in Stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in Stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in DCs) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipments from DC i cannot exceed capacity if opened
    for i in DCs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in Stores) <= capacities[i] * y[i],
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