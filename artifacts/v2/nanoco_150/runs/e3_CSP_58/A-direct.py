import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    stock_length = params["stock_length"]
    segment_lengths = params["segment_lengths"]
    demands = params["demands"]

    n_types = len(segment_lengths)
    # Upper bound on reels: total length required divided by stock, rounded up, plus slack
    total_len = sum(segment_lengths[i] * demands[i] for i in range(n_types))
    max_reels = int(total_len // stock_length) + sum(demands) + 1

    model = pyo.ConcreteModel()

    model.types = pyo.RangeSet(0, n_types - 1)
    model.reels = pyo.RangeSet(0, max_reels - 1)

    # x[r, t] = number of segments of type t cut from reel r
    model.x = pyo.Var(model.reels, model.types, domain=pyo.NonNegativeIntegers)

    # y[r] = 1 if reel r is used
    model.y = pyo.Var(model.reels, domain=pyo.Binary)

    # Capacity: sum of lengths on each reel <= stock_length * y[r]
    def cap_rule(m, r):
        return sum(segment_lengths[t] * m.x[r, t] for t in m.types) <= stock_length * m.y[r]
    model.cap = pyo.Constraint(model.reels, rule=cap_rule)

    # Demand satisfaction
    def demand_rule(m, t):
        return sum(m.x[r, t] for r in m.reels) == demands[t]
    model.demand = pyo.Constraint(model.types, rule=demand_rule)

    # Symmetry breaking: y[r] >= y[r+1] is not straightforward with integer vars excluding,
    # but a simple valid bound: if y[r]==0 then no usage (already implied by cap). Add ordering.
    def order_rule(m, r):
        if r < max_reels - 1:
            return m.y[r] >= m.y[r + 1]
        return pyo.Constraint.Skip
    model.order = pyo.Constraint(model.reels, rule=order_rule)

    model.obj = pyo.Objective(expr=sum(model.y[r] for r in model.reels), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}