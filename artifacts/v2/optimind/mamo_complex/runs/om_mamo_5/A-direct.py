import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H", "I"]

    cost_map = {}
    for a in cities:
        for b in cities:
            if a != b:
                cost_map[(a, b)] = params["cost_" + a + "_" + b]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(
        initialize=[(a, b) for a in cities for b in cities if a != b],
        dimen=2,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_map[(a, b)] * m.x[a, b] for (a, b) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(model.cities, rule=out_rule)

    def in_rule(m, i):
        return sum(m.x[j, i] for j in cities if j != i) == 1

    model.in_flow = pyo.Constraint(model.cities, rule=in_rule)

    # Miller-Tucker-Zemlin subtour elimination
    model.order = pyo.Var(model.cities, bounds=(1, len(cities)))
    model.order["E"].fix(1)

    def mtz_rule(m, i, j):
        if i == "E" or j == "E" or i == j:
            return pyo.Constraint.Skip
        return m.order[i] - m.order[j] + len(cities) * m.x[i, j] <= len(cities) - 1

    model.mtz = pyo.Constraint(model.cities, model.cities, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}