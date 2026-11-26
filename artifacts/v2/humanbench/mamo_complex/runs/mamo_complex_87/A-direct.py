import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ['E', 'F', 'G', 'H', 'I']
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost_data = {
        ('E', 'F'): params["cost_E_F"],
        ('E', 'G'): params["cost_E_G"],
        ('E', 'H'): params["cost_E_H"],
        ('E', 'I'): params["cost_E_I"],
        ('F', 'E'): params["cost_F_E"],
        ('F', 'G'): params["cost_F_G"],
        ('F', 'H'): params["cost_F_H"],
        ('F', 'I'): params["cost_F_I"],
        ('G', 'E'): params["cost_G_E"],
        ('G', 'F'): params["cost_G_F"],
        ('G', 'H'): params["cost_G_H"],
        ('G', 'I'): params["cost_G_I"],
        ('H', 'E'): params["cost_H_E"],
        ('H', 'F'): params["cost_H_F"],
        ('H', 'G'): params["cost_H_G"],
        ('H', 'I'): params["cost_H_I"],
        ('I', 'E'): params["cost_I_E"],
        ('I', 'F'): params["cost_I_F"],
        ('I', 'G'): params["cost_I_G"],
        ('I', 'H'): params["cost_I_H"],
    }

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_data[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in nodes if j != i) == 1

    model.out_con = pyo.Constraint(model.nodes, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in nodes if i != j) == 1

    model.in_con = pyo.Constraint(model.nodes, rule=in_rule)

    model.u = pyo.Var(model.nodes, bounds=(0, len(nodes) - 1))
    model.u['E'].fix(0)

    subtour_nodes = [n for n in nodes if n != 'E']

    def subtour_rule(m, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (len(nodes) - 1) * m.x[(i, j)] <= len(nodes) - 2

    model.subtour_con = pyo.Constraint(subtour_nodes, subtour_nodes, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}