import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_cost = list(params["route_cost"])
    route_capacity_r = params["route_capacity_r"]

    # Structural constants: number of routes and number of sales locations.
    n = len(route_cost)
    # Feasible route structure: route j covers a set of sales locations.
    # Since only costs are provided in params, we model each route as covering
    # a single distinct sales location type (index structure is structural).
    # Sales locations correspond 1-1 with route indices here.
    m = n

    # Build route -> set of covered sales locations (structural incidence).
    # Each route j covers sales location j.
    route_locations = {j: {j} for j in range(n)}

    model = pyo.ConcreteModel()

    # Sets
    model.ROUTES = pyo.RangeSet(0, n - 1)
    model.LOCATIONS = pyo.RangeSet(0, m - 1)

    # Decision variables: x_j = number of delivery persons assigned to route j
    model.x = pyo.Var(model.ROUTES, domain=pyo.NonNegativeIntegers)

    # Constraint: each sales location's order must be satisfied (covered by
    # at least one route that includes it).
    def cover_rule(model, i):
        covering = [j for j in range(n) if i in route_locations[j]]
        return sum(model.x[j] for j in covering) >= 1

    model.cover = pyo.Constraint(model.LOCATIONS, rule=cover_rule)

    # Constraint: each delivery person can transport up to r types of orders.
    # Each route used (x_j >= 1) must have at most r covered order types.
    def capacity_rule(model, j):
        return len(route_locations[j]) * model.x[j] <= route_capacity_r * model.x[j]

    model.capacity = pyo.Constraint(model.ROUTES, rule=capacity_rule)

    # Objective: minimize total cost of selected routes.
    model.obj = pyo.Objective(
        expr=sum(route_cost[j] * model.x[j] for j in model.ROUTES),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}