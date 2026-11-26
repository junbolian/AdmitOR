def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    demand = [params[f"d{j}"] for j in range(1, 8)]

    model = pyo.ConcreteModel()

    # x[i] = number of nurses starting their 5-consecutive-day shift on day i
    model.x = pyo.Var(range(1, 8), within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(model.x[i] for i in range(1, 8)),
        sense=pyo.minimize,
    )

    def coverage_rule(m, j):
        # nurses working day j are those who started on j, j-1, ..., j-4 (mod 7)
        return sum(m.x[((j - k - 1) % 7) + 1] for k in range(5)) >= demand[j - 1]

    model.coverage = pyo.Constraint(range(1, 8), rule=coverage_rule)

    try:
        result = Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}