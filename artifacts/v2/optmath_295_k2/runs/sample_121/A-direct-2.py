import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n_origins = 14
    n_destinations = 12

    I = range(n_origins)
    J = range(n_destinations)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(I))
    model.J = pyo.Set(initialize=list(J))

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}