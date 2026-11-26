import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock_3m_count = params["stock_3m_count"]
    stock_4m_count = params["stock_4m_count"]
    raw_length = params["raw_length"]
    piece_3m_length = params["piece_3m_length"]
    piece_4m_length = params["piece_4m_length"]

    max_3 = int(raw_length // piece_3m_length)
    max_4 = int(raw_length // piece_4m_length)

    patterns = []
    for i in range(max_3 + 1):
        for j in range(max_4 + 1):
            used = i * piece_3m_length + j * piece_4m_length
            if used <= raw_length and (i + j) > 0:
                patterns.append((i, j))

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, len(patterns) - 1)
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def meet_3m_rule(m):
        return sum(m.x[p] * patterns[p][0] for p in m.P) >= stock_3m_count

    def meet_4m_rule(m):
        return sum(m.x[p] * patterns[p][1] for p in m.P) >= stock_4m_count

    model.meet_3m = pyo.Constraint(rule=meet_3m_rule)
    model.meet_4m = pyo.Constraint(rule=meet_4m_rule)

    model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}