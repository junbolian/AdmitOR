import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H"]

    arc_cost = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("F", "E"): params["cost_F_E"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("G", "E"): params["cost_G_E"],
        ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"],
        ("H", "E"): params["cost_H_E"],
        ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"],
    }

    arcs = list(arc_cost.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(arc_cost[a] * m.x[a] for a in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_cons = pyo.Constraint(cities, rule=out_rule)
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    def mtz_rule(m, i, j):
        if i != j and i != "E" and j != "E":
            return m.u[i] - m.u[j] + len(cities) * m.x[(i, j)] <= len(cities) - 1
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=mtz_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}