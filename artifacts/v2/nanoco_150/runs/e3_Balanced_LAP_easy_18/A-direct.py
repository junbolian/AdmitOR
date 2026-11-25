import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    m = len(cost_matrix[0])

    model = pyo.ConcreteModel()
    model.rows = pyo.RangeSet(0, n - 1)
    model.cols = pyo.RangeSet(0, m - 1)
    model.x = pyo.Var(model.rows, model.cols, domain=pyo.Binary)

    def obj_rule(md):
        return sum(cost_matrix[i][j] * md.x[i, j]
                   for i in md.rows for j in md.cols)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def row_rule(md, i):
        return sum(md.x[i, j] for j in md.cols) == 1
    model.row_con = pyo.Constraint(model.rows, rule=row_rule)

    def col_rule(md, j):
        return sum(md.x[i, j] for i in md.rows) == 1
    model.col_con = pyo.Constraint(model.cols, rule=col_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}