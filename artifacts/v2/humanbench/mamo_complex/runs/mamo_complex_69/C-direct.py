import gurobipy as gp
from gurobipy import GRB


def _get_transport_costs(params):
    # Try common key names the harness may use for the per-unit transport cost matrix.
    for key in ("transport_costs", "transportation_costs", "transport_cost",
                "shipping_costs", "cost_matrix", "costs", "c"):
        if key in params:
            return params[key]
    raise KeyError("transport costs matrix not found in params")


def solve(params):
    opening_costs = params["opening_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    transport_costs = _get_transport_costs(params)

    num_centers = len(opening_costs)
    num_stores = len(demands)

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if distribution center i is opened
    y = model.addVars(num_centers, vtype=GRB.BINARY, name="open")
    # x[i,j] = units shipped from center i to store j
    x = model.addVars(num_centers, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in range(num_centers))
        + gp.quicksum(
            transport_costs[i][j] * x[i, j]
            for i in range(num_centers)
            for j in range(num_stores)
        ),
        GRB.MINIMIZE,
    )

    # Demand constraints: each store's demand must be met exactly
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_centers)) == demands[j],
            name=f"demand_{j}",
        )

    # Capacity constraints: shipments from a center only if open, within capacity
    for i in range(num_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacities[i] * y[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"solver_status_{status}"}