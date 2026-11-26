import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)

    # Directed cost dictionary from params
    cost = {
        ('E', 'F'): params["cost_E_F"], ('E', 'G'): params["cost_E_G"],
        ('E', 'H'): params["cost_E_H"], ('E', 'I'): params["cost_E_I"],
        ('F', 'E'): params["cost_F_E"], ('F', 'G'): params["cost_F_G"],
        ('F', 'H'): params["cost_F_H"], ('F', 'I'): params["cost_F_I"],
        ('G', 'E'): params["cost_G_E"], ('G', 'F'): params["cost_G_F"],
        ('G', 'H'): params["cost_G_H"], ('G', 'I'): params["cost_G_I"],
        ('H', 'E'): params["cost_H_E"], ('H', 'F'): params["cost_H_F"],
        ('H', 'G'): params["cost_H_G"], ('H', 'I'): params["cost_H_I"],
        ('I', 'E'): params["cost_I_E"], ('I', 'F'): params["cost_I_F"],
        ('I', 'G'): params["cost_I_G"], ('I', 'H'): params["cost_I_H"],
    }

    # Arcs exclude self-loops
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.CITIES = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.out_constraint = pyo.Constraint(model.CITIES, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.in_constraint = pyo.Constraint(model.CITIES, rule=in_rule)

    # Subtour elimination (MTZ). With a single tour over all 5 cities,
    # enforce ordering variables u in [1, n-1] for non-depot nodes.
    depot = 'E'
    others = [c for c in cities if c != depot]
    model.u = pyo.Var(others, bounds=(1, n - 1))

    def mtz_rule(m, i, j):
        if i == depot or j == depot:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (n - 1) * m.x[(i, j)] <= (n - 2)

    model.mtz_constraint = pyo.Constraint(arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}