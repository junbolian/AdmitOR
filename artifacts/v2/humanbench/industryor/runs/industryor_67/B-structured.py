# IR: {"sets":{"I":"range(n), n=len(params['d'])","P":"range(n)"},"params":{"d":"params['d']: nonempty n-by-n matrix of transportation quantities","c":"params['c']: n-by-n matrix of unit transportation costs"},"variables":{"x[i,p]":"binary: factory i occupies location p","z[i,j,p,q]":"continuous in [0,1]: x[i,p]*x[j,q]"},"constraints":["For each i: sum_p x[i,p] = 1","For each p: sum_i x[i,p] = 1","For each i,j,p,q: z[i,j,p,q] <= x[i,p]","For each i,j,p,q: z[i,j,p,q] <= x[j,q]","For each i,j,p,q: z[i,j,p,q] >= x[i,p] + x[j,q] - 1"],"objective":"minimize sum_{i,j,p,q} d[i][j]*c[p][q]*z[i,j,p,q]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Missing required data cannot be inferred or replaced with invented values.
    try:
        d = params["d"]
        c = params["c"]
    except KeyError as exc:
        return {"objective": None, "status": f"missing_parameter:{exc.args[0]}"}

    n = len(d)
    if (
        n == 0
        or len(c) != n
        or any(len(row) != n for row in d)
        or any(len(row) != n for row in c)
    ):
        return {"objective": None, "status": "invalid_matrix_dimensions"}

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=range(n), ordered=True)
    model.P = pyo.Set(initialize=range(n), ordered=True)

    model.x = pyo.Var(model.I, model.P, domain=pyo.Binary)
    model.z = pyo.Var(
        model.I, model.I, model.P, model.P, domain=pyo.UnitInterval
    )

    def factory_assignment_rule(mdl, i):
        return sum(mdl.x[i, p] for p in mdl.P) == 1

    model.factory_assignment = pyo.Constraint(
        model.I, rule=factory_assignment_rule
    )

    def location_assignment_rule(mdl, p):
        return sum(mdl.x[i, p] for i in mdl.I) == 1

    model.location_assignment = pyo.Constraint(
        model.P, rule=location_assignment_rule
    )

    def product_upper_first_rule(mdl, i, j, p, q):
        return mdl.z[i, j, p, q] <= mdl.x[i, p]

    model.product_upper_first = pyo.Constraint(
        model.I, model.I, model.P, model.P,
        rule=product_upper_first_rule,
    )

    def product_upper_second_rule(mdl, i, j, p, q):
        return mdl.z[i, j, p, q] <= mdl.x[j, q]

    model.product_upper_second = pyo.Constraint(
        model.I, model.I, model.P, model.P,
        rule=product_upper_second_rule,
    )

    def product_lower_rule(mdl, i, j, p, q):
        return mdl.z[i, j, p, q] >= mdl.x[i, p] + mdl.x[j, q] - 1

    model.product_lower = pyo.Constraint(
        model.I, model.I, model.P, model.P,
        rule=product_lower_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            d[i][j] * c[p][q] * model.z[i, j, p, q]
            for i in model.I
            for j in model.I
            for p in model.P
            for q in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi can raise when it cannot load a feasible solution.
        # Still determine success solely by objective retrieval below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}