import pyomo.environ as pyo


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    flight_capacity = params["flight_capacity"]

    n_packages = len(revenue)
    n_legs = len(flight_capacity)

    leg_packages = {
        0: [1, 2, 4, 5, 6, 7],
        1: [0, 2, 4, 6, 8, 9, 10],
        2: [2, 3, 4, 10],
        3: [1, 6, 7, 10],
        4: [1, 3, 6, 7, 8, 9],
    }

    model = pyo.ConcreteModel()

    model.PACKAGES = pyo.RangeSet(0, n_packages - 1)
    model.LEGS = pyo.RangeSet(0, n_legs - 1)

    model.x = pyo.Var(model.PACKAGES, domain=pyo.NonNegativeIntegers)

    model.demand_con = pyo.Constraint(
        model.PACKAGES,
        rule=lambda m, p: m.x[p] <= demand_limit[p],
    )

    model.capacity_con = pyo.Constraint(
        model.LEGS,
        rule=lambda m, l: sum(m.x[p] for p in leg_packages[l])
        <= flight_capacity[l],
    )

    model.obj = pyo.Objective(
        expr=sum(revenue[p] * model.x[p] for p in model.PACKAGES),
        sense=pyo.maximize,
    )

    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": type(exc).__name__}

    return {"objective": obj_val, "status": "optimal"}