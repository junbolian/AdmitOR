import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    budget = params["budget"]

    n = len(values)

    model = pyo.ConcreteModel(name="campaign_knapsack")

    model.x = pyo.Var(range(n), domain=pyo.Binary)

    model.profit = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in range(n)),
        sense=pyo.maximize,
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in range(n)) <= budget
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}