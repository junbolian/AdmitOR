import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 5
    model = pyo.ConcreteModel()

    model.vm = pyo.RangeSet(0, n - 1)
    model.node = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.vm, model.node, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j]
                   for i in range(n) for j in range(n))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def vm_rule(m, i):
        return sum(m.x[i, j] for j in range(n)) == 1

    model.vm_constraint = pyo.Constraint(model.vm, rule=vm_rule)

    def node_rule(m, j):
        return sum(m.x[i, j] for i in range(n)) == 1

    model.node_constraint = pyo.Constraint(model.node, rule=node_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}