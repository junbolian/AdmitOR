import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    def get_val(name, i):
        v = params[name]
        if isinstance(v, dict):
            return v[i] if i in v else v[str(i)]
        return v

    supply = {c: get_val("supply", c) for c in cities}
    demand = {c: get_val("demand", c) for c in cities}

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_to_{j}"]

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in cities for j in cities if i != j]
    model.arcs = pyo.Set(dimen=2, initialize=arcs)

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def _obj(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=_obj, sense=pyo.minimize)

    def _balance_rule(m, c):
        inflow = sum(m.x[i, c] for i in cities if i != c)
        outflow = sum(m.x[c, j] for j in cities if j != c)
        return supply[c] + inflow - outflow >= demand[c]

    model.balance = pyo.Constraint(cities, rule=_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}