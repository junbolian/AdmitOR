import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = [f"aircraft_{i}" for i in range(5)]
    route = [f"route_{j}" for j in range(6)]

    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    def norm(d):
        # accept dict-of-dicts or flat "a,b" / "a_x" style keys
        if all(isinstance(v, dict) for v in d.values()):
            return d
        out = {}
        for k, v in d.items():
            if isinstance(k, tuple):
                a, r = k
            elif "," in k:
                a, r = k.split(",")
            else:
                for aa in aircraft:
                    if k.startswith(aa + "_"):
                        a, r = aa, k[len(aa) + 1:]
                        break
                else:
                    continue
            out.setdefault(a.strip(), {})[r.strip()] = v
        return out

    capacity = norm(capacity)
    cost = norm(cost)

    def get(mat, a, r, default):
        return mat.get(a, {}).get(r, default)

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=route)
    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(get(cost, a, r, 0) * model.x[a, r] for a in model.A for r in model.R),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        model.A,
        rule=lambda m, a: sum(m.x[a, r] for r in m.R) <= availability[a],
    )

    model.demand_con = pyo.Constraint(
        model.R,
        rule=lambda m, r: sum(
            get(capacity, a, r, 0) * m.x[a, r] for a in m.A
        ) >= demand[r],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}