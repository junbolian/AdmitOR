# IR: {"sets":{"U":[0,1,2,3,4,5,6],"D":[0,1],"A":[[0,1],[0,3],[0,6],[1,0],[1,2],[1,3],[1,6],[2,1],[2,3],[3,2],[3,4],[4,2],[4,3],[4,5],[5,4],[5,6],[6,0],[6,5]]},"params":{"coordinates":"real[U,D], spatial metadata","lower_bounds":"real[A], supplied in A order","upper_bounds":"real[A], supplied in A order","costs":"real[A], supplied in A order"},"variables":{"flow":"nonnegative continuous[A]"},"constraints":["flow[i,j] >= lower_bounds[i,j] for each (i,j) in A","flow[i,j] <= upper_bounds[i,j] for each (i,j) in A","sum(flow[i,u] for (i,u) in A) == sum(flow[u,j] for (u,j) in A) for each u in U"],"objective":"minimize sum(costs[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Input format:
      coordinates: sequence of seven two-dimensional coordinate pairs.
      lower_bounds, upper_bounds, costs: sequences of length eighteen,
      ordered according to the pipeline list in the IR.
    """
    coordinates = params["coordinates"]
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    costs = params["costs"]

    arcs = (
        (0, 1),
        (0, 3),
        (0, 6),
        (1, 0),
        (1, 2),
        (1, 3),
        (1, 6),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 2),
        (4, 3),
        (4, 5),
        (5, 4),
        (5, 6),
        (6, 0),
        (6, 5),
    )

    model = pyo.ConcreteModel()
    model.units = pyo.RangeSet(0, 6)
    model.dimensions = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.coordinates = pyo.Param(
        model.units,
        model.dimensions,
        initialize={
            (unit, dimension): coordinates[unit][dimension]
            for unit in model.units
            for dimension in model.dimensions
        },
        within=pyo.Reals,
    )
    model.lower_bounds = pyo.Param(
        model.arcs,
        initialize={arc: lower_bounds[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.upper_bounds = pyo.Param(
        model.arcs,
        initialize={arc: upper_bounds[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.costs = pyo.Param(
        model.arcs,
        initialize={arc: costs[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.minimum_flow = pyo.Constraint(
        model.arcs,
        rule=lambda block, source, target: (
            block.flow[source, target] >= block.lower_bounds[source, target]
        ),
    )
    model.maximum_flow = pyo.Constraint(
        model.arcs,
        rule=lambda block, source, target: (
            block.flow[source, target] <= block.upper_bounds[source, target]
        ),
    )

    incoming = {
        unit: tuple(arc for arc in arcs if arc[1] == unit)
        for unit in model.units
    }
    outgoing = {
        unit: tuple(arc for arc in arcs if arc[0] == unit)
        for unit in model.units
    }

    def balance_rule(block, unit):
        return (
            sum(block.flow[arc] for arc in incoming[unit])
            == sum(block.flow[arc] for arc in outgoing[unit])
        )

    model.mass_balance = pyo.Constraint(model.units, rule=balance_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[source, target] * model.flow[source, target]
            for source, target in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}