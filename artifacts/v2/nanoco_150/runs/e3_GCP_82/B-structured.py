# IR: {"sets":{"T":"0..11","F":"0..11","E":[[0,1],[0,4],[5,8],[4,9],[6,9],[6,8],[3,10],[5,7],[0,6],[6,7],[8,9],[2,6],[0,5],[9,11],[0,8],[2,11],[0,11]]},"params":{},"variables":{"x[t,f]":"binary; tower t uses frequency f","y[f]":"binary; frequency f is used"},"constraints":["sum(f in F) x[t,f] = 1 for every t in T","x[t,f] <= y[f] for every t in T, f in F","x[u,f] + x[v,f] <= 1 for every (u,v) in E, f in F"],"objective":"minimize sum(f in F) y[f]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the minimum-frequency assignment problem.

    No numeric parameters are specified; params may be an empty dict.
    Twelve candidate frequencies suffice for twelve towers.
    """
    model = pyo.ConcreteModel()

    model.towers = pyo.RangeSet(0, 11)
    model.frequencies = pyo.RangeSet(0, 11)
    model.links = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1),
            (0, 4),
            (5, 8),
            (4, 9),
            (6, 9),
            (6, 8),
            (3, 10),
            (5, 7),
            (0, 6),
            (6, 7),
            (8, 9),
            (2, 6),
            (0, 5),
            (9, 11),
            (0, 8),
            (2, 11),
            (0, 11),
        ],
    )

    model.assignment = pyo.Var(
        model.towers, model.frequencies, domain=pyo.Binary
    )
    model.frequency_used = pyo.Var(model.frequencies, domain=pyo.Binary)

    def assignment_rule(instance, tower):
        return sum(
            instance.assignment[tower, frequency]
            for frequency in instance.frequencies
        ) == 1

    model.one_frequency = pyo.Constraint(
        model.towers, rule=assignment_rule
    )

    def usage_rule(instance, tower, frequency):
        return (
            instance.assignment[tower, frequency]
            <= instance.frequency_used[frequency]
        )

    model.usage_link = pyo.Constraint(
        model.towers, model.frequencies, rule=usage_rule
    )

    def interference_rule(instance, tower_u, tower_v, frequency):
        return (
            instance.assignment[tower_u, frequency]
            + instance.assignment[tower_v, frequency]
            <= 1
        )

    model.no_interference = pyo.Constraint(
        model.links, model.frequencies, rule=interference_rule
    )

    model.total_frequencies = pyo.Objective(
        expr=sum(
            model.frequency_used[frequency]
            for frequency in model.frequencies
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors must propagate.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_frequencies))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}