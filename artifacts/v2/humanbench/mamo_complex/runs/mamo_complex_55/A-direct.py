import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()
    regions = [1, 2, 3, 4, 5]
    pairs = [(i, j) for i in regions for j in regions if i != j]

    model.P = pyo.Set(initialize=regions, dimen=1)
    model.A = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.cost = pyo.Objective(
        expr=sum(params["cost_%d_%d" % (i, j)] * model.x[i, j] for (i, j) in pairs),
        sense=pyo.minimize,
    )

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in regions if j != i) - \
               sum(m.x[j, i] for j in regions if j != i) <= \
               params["supply_%d" % i] - params["demand_%d" % i]
    model.supply_con = pyo.Constraint(model.P, rule=supply_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}