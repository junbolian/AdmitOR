# IR: {"sets":{"V":"0..11","K":"0..11","E":[[4,9],[3,7],[3,10],[5,7],[2,11],[1,9],[6,8],[4,5],[4,8],[0,1],[0,7],[2,4],[10,11],[0,4],[0,10],[2,7],[1,5],[6,7],[6,10],[4,7],[3,8],[0,9],[8,10],[1,7],[2,6]]},"params":{},"variables":{"x[v,k]":"binary; enclosure v receives species k","y[k]":"binary; species k is enabled"},"constraints":["sum(k in K) x[v,k] = 1 for each v in V","x[u,k] + x[v,k] <= 1 for each (u,v) in E and k in K","x[v,k] <= y[k] for each v in V and k in K"],"objective":"minimize sum(k in K) y[k]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize distinct species types through binary graph coloring."""
    model = pyo.ConcreteModel()

    model.enclosures = pyo.RangeSet(0, 11)
    model.species = pyo.RangeSet(0, 11)
    model.adjacencies = pyo.Set(
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

    model.assignment = pyo.Var(
        model.enclosures, model.species, domain=pyo.Binary
    )
    model.species_used = pyo.Var(model.species, domain=pyo.Binary)

    def one_species_rule(current_model, enclosure):
        return sum(
            current_model.assignment[enclosure, species]
            for species in current_model.species
        ) == 1

    model.one_species = pyo.Constraint(
        model.enclosures, rule=one_species_rule
    )

    def incompatibility_rule(current_model, first, second, species):
        return (
            current_model.assignment[first, species]
            + current_model.assignment[second, species]
            <= 1
        )

    model.incompatibility = pyo.Constraint(
        model.adjacencies,
        model.species,
        rule=incompatibility_rule,
    )

    def usage_link_rule(current_model, enclosure, species):
        return (
            current_model.assignment[enclosure, species]
            <= current_model.species_used[species]
        )

    model.usage_link = pyo.Constraint(
        model.enclosures,
        model.species,
        rule=usage_link_rule,
    )

    model.species_count = pyo.Objective(
        expr=sum(
            model.species_used[species] for species in model.species
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.species_count))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}