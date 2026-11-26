import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    min_req = params["min_waitstaff"]

    # Six 4-hour time blocks; each worker works 8 hours = 2 consecutive blocks.
    # shift s starts at block s and covers blocks (s, s+1 mod 6)
    n_blocks = 6

    model = pyo.ConcreteModel()
    model.SHIFTS = pyo.RangeSet(0, n_blocks - 1)

    # Number of workers assigned to each 2-block shift
    model.x = pyo.Var(model.SHIFTS, domain=pyo.NonNegativeReals)

    # Each block's demand must be met; block b is covered by shifts b and b-1
    def demand_rule(m, b):
        return m.x[b] + m.x[(b - 1) % n_blocks] >= min_req[b]

    model.demand = pyo.Constraint(pyo.RangeSet(0, n_blocks - 1), rule=demand_rule)

    def obj_rule(m):
        return sum(m.x[s] for s in m.SHIFTS)

    model.total = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total))
    return {"objective": obj_val, "status": "optimal"}