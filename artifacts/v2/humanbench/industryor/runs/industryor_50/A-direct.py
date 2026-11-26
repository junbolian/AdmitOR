import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]
    n = params["n"]

    stages = list(range(1, n + 1))

    model = pyo.ConcreteModel()
    model.S = pyo.Set(initialize=stages)

    # x[j] = number of new tools purchased (available) at start of stage j
    model.x = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    # s[j] = number of tools sent to slow repair at end of stage j
    model.s = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    # f[j] = number of tools sent to fast repair at end of stage j
    model.f = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)

    # Tools available (usable) at stage j:
    #   newly purchased x[j]
    #   + slow-repaired from stage j-p (finished at start of stage j)
    #   + fast-repaired from stage j-q
    # must meet requirement r[j], and the remainder is sent to repairs.
    def avail_rule(m, j):
        slow_ret = m.s[j - p] if (j - p) in stages else 0
        fast_ret = m.f[j - q] if (j - q) in stages else 0
        return m.x[j] + slow_ret + fast_ret
    model.avail = pyo.Expression(model.S, rule=avail_rule)

    # Tools used in stage j = r[j]; after the stage they are split into slow+fast repair.
    # Balance: available tools = used + slow + fast
    def bal_rule(m, j):
        return m.avail[j] == r[j] + m.s[j] + m.f[j]
    model.balance = pyo.Constraint(model.S, rule=bal_rule)

    # Objective: purchase cost + slow repair cost + fast repair cost
    def obj_rule(m):
        return (sum(a * m.x[j] for j in m.S)
                + sum(b * m.s[j] for j in m.S)
                + sum(c * m.f[j] for j in m.S))
    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}