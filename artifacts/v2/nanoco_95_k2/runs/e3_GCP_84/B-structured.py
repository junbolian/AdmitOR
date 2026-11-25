# IR: {"sets":{"V":[0,1,2,3,4,5,6,7,8,9,10,11],"K":[0,1,2,3,4,5,6,7,8,9,10,11],"E":[[4,9],[3,7],[3,10],[5,7],[2,11],[1,9],[6,8],[4,5],[4,8],[0,1],[0,7],[2,4],[10,11],[0,4],[0,10],[2,7],[1,5],[6,7],[6,10],[4,7],[3,8],[0,9],[8,10],[1,7],[2,6]]},"params":{},"decision_variables":{"x[v,k]":"binary; enclosure v receives species k","y[k]":"binary; species k is used"},"constraints":["sum(k in K) x[v,k] = 1 for each v in V","x[u,k] + x[v,k] <= 1 for each (u,v) in E and k in K","x[v,k] <= y[k] for each v in V and k in K","y[k] <= sum(v in V) x[v,k] for each k in K"],"objective":"minimize sum(k in K) y[k]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # No numeric parameters are specified; all constants define graph structure.
    edges = [
        (4, 9),
        (3, 7),
        (3, 10),
        (5, 7),
        (2, 11),
        (1, 9),
        (6, 8),
        (4, 5),
        (4, 8),
        (0, 1),
        (0, 7),
        (2, 4),
        (10, 11),
        (0, 4),
        (0, 10),
        (2, 7),
        (1, 5),
        (6, 7),
        (6, 10),
        (4, 7),
        (3, 8),
        (0, 9),
        (8, 10),
        (1, 7),
        (2, 6),
    ]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 11)
    model.K = pyo.RangeSet(0, 11)
    model.E = pyo.Set(dimen=2, initialize=edges)

    model.x = pyo.Var(model.V, model.K, domain=pyo.Binary)
    model.y = pyo.Var(model.K, domain=pyo.Binary)

    def assignment_rule(mdl, enclosure):
        return sum(mdl.x[enclosure, species] for species in mdl.K) == 1

    model.assignment_constraints = pyo.Constraint(
        model.V, rule=assignment_rule
    )

    def incompatibility_rule(mdl, first, second, species):
        return mdl.x[first, species] + mdl.x[second, species] <= 1

    model.incompatibility_constraints = pyo.Constraint(
        model.E, model.K, rule=incompatibility_rule
    )

    def usage_link_rule(mdl, enclosure, species):
        return mdl.x[enclosure, species] <= mdl.y[species]

    model.usage_link_constraints = pyo.Constraint(
        model.V, model.K, rule=usage_link_rule
    )

    def actual_usage_rule(mdl, species):
        return mdl.y[species] <= sum(
            mdl.x[enclosure, species] for enclosure in mdl.V
        )

    model.actual_usage_constraints = pyo.Constraint(
        model.K, rule=actual_usage_rule
    )

    model.total_species = pyo.Objective(
        expr=sum(model.y[species] for species in model.K),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_species))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}