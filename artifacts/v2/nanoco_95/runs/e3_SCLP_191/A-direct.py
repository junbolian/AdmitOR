import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["establishment_costs"]
    radius = params["coverage_radius"]
    dist = params["distance_matrix"]

    n_zones = len(dist)
    n_cands = len(costs)

    model = pyo.ConcreteModel()

    model.CAND = pyo.RangeSet(0, n_cands - 1)
    model.ZONE = pyo.RangeSet(0, n_zones - 1)

    model.x = pyo.Var(model.CAND, domain=pyo.Binary)

    def cover_rule(mdl, i):
        eligible = [j for j in range(n_cands) if dist[i][j] <= radius]
        if not eligible:
            return pyo.Constraint.Skip
        return sum(mdl.x[j] for j in eligible) >= 1

    model.cover = pyo.Constraint(model.ZONE, rule=cover_rule)

    model.obj = pyo.Objective(
        expr=sum(costs[j] * model.x[j] for j in model.CAND),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:100] or "solve failed"}