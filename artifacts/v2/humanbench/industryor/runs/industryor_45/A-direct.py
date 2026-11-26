import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    m = params["m"]
    H = params["H"]
    T = params["T"]
    b = params["b"]
    g = params["g"]
    n = int(params["n"])

    dt = T / n

    model = pyo.ConcreteModel()

    # Indices 0..n for states, 0..n-1 for control (forces at time k, k <= n-1)
    model.Ky = pyo.RangeSet(0, n)
    model.Ku = pyo.RangeSet(0, n - 1)

    model.y = pyo.Var(model.Ky, initialize=0.0)
    model.v = pyo.Var(model.Ky, initialize=0.0)
    model.u = pyo.Var(model.Ku, initialize=0.0, bounds=(-b, b))

    model.y[0].fix(0.0)
    model.v[0].fix(0.0)

    def velocity_rule(model, k):
        if k == 0:
            return pyo.Constraint.Skip
        return model.v[k] == model.v[k - 1] + (dt / m) * model.u[k - 1] - dt * g

    model.velocity_con = pyo.Constraint(model.Ky, rule=velocity_rule)

    def height_rule(model, k):
        if k == 0:
            return pyo.Constraint.Skip
        return model.y[k] == model.y[k - 1] + dt * model.v[k - 1]

    model.height_con = pyo.Constraint(model.Ky, rule=height_rule)

    model.reach = pyo.Constraint(expr=model.y[n] >= H)

    # Minimize total energy: integral of |u| => linear L1 formulation
    model.pos = pyo.Var(model.Ku, initialize=0.0, bounds=(0, None))
    model.neg = pyo.Var(model.Ku, initialize=0.0, bounds=(0, None))

    def force_split_rule(model, k):
        return model.u[k] == model.pos[k] - model.neg[k]

    model.force_split = pyo.Constraint(model.Ku, rule=force_split_rule)

    model.obj = pyo.Objective(
        expr=dt * sum(model.pos[k] + model.neg[k] for k in model.Ku),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}