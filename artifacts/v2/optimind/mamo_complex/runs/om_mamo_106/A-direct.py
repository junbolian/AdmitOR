import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H", "I"]
    cost = {
        ("E", "F"): params["cost_E_F"], ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"], ("E", "I"): params["cost_E_I"],
        ("F", "E"): params["cost_F_E"], ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"], ("F", "I"): params["cost_F_I"],
        ("G", "E"): params["cost_G_E"], ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"], ("G", "I"): params["cost_G_I"],
        ("H", "E"): params["cost_H_E"], ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"], ("H", "I"): params["cost_H_I"],
        ("I", "E"): params["cost_I_E"], ("I", "F"): params["cost_I_F"],
        ("I", "G"): params["cost_I_G"], ("I", "H"): params["cost_I_H"],
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Each city has exactly one outgoing arc
    model.out_rule = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1
    )
    # Each city has exactly one incoming arc
    model.in_rule = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1
    )

    # Subtour elimination (MTZ)
    n = len(cities)
    model.order = pyo.Var(cities, bounds=(1, n))
    model.mtz_rule = pyo.Constraint(
        [(i, j) for (i, j) in arcs if i != cities[0] and j != cities[0]],
        rule=lambda m, i, j: m.order[i] - m.order[j] + n * m.x[i, j] <= n - 1,
    )
    model.order_fix = pyo.Constraint(expr=model.order[cities[0]] == 1)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[i, j] for (i, j) in arcs), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}