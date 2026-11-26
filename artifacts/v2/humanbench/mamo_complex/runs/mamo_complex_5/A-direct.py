import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H", "I"]

    # Build arc cost dictionary from params (no self-arcs)
    arc_cost = {}
    for a in cities:
        for b in cities:
            if a != b:
                arc_cost[(a, b)] = params["cost_" + a + b]

    model = pyo.ConcreteModel()
    model.CITY = pyo.Set(initialize=cities)
    model.ARC = pyo.Set(initialize=list(arc_cost.keys()), dimen=2)

    model.x = pyo.Var(model.ARC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(arc_cost[(a, b)] * m.x[a, b] for (a, b) in arc_cost)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city: exactly one outgoing arc
    def out_rule(m, a):
        return sum(m.x[a, b] for b in cities if b != a) == 1

    # Each city: exactly one incoming arc
    def in_rule(m, b):
        return sum(m.x[a, b] for a in cities if a != b) == 1

    model.out_cons = pyo.Constraint(model.CITY, rule=out_rule)
    model.in_cons = pyo.Constraint(model.CITY, rule=in_rule)

    # Subtour elimination (MTZ-style ordering variables)
    others = ["F", "G", "H", "I"]
    model.u = pyo.Var(others, domain=pyo.NonNegativeReals, bounds=(1, len(cities) - 1))

    def mtz_rule(m, a, b):
        if a != b and a in others and b in others:
            return m.u[a] - m.u[b] + (len(cities) - 1) * m.x[a, b] <= len(cities) - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.CITY, model.CITY, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}