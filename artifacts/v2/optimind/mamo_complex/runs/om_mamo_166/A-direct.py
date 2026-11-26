import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["A", "B", "C", "D"]

    def travel_cost(i, j):
        return params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in cities for j in cities if i != j],
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(travel_cost(i, j) * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.out_degree = pyo.Constraint(model.cities, rule=out_rule)
    model.in_degree = pyo.Constraint(model.cities, rule=in_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}