import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    req = [params["req_1"], params["req_2"], params["req_3"],
           params["req_4"], params["req_5"], params["req_6"]]
    shift_length = params["shift_length"]

    num_periods = 6
    periods = list(range(6))

    # Each start covers shift_length consecutive periods (cyclically)
    covers = [[(s + k) % num_periods for k in range(int(shift_length))]
              for s in periods]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(periods, domain=pyo.NonNegativeReals)

    def demand_rule(model, t):
        return sum(model.x[s] for s in periods if t in covers[s]) >= req[t]
    model.demand = pyo.Constraint(periods, rule=demand_rule)

    model.obj = pyo.Objective(expr=sum(model.x[s] for s in periods),
                              sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}