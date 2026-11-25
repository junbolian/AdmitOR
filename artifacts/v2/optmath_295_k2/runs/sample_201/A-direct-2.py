import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    A = 6
    R = 7

    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, A - 1)
    model.route = pyo.RangeSet(0, R - 1)

    model.x = pyo.Var(model.aircraft, model.route, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(
            cost["aircraft_%d" % i][j] * model.x[i, j]
            for i in range(A)
            for j in range(R)
        ),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        model.aircraft,
        rule=lambda m, i: sum(m.x[i, j] for j in range(R)) <= availability["aircraft_%d" % i],
    )

    model.demand_con = pyo.Constraint(
        model.route,
        rule=lambda m, j: sum(
            capacity["aircraft_%d" % i][j] * m.x[i, j] for i in range(A)
        ) >= demand["route_%d" % j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}