import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H", "I"]

    cost = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("E", "I"): params["cost_E_I"],
        ("F", "E"): params["cost_F_E"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("F", "I"): params["cost_F_I"],
        ("G", "E"): params["cost_G_E"],
        ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"],
        ("G", "I"): params["cost_G_I"],
        ("H", "E"): params["cost_H_E"],
        ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"],
        ("H", "I"): params["cost_H_I"],
        ("I", "E"): params["cost_I_E"],
        ("I", "F"): params["cost_I_F"],
        ("I", "G"): params["cost_I_G"],
        ("I", "H"): params["cost_I_H"],
    }

    arcs = [(a, b) for a in cities for b in cities if a != b]

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.CITY = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.ARC, domain=pyo.Binary)
    model.u = pyo.Var(model.CITY, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(a, b)] * m.x[(a, b)] for (a, b) in m.ARC)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, a):
        return sum(m.x[(a, b)] for b in cities if b != a) == 1

    def in_rule(m, b):
        return sum(m.x[(a, b)] for a in cities if a != b) == 1

    model.out_cons = pyo.Constraint(model.CITY, rule=out_rule)
    model.in_cons = pyo.Constraint(model.CITY, rule=in_rule)

    # Subtour elimination (MTZ). Fix u[E] = 0 as the anchor to break symmetry.
    model.u["E"].fix(0)

    def mtz_rule(m, a, b):
        if a != b and a != "E" and b != "E":
            return m.u[a] - m.u[b] + len(cities) * m.x[(a, b)] <= len(cities) - 1
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(model.ARC, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}