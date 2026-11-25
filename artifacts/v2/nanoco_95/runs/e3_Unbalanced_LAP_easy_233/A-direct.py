import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    attorneys = list(range(8))
    documents = list(range(4))

    model = pyo.ConcreteModel()

    model.attorneys = pyo.Set(initialize=attorneys)
    model.documents = pyo.Set(initialize=documents)

    model.x = pyo.Var(model.attorneys, model.documents, domain=pyo.Binary)

    def objective_rule(m):
        return sum(
            cost_matrix[i][j] * m.x[i, j]
            for i in m.attorneys
            for j in m.documents
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def document_rule(m, j):
        return sum(m.x[i, j] for i in m.attorneys) == 1

    model.document_constraint = pyo.Constraint(model.documents, rule=document_rule)

    def attorney_rule(m, i):
        return sum(m.x[i, j] for j in m.documents) <= 1

    model.attorney_constraint = pyo.Constraint(model.attorneys, rule=attorney_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}