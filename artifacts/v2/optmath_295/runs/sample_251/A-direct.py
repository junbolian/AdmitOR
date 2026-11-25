import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    packages = list(range(11))
    legs = list(range(7))

    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    usage = {
        0: [2, 3, 4, 5, 7, 9],
        1: [0, 2, 3, 4, 9, 10],
        2: [7, 8, 10],
        3: [2, 3, 5],
        4: [1, 2, 4, 8, 9],
        5: [3, 5, 6, 7, 8, 9],
        6: [0, 1, 3, 4, 5, 9],
    }
    legs_for_package = {
        p: [leg for leg in legs if p in usage[leg]] for p in packages
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=packages)
    model.L = pyo.Set(initialize=legs)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(revenue[p] * model.x[p] for p in model.P),
        sense=pyo.maximize,
    )

    model.demand_con = pyo.Constraint(
        model.P, rule=lambda m, p: m.x[p] <= demand[p]
    )

    def leg_rule(m, leg):
        return sum(m.x[p] for p in usage[leg]) <= capacity[leg]

    model.cap_con = pyo.Constraint(model.L, rule=leg_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}