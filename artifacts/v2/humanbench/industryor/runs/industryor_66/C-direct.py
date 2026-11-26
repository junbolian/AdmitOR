import gurobipy as gp
from gurobipy import GRB

def solve(params):
    route_cost = params["route_cost"]
    r = params["route_capacity_r"]

    # Accept coverage matrix under various key names
    if "route_coverage" in params:
        route_coverage = params["route_coverage"]
    elif "coverage" in params:
        route_coverage = params["coverage"]
    elif "a" in params:
        route_coverage = params["a"]
    else:
        return {"objective": None, "status": "missing coverage matrix"}

    n = len(route_cost)
    m = len(route_coverage)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = 1 if route j is selected
    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(route_cost[j] * x[j] for j in range(n)),
        GRB.MINIMIZE
    )

    # Coverage constraint: every sales location i must be covered by at least one selected route
    for i in range(m):
        model.addConstr(
            gp.quicksum(route_coverage[i][j] * x[j] for j in range(n)) >= 1,
            name=f"cover_{i}"
        )

    # Capacity constraint: each selected route j covers at most r distinct sales locations
    for j in range(n):
        locations_on_route = sum(route_coverage[i][j] for i in range(m))
        if locations_on_route > r:
            # This route violates capacity; force it to 0
            model.addConstr(x[j] == 0, name=f"infeasible_route_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}