import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    n_sec = len(price)
    n_cty = len(payoff)
    secs = list(range(n_sec))
    ctys = list(range(n_cty))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(secs, bounds=lambda m, i: (0, share_limit[i]))

    # Worst-case net revenue: auxiliary variable z <= revenue in every country
    model.z = pyo.Var()

    model.obj = pyo.Objective(expr=model.z, sense=pyo.maximize)

    def rev_rule(m, c):
        return m.z <= sum(payoff[c][i] * m.x[i] for i in secs) - sum(
            price[i] * m.x[i] for i in secs
        )

    model.rev_con = pyo.Constraint(ctys, rule=rev_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception as exc:
        return {'objective': None, 'status': str(exc) or 'failed'}