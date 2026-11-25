import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    n_attorneys = 8
    n_docs = 4
    attorneys = list(range(n_attorneys))
    docs = list(range(n_docs))

    model = pyo.ConcreteModel()

    model.attorneys = pyo.Set(initialize=attorneys)
    model.docs = pyo.Set(initialize=docs)
    model.pairs = pyo.Set(initialize=[(i, j) for i in attorneys for j in docs], dimen=2)

    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in attorneys for j in docs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def doc_rule(mdl, j):
        return sum(mdl.x[i, j] for i in attorneys) == 1

    model.doc_constraint = pyo.Constraint(model.docs, rule=doc_rule)

    def attorney_rule(mdl, i):
        return sum(mdl.x[i, j] for j in docs) <= 1

    model.attorney_constraint = pyo.Constraint(model.attorneys, rule=attorney_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}