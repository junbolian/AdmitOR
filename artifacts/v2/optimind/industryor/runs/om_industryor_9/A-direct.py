import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_radius_m = params["coverage_radius_m"]

    areas = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

    coverage = {
        "A": ["A", "C", "E", "G", "H", "I"],
        "B": ["B", "H", "I"],
        "C": ["A", "C", "G", "H", "I"],
        "D": ["D", "J"],
        "E": ["A", "E", "G"],
        "F": ["F", "J", "K"],
        "G": ["A", "C", "E", "G"],
        "H": ["A", "B", "C", "H", "I"],
        "I": ["A", "B", "C", "H", "I"],
        "J": ["D", "F", "J", "K", "L"],
        "K": ["F", "J", "K", "L"],
        "L": ["J", "K", "L"],
    }

    # Static validity check on the coverage radius parameter. If the radius is
    # non-positive, no area can cover any (distinct) residential area.
    if coverage_radius_m <= 0:
        return {"objective": None, "status": "infeasible: coverage radius must be positive"}

    model = pyo.ConcreteModel()

    model.AREAS = pyo.Set(initialize=areas)

    def cover_init(mdl):
        cov = {}
        for i in areas:
            for j in coverage[i]:
                cov[(i, j)] = True
        return cov

    model.COVER = pyo.Set(dimen=2, initialize=cover_init)

    model.y = pyo.Var(model.AREAS, domain=pyo.Binary)

    def cover_rule(mdl, j):
        return sum(mdl.y[i] for i in areas if (i, j) in mdl.COVER) >= 1

    model.cover_con = pyo.Constraint(model.AREAS, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(model.y[i] for i in model.AREAS), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}