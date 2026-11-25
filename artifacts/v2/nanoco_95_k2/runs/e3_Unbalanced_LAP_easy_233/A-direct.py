import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n_attorneys = 8
    n_docs = 4

    model = pyo.ConcreteModel()

    model.attorneys = pyo.RangeSet(0, n_attorneys - 1)
    model.documents = pyo.RangeSet(0, n_docs - 1)

    def cost_rule(m, i, j):
        return cost[i][j]
    model.cost = pyo.Param(model.attorneys, model.documents, rule=cost_rule)

    model.assign = pyo.Var(model.attorneys, model.documents, domain=pyo.Binary)

    def doc_rule(m, j):
        return sum(m.assign[i, j] for i in m.attorneys) == 1
    model.doc_constraint = pyo.Constraint(model.documents, rule=doc_rule)

    def atty_rule(m, i):
        return sum(m.assign[i, j] for j in m.documents) <= 1
    model.atty_constraint = pyo.Constraint(model.attorneys, rule=atty_rule)

    def obj_rule(m):
        return sum(m.cost[i, j] * m.assign[i, j] for i in m.attorneys for j in m.documents)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}