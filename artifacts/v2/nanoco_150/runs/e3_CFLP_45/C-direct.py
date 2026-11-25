import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_costs = params["fixed_costs"]
    capacities = params["capacities"]
    demands = params["demands"]
    latency_matrix = params["latency_matrix"]

    n_facilities = len(fixed_costs)
    n_nodes = len(demands)

    model = gp.Model("edge_computing_facility_location")
    model.setParam("OutputFlag", 0)

    # Binary: open facility j
    open_vars = model.addVars(n_facilities, vtype=GRB.BINARY, name="open")

    # Binary: assign node i to facility j
    assign_vars = model.addVars(n_nodes, n_facilities, vtype=GRB.BINARY, name="assign")

    # Objective: fixed costs + latency penalties
    model.setObjective(
        gp.quicksum(fixed_costs[j] * open_vars[j] for j in range(n_facilities))
        + gp.quicksum(
            latency_matrix[i][j] * assign_vars[i, j]
            for i in range(n_nodes)
            for j in range(n_facilities)
        ),
        GRB.MINIMIZE,
    )

    # Each node assigned to exactly one facility
    for i in range(n_nodes):
        model.addConstr(
            gp.quicksum(assign_vars[i, j] for j in range(n_facilities)) == 1,
            name=f"single_source_{i}",
        )

    # Capacity constraints
    for j in range(n_facilities):
        model.addConstr(
            gp.quicksum(demands[i] * assign_vars[i, j] for i in range(n_nodes))
            <= capacities[j] * open_vars[j],
            name=f"capacity_{j}",
        )

    # Linking: can only assign to open facility
    for i in range(n_nodes):
        for j in range(n_facilities):
            model.addConstr(
                assign_vars[i, j] <= open_vars[j],
                name=f"link_{i}_{j}",
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