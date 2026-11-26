import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    cap = params["capacity_matrix"]

    def cap_at(i, j):
        return cap[i][j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
    )

    def flow_bounds(m, i, j):
        return (0, cap_at(i, j))

    model.flow = pyo.Var(model.arcs, bounds=flow_bounds)

    def balance_rule(m, k):
        out_flow = sum(m.flow[k, j] for j in range(n) if j != k)
        in_flow = sum(m.flow[i, k] for i in range(n) if i != k)
        if k == 0:
            return out_flow - in_flow >= 0
        if k == 8:
            return in_flow - out_flow >= 0
        return out_flow - in_flow == 0

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def sink_rule(m):
        return sum(m.flow[8, j] for j in range(n) if j != 8) == 0

    model.sink = pyo.Constraint(rule=sink_rule)

    def objective_rule(m):
        return sum(m.flow[i, 8] for i in range(n) if i != 8)

    model.objective_expr = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective_expr))
    return {"objective": obj_val, "status": "optimal"}