import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_checkpoints = int(params["num_checkpoints"])
    N = num_checkpoints

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, N - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(N) for j in range(N) if i != j],
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in range(N) if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in range(N) if i != j) == 1

    model.out_cons = pyo.Constraint(model.nodes, rule=out_rule)
    model.in_cons = pyo.Constraint(model.nodes, rule=in_rule)

    model.arc_list = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in range(N) for j in range(N) if i != j and i != 0 and j != 0
        ],
    )
    model.u = pyo.Var(model.nodes, domain=pyo.NonNegativeReals, bounds=(0, N - 1))

    def subtour_rule(m, i, j):
        return m.u[i] - m.u[j] + (N - 1) * m.x[i, j] <= N - 2

    model.subtour_cons = pyo.Constraint(model.arc_list, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}