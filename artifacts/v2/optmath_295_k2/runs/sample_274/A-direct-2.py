import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    flight_capacity = params["flight_capacity"]

    n_packages = len(revenue)
    n_legs = len(flight_capacity)

    # Structural incidence: which packages use which flight legs
    legs_for_package = {
        0: [1],
        1: [0, 3, 4],
        2: [0, 1, 2],
        3: [2, 4],
        4: [0, 1, 2],
        5: [0],
        6: [0, 1, 3, 4],
        7: [0, 3, 4],
        8: [1, 4],
        9: [1, 4],
        10: [1, 2, 3],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_packages - 1)
    model.L = pyo.RangeSet(0, n_legs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.revenue_expr = pyo.Expression(
        expr=sum(revenue[j] * model.x[j] for j in model.P)
    )

    def demand_rule(mdl, j):
        return mdl.x[j] <= demand_limit[j]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def leg_rule(mdl, i):
        packages_on_leg = [j for j in range(n_packages) if i in legs_for_package[j]]
        return sum(mdl.x[j] for j in packages_on_leg) <= flight_capacity[i]

    model.leg_con = pyo.Constraint(model.L, rule=leg_rule)

    model.obj = pyo.Objective(expr=model.revenue_expr, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": f"failed: {type(exc).__name__}"}