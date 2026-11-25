import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 13

    model = pyo.ConcreteModel()

    model.x = pyo.Var(range(n), domain=pyo.Binary)

    values = [params["value_%d" % i] for i in range(n)]
    costs = [params["cost_%d" % i] for i in range(n)]

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in range(n)),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(costs[i] * model.x[i] for i in range(n)) <= params["budget"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}