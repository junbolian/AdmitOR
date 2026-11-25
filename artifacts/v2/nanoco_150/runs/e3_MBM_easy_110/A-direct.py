import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural data
    orders = list(range(6))
    stations = list(range(5))

    # Feasible (order, station) connection paths
    paths = [
        (0, 0), (0, 1), (0, 4),
        (1, 2),
        (2, 0), (2, 1), (2, 4),
        (3, 0), (3, 1), (3, 2),
        (4, 3),
    ]

    model = pyo.ConcreteModel()

    model.PATHS = pyo.Set(initialize=paths, dimen=2)

    model.x = pyo.Var(model.PATHS, domain=pyo.Binary)

    # Build index helpers
    paths_by_order = {i: [] for i in orders}
    paths_by_station = {j: [] for j in stations}
    for (i, j) in paths:
        paths_by_order[i].append((i, j))
        paths_by_station[j].append((i, j))

    def obj_rule(m):
        return sum(m.x[p] for p in m.PATHS)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Each order at most one station
    def order_rule(m, i):
        expr = sum(m.x[p] for p in paths_by_order[i])
        if len(paths_by_order[i]) == 0:
            return pyo.Constraint.Feasible
        return expr <= 1

    model.order_limit = pyo.Constraint(orders, rule=order_rule)

    # Each station at most one order
    def station_rule(m, j):
        expr = sum(m.x[p] for p in paths_by_station[j])
        if len(paths_by_station[j]) == 0:
            return pyo.Constraint.Feasible
        return expr <= 1

    model.station_limit = pyo.Constraint(stations, rule=station_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}