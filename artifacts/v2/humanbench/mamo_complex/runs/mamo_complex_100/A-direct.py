import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {
        ('A', 'B'): params["cost_A_B"],
        ('A', 'C'): params["cost_A_C"],
        ('A', 'D'): params["cost_A_D"],
        ('B', 'A'): params["cost_B_A"],
        ('B', 'C'): params["cost_B_C"],
        ('B', 'D'): params["cost_B_D"],
        ('C', 'A'): params["cost_C_A"],
        ('C', 'B'): params["cost_C_B"],
        ('C', 'D'): params["cost_C_D"],
        ('D', 'A'): params["cost_D_A"],
        ('D', 'B'): params["cost_D_B"],
        ('D', 'C'): params["cost_D_C"],
    }

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[a] * mdl.x[a] for a in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}