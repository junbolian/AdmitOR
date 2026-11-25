# IR: {"sets":{"V":"0..11","K":"0..11","E":[[4,9],[3,7],[3,10],[5,7],[2,11],[1,9],[6,8],[4,5],[4,8],[0,1],[0,7],[2,4],[10,11],[0,4],[0,10],[2,7],[1,5],[6,7],[6,10],[4,7],[3,8],[0,9],[8,10],[1,7],[2,6]]},"params":{},"variables":{"x[v,k]":"binary; species k assigned to enclosure v","y[k]":"binary; species k used"},"constraints":["sum(k in K) x[v,k] = 1 for each v in V","x[u,k] + x[v,k] <= 1 for each (u,v) in E, k in K","x[v,k] <= y[k] for each v in V, k in K"],"objective":"minimize sum(k in K) y[k]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # PARAMS is empty. All numeric data below define the graph structure
    # or the binary assignment formulation.
    model = pyo.ConcreteModel()

    model.enclosures = pyo.RangeSet(0, 11)
    model.species = pyo.RangeSet(0, 11)
    model.adjacency = pyo.Set(
        dimen=2,
        initialize=[
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
        ],
    )

    model.x = pyo.Var(
        model.enclosures, model.species, domain=pyo.Binary
    )
    model.y = pyo.Var(model.species, domain=pyo.Binary)

    def assignment_rule(mdl, enclosure):
        return sum(
            mdl.x[enclosure, species] for species in mdl.species
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.enclosures, rule=assignment_rule
    )

    def incompatibility_rule(mdl, first, second, species):
        return mdl.x[first, species] + mdl.x[second, species] <= 1

    model.incompatibility_constraints = pyo.Constraint(
        model.adjacency, model.species, rule=incompatibility_rule
    )

    def species_usage_rule(mdl, enclosure, species):
        return mdl.x[enclosure, species] <= mdl.y[species]

    model.species_usage_constraints = pyo.Constraint(
        model.enclosures, model.species, rule=species_usage_rule
    )

    model.total_species = pyo.Objective(
        expr=sum(model.y[species] for species in model.species),
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