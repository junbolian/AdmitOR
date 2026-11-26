# IR: {"sets":{"F":[1,2],"L":[1,2],"A":[[1,2],[2,1]]},"params":{"d":{"(1,2)":"d12","(2,1)":"d21"},"c":{"(1,1)":"c11","(1,2)":"c12","(2,1)":"c21","(2,2)":"c22"}},"variables":{"x[i,p]":"binary for i in F, p in L","y[i,j,p,q]":"continuous in [0,1] for (i,j) in A, p,q in L"},"constraints":["sum_p x[i,p] = 1 for i in F","sum_i x[i,p] = 1 for p in L","y[i,j,p,q] <= x[i,p] for (i,j) in A, p,q in L","y[i,j,p,q] <= x[j,q] for (i,j) in A, p,q in L","y[i,j,p,q] >= x[i,p] + x[j,q] - 1 for (i,j) in A, p,q in L"],"objective":"minimize sum_{(i,j) in A,p,q in L} d[i,j]*c[p,q]*y[i,j,p,q]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=[1, 2], ordered=True)
    model.L = pyo.Set(initialize=[1, 2], ordered=True)
    model.A = pyo.Set(
        dimen=2, initialize=[(1, 2), (2, 1)], ordered=True
    )

    model.d = pyo.Param(
        model.A,
        initialize={
            (1, 2): params["d12"],
            (2, 1): params["d21"],
        },
        within=pyo.Reals,
    )
    model.c = pyo.Param(
        model.L,
        model.L,
        initialize={
            (1, 1): params["c11"],
            (1, 2): params["c12"],
            (2, 1): params["c21"],
            (2, 2): params["c22"],
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)
    model.y = pyo.Var(
        model.A, model.L, model.L, domain=pyo.UnitInterval
    )

    def factory_assignment_rule(mdl, i):
        return sum(mdl.x[i, p] for p in mdl.L) == 1

    model.factory_assignment = pyo.Constraint(
        model.F, rule=factory_assignment_rule
    )

    def location_assignment_rule(mdl, p):
        return sum(mdl.x[i, p] for i in mdl.F) == 1

    model.location_assignment = pyo.Constraint(
        model.L, rule=location_assignment_rule
    )

    def product_first_upper_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] <= mdl.x[i, p]

    model.product_first_upper = pyo.Constraint(
        model.A, model.L, model.L, rule=product_first_upper_rule
    )

    def product_second_upper_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] <= mdl.x[j, q]

    model.product_second_upper = pyo.Constraint(
        model.A, model.L, model.L, rule=product_second_upper_rule
    )

    def product_lower_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] >= mdl.x[i, p] + mdl.x[j, q] - 1

    model.product_lower = pyo.Constraint(
        model.A, model.L, model.L, rule=product_lower_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.d[i, j] * model.c[p, q] * model.y[i, j, p, q]
            for i, j in model.A
            for p in model.L
            for q in model.L
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}