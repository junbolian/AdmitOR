import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]

    days = list(range(7))  # 0=Monday ... 6=Sunday

    model = pyo.ConcreteModel()

    # x[s] = number of employees whose two-day off block starts on day s.
    # Working days are the 5 consecutive days following the off block.
    # Off pair for shift starting day s: {s, (s+1) mod 7}.
    model.S = pyo.Set(initialize=days)
    model.x = pyo.Var(model.S, domain=pyo.NonNegativeReals)

    def on_duty_rule(m, d):
        # employees are on duty on day d unless their off block includes d
        return sum(
            m.x[s]
            for s in m.S
            if d != s and d != (s + 1) % 7
        ) >= requirements[d]

    model.demand = pyo.Constraint(model.S, rule=on_duty_rule)

    model.total = pyo.Objective(
        expr=sum(model.x[s] for s in model.S),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:120]}