import gurobipy as gp
from gurobipy import GRB


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]

    # Try both "cost" and "operational_cost" as possible keys
    if "cost" in params:
        cost = params["cost"]
    elif "operational_cost" in params:
        cost = params["operational_cost"]
    else:
        # Find whatever key contains cost-like data
        raise KeyError(f"No cost key found in params. Available keys: {list(params.keys())}")

    # Support both list-of-lists and dict-of-dicts structures
    def get_val(matrix, i, j, row_prefix="aircraft_", col_prefix="route_"):
        if isinstance(matrix, list):
            row = matrix[i]
            if isinstance(row, list):
                return row[j]
            elif isinstance(row, dict):
                key = f"{col_prefix}{j}"
                return row[key]
        elif isinstance(matrix, dict):
            row_key = f"{row_prefix}{i}"
            row = matrix[row_key]
            if isinstance(row, list):
                return row[j]
            elif isinstance(row, dict):
                col_key = f"{col_prefix}{j}"
                return row[col_key]
        raise ValueError(f"Unsupported matrix structure: {type(matrix)}")

    def get_scalar(vec, i, prefix="aircraft_"):
        if isinstance(vec, list):
            return vec[i]
        elif isinstance(vec, dict):
            key = f"{prefix}{i}"
            return vec[key]
        raise ValueError(f"Unsupported vector structure: {type(vec)}")

    def get_demand(vec, j, prefix="route_"):
        if isinstance(vec, list):
            return vec[j]
        elif isinstance(vec, dict):
            key = f"{prefix}{j}"
            return vec[key]
        raise ValueError(f"Unsupported vector structure: {type(vec)}")

    n_aircraft = len(availability)
    n_routes = len(demand)

    model = gp.Model("airline_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_aircraft):
        for j in range(n_routes):
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(
            get_val(cost, i, j) * x[i, j]
            for i in range(n_aircraft)
            for j in range(n_routes)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= get_scalar(availability, i),
            name=f"avail_{i}",
        )

    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(get_val(capacity, i, j) * x[i, j] for i in range(n_aircraft)) >= get_demand(demand, j),
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}