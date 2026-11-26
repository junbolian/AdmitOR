import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    districts = ["D1", "D2", "D3", "D4"]

    def _get(val, key, idx):
        if isinstance(val, dict):
            return val[key]
        return val[idx]

    supply = {d: _get(params["supply"], d, k) for k, d in enumerate(districts)}
    demand = {d: _get(params["demand"], d, k) for k, d in enumerate(districts)}

    cost = {}
    for i, di in enumerate(districts):
        for j, dj in enumerate(districts):
            if i != j:
                cost[(di, dj)] = params["cost_%d_to_%d" % (i + 1, j + 1)]

    model = pyo.ConcreteModel()

    model.groups = pyo.Set(initialize=districts)

    model.arcs = pyo.Set(
        initialize=[(di, dj) for di in districts for dj in districts if di != dj],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[(di, dj)] * mdl.flow[(di, dj)] for (di, dj) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Net outflow from each district equals supply minus demand (surplus shipped out / deficit received)
    def balance_rule(mdl, i):
        outflow = sum(mdl.flow[(i, j)] for j in districts if j != i)
        inflow = sum(mdl.flow[(j, i)] for j in districts if j != i)
        return outflow - inflow == supply[i] - demand[i]

    model.balance_con = pyo.Constraint(model.groups, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}