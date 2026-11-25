import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_demand = params["capacity_demand"]
    aircraft_availability = params["aircraft_availability"]
    capacity_contribution = params["capacity_contribution"]
    assignment_cost = params["assignment_cost"]

    num_aircraft = 7
    num_routes = 6
    aircraft_types = range(num_aircraft)
    routes = range(num_routes)

    def seq_get(container, idx, prefix=None):
        """Get item by integer index from a list, tuple, or dict with int/str keys."""
        if isinstance(container, (list, tuple)):
            return container[idx]
        if isinstance(container, dict):
            if idx in container:
                return container[idx]
            if str(idx) in container:
                return container[str(idx)]
            if prefix is not None:
                key = f"{prefix}_{idx}"
                if key in container:
                    return container[key]
        raise KeyError(f"Cannot find index {idx} in {type(container)}")

    def get_demand(j):
        return seq_get(capacity_demand, j, "route")

    def get_avail(i):
        return seq_get(aircraft_availability, i, "aircraft")

    def get_cap(i, j):
        row = seq_get(capacity_contribution, i, "aircraft")
        return seq_get(row, j, "route")

    def get_cost(i, j):
        row = seq_get(assignment_cost, i, "aircraft")
        return seq_get(row, j, "route")

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_aircraft, num_routes, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(
        gp.quicksum(
            get_cost(i, j) * x[i, j]
            for i in aircraft_types
            for j in routes
        ),
        GRB.MINIMIZE
    )

    for j in routes:
        model.addConstr(
            gp.quicksum(get_cap(i, j) * x[i, j] for i in aircraft_types)
            >= get_demand(j),
            name=f"cap_{j}"
        )

    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= get_avail(i),
            name=f"avail_{i}"
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