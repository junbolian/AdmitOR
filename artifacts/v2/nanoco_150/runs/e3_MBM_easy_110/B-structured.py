# IR: {"sets":{"orders":[0,1,2,3,4,5],"stations":[0,1,2,3,4],"arcs":[[0,0],[0,1],[0,4],[1,2],[2,0],[2,1],[2,4],[3,0],[3,1],[3,2],[4,3]]},"params":{},"variables":{"x[i,j]":{"index":"arcs","type":"binary"}},"constraints":["For each order i: sum(x[i,j] for (i,j) in arcs) <= 1","For each station j: sum(x[i,j] for (i,j) in arcs) <= 1"],"objective":{"sense":"maximize","expression":"sum(x[i,j] for (i,j) in arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # No numeric parameters are specified; indices and arcs are structural.
    model = pyo.ConcreteModel()

    model.orders = pyo.Set(initialize=range(6), ordered=True)
    model.stations = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (0, 0), (0, 1), (0, 4),
            (1, 2),
            (2, 0), (2, 1), (2, 4),
            (3, 0), (3, 1), (3, 2),
            (4, 3),
        ],
        ordered=True,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def order_capacity_rule(instance, order):
        total = pyo.quicksum(
            instance.x[order, station]
            for station in instance.stations
            if (order, station) in instance.arcs
        )
        # Tuple form also represents the constant constraint for order 5.
        return (None, total, 1)

    model.order_capacity = pyo.Constraint(
        model.orders, rule=order_capacity_rule
    )

    def station_capacity_rule(instance, station):
        return (
            None,
            pyo.quicksum(
                instance.x[order, station]
                for order in instance.orders
                if (order, station) in instance.arcs
            ),
            1,
        )

    model.station_capacity = pyo.Constraint(
        model.stations, rule=station_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.x[order, station] for order, station in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}