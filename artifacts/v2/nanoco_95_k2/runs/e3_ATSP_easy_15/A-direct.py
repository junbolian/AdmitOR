import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_checkpoints = params["num_checkpoints"]

    N = list(range(num_checkpoints))
    nodes = [i for i in N if i != 0]
    arcs = [(i, j) for i in N for j in N if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals, bounds=(1, num_checkpoints - 1))

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in N if j != i) == 1
    model.out_flow = pyo.Constraint(N, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in N if i != j) == 1
    model.in_flow = pyo.Constraint(N, rule=in_rule)

    def subtour_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (num_checkpoints - 1) * m.x[i, j] <= num_checkpoints - 2
    model.subtour = pyo.Constraint(
        [(i, j) for (i, j) in arcs if i != 0 and j != 0], rule=subtour_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}