import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_demand = params["supply_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    n = 6
    # Build list of arcs (i, j) for i != j, in the order given
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j))

    # Map arc to index in the flat lists
    arc_index = {arc: idx for idx, arc in enumerate(arcs)}

    cost = {arc: cost_matrix[arc_index[arc]] for arc in arcs}
    capacity = {arc: capacity_matrix[arc_index[arc]] for arc in arcs}

    model = gp.Model("resource_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= capacity[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow balance constraints
    # supply_demand[i] > 0 means net supply, < 0 means net demand
    # outflow - inflow = supply_demand[i]
    for i in range(n):
        outflow = gp.quicksum(flow[(i, j)] for j in range(n) if i != j)
        inflow = gp.quicksum(flow[(j, i)] for j in range(n) if i != j)
        model.addConstr(outflow - inflow == supply_demand[i], name=f"balance_{i}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[arc] * flow[arc] for arc in arcs),
        GRB.MINIMIZE
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