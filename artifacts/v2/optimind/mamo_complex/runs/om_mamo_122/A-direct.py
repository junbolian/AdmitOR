import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)

    model = pyo.ConcreteModel()
    model.cities_from = pyo.Set(initialize=range(n))
    model.cities_to = pyo.Set(initialize=range(n))

    model.flow = pyo.Var(model.cities_from, model.cities_to, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.flow[i, j]
                 for i in model.cities_from
                 for j in model.cities_to
                 if i != j),
        sense=pyo.minimize,
    )

    model.supply_con = pyo.Constraint(
        model.cities_from,
        rule=lambda m, i: sum(m.flow[i, j] for j in m.cities_to if j != i) <= supply[i],
    )

    model.demand_con = pyo.Constraint(
        model.cities_to,
        rule=lambda m, j: sum(m.flow[i, j] for i in m.cities_from if i != j) >= demand[j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}