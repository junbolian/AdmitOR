import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow = params["flow_matrix"]
    dist = params["distance_matrix"]
    n_fac = params["num_facilities"]
    n_loc = params["num_locations"]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_fac - 1)
    model.L = pyo.RangeSet(0, n_loc - 1)

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            flow[i][j] * dist[a][b] * mdl.x[i, a] * mdl.x[j, b]
            for i in mdl.F
            for j in mdl.F
            for a in mdl.L
            for b in mdl.L
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def rack_rule(mdl, i):
        return sum(mdl.x[i, a] for a in mdl.L) == 1

    def slot_rule(mdl, a):
        return sum(mdl.x[i, a] for i in mdl.F) == 1

    model.rack_con = pyo.Constraint(model.F, rule=rack_rule)
    model.slot_con = pyo.Constraint(model.L, rule=slot_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}