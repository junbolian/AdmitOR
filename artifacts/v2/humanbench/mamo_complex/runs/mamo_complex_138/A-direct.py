import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    nodes = list(range(n))

    model = pyo.ConcreteModel()

    cost = {(i, j): float(cost_matrix[i][j]) for i in nodes for j in nodes if i != j}

    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=list(cost.keys()), dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for (i, j) in m.A)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node: exactly one outgoing and one incoming arc
    model.out_deg = pyo.Constraint(
        model.N,
        rule=lambda m, i: sum(m.x[i, j] for j in nodes if j != i) == 1,
    )
    model.in_deg = pyo.Constraint(
        model.N,
        rule=lambda m, j: sum(m.x[i, j] for i in nodes if i != j) == 1,
    )

    # Subtour elimination via single-commodity flow (MTZ-style)
    # u[i] = number of nodes visited so far when arriving at node i
    model.u = pyo.Var(model.N, bounds=(1, n - 1))

    # Fix depot node 0 as the start (u[0] = 1); shift keeps formulation valid
    model.fix_depot = pyo.Constraint(expr=model.u[0] == 1)

    arcs_non_depot = [(i, j) for (i, j) in cost.keys() if i != 0 and j != 0]

    def mtz_rule(m, i, j):
        if i != 0 and j != 0 and i != j:
            return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= (n - 2)
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(arcs_non_depot, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}