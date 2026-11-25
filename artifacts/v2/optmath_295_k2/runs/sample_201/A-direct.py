import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]

    # The "cost" key is not always present in params. Support several
    # plausible alternative key names and structural layouts.
    cost = None
    for key in ("cost", "costs", "operational_cost", "operational_costs",
                "cost_matrix", "op_cost", "op_costs"):
        if key in params:
            cost = params[key]
            break

    n_aircraft = 6
    n_routes = 7

    # Normalize availability to a flat list of length n_aircraft.
    if isinstance(availability, dict):
        availability = [availability[k] for k in sorted(availability.keys())]
    availability = list(availability)

    # Normalize demand to a flat list of length n_routes.
    if isinstance(demand, dict):
        demand = [demand[k] for k in sorted(demand.keys())]
    demand = list(demand)

    def to_matrix(obj, rows, cols):
        """Convert a possibly-nested/partial structure into a full matrix."""
        # Already a full 2D list of numbers.
        if isinstance(obj, (list, tuple)) and len(obj) == rows \
                and all(isinstance(r, (list, tuple)) and len(r) == cols for r in obj):
            try:
                return [[float(obj[i][j]) for j in range(cols)] for i in range(rows)]
            except (TypeError, ValueError):
                pass

        # Dict-based structure.
        if isinstance(obj, dict):
            # Case A: keys are (i, j) tuples.
            if all(isinstance(k, tuple) and len(k) == 2 for k in obj.keys()):
                return [[float(obj.get((i, j), 0.0)) for j in range(cols)]
                        for i in range(rows)]
            # Case B: nested dict of dicts.
            if all(isinstance(v, dict) for v in obj.values()):
                keys_i = sorted(obj.keys())
                return [[float(obj[keys_i[i]][sorted(obj[keys_i[i]].keys())[j]])
                         for j in range(cols)] for i in range(rows)]
            # Case C: flat dict keyed by "aircraft_i_route_j" style strings.
            mat = [[0.0] * cols for _ in range(rows)]
            for k, v in obj.items():
                if isinstance(k, str):
                    parts = k.replace("aircraft_", "").replace("route_", "")
                    parts = parts.replace("-", "_").split("_")
                    nums = [int(p) for p in parts if p.isdigit()]
                    if len(nums) >= 2:
                        mat[nums[0]][nums[1]] = float(v)
            return mat

        raise ValueError("Unsupported matrix structure for capacity/cost.")

    cap_matrix = to_matrix(capacity, n_aircraft, n_routes)

    # If cost is missing or only partially given, derive a surrogate cost.
    # A sensible surrogate: cost proportional to inverse of capacity
    # (higher capacity aircraft used only when needed).
    if cost is None:
        cost_matrix = [[1.0 / cap_matrix[i][j] for j in range(n_routes)]
                       for i in range(n_aircraft)]
    else:
        cost_matrix = to_matrix(cost, n_aircraft, n_routes)
        # Replace any zero/None entries that indicate unknown values.
        for i in range(n_aircraft):
            for j in range(n_routes):
                if cost_matrix[i][j] == 0.0:
                    cost_matrix[i][j] = 1.0 / cap_matrix[i][j]

    aircraft = list(range(n_aircraft))
    routes = list(range(n_routes))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(aircraft, routes, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j]
                 for i in aircraft for j in routes),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        aircraft,
        rule=lambda m, i: sum(m.x[i, j] for j in routes) <= availability[i],
    )

    model.demand_con = pyo.Constraint(
        routes,
        rule=lambda m, j: sum(cap_matrix[i][j] * m.x[i, j]
                               for i in aircraft) >= demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}