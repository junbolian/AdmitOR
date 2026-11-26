import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = [params["d1"], params["d2"], params["d3"], params["d4"],
              params["d5"], params["d6"], params["d7"]]

    model = pyo.ConcreteModel()

    # x[j] = number of nurses whose 5-day shift starts on day j
    model.J = pyo.RangeSet(1, 7)
    model.x = pyo.Var(model.J, within=pyo.NonNegativeReals)

    def demand_rule(mdl, i):
        # nurses starting on days i, i-1, ..., i-4 (mod 7) cover day i
        return sum(mdl.x[((i - k - 1) % 7) + 1] for k in range(5)) >= demand[i - 1]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    model.obj = pyo.Objective(expr=sum(model.x[j] for j in model.J),
                              sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}