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

    # Directed arcs (all ordered pairs of distinct cities)
    arcs = [(a, b) for a in cities for b in cities if a != b]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(range(len(cities)), within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[(a, b)] * model.x[(a, b)] for (a, b) in arcs),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing and one incoming arc
    model.out_deg = pyo.Constraint(
        cities, rule=lambda md, c: sum(md.x[(c, d)] for d in cities if d != c) == 1
    )
    model.in_deg = pyo.Constraint(
        cities, rule=lambda md, c: sum(md.x[(d, c)] for d in cities if d != c) == 1
    )

    n = len(cities)
    idx = {c: k for k, c in enumerate(cities)}

    # Subtour elimination (MTZ style) on non-start nodes
    def mtz_rule(md, a, b):
        if a == cities[0] or b == cities[0]:
            return pyo.Constraint.Skip
        return md.u[idx[a]] - md.u[idx[b]] + n * md.x[(a, b)] <= n - 1

    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    # Bounds on u for all nodes
    def u_lo(md, k):
        return md.u[k] >= 1

    def u_hi(md, k):
        return md.u[k] <= n - 1

    model.u_lo = pyo.Constraint(range(n), rule=u_lo)
    model.u_hi = pyo.Constraint(range(n), rule=u_hi)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}