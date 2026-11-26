import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    order_widths = params["order_widths"]
    order_lengths = params["order_lengths"]
    stock_widths = params["stock_widths"]

    n_orders = len(order_widths)
    n_stock = len(stock_widths)

    model = pyo.ConcreteModel()

    model.ORDERS = pyo.RangeSet(0, n_orders - 1)
    model.STOCK = pyo.RangeSet(0, n_stock - 1)

    # y[j,k]: number of stock rolls of type j cut using pattern k (integer >= 0)
    # Pattern k = vector of counts (a[i,k]) of order i strips per stock roll of type j.
    # Because stock widths are few and small, enumerate integer cut patterns per stock type.

    # Build patterns per stock type: all nonneg integer vectors a with sum_i a[i]*w[i] <= W_j
    patterns = {}  # j -> list of tuples (length n_orders)
    for j in range(n_stock):
        W = stock_widths[j]
        pats = []

        def rec(i, rem, cur):
            if i == n_orders:
                pats.append(tuple(cur))
                return
            w = order_widths[i]
            maxc = int(rem // w) if w > 0 else 0
            for c in range(maxc + 1):
                cur.append(c)
                rec(i + 1, rem - c * w, cur)
                cur.pop()

        rec(0, W, [])
        patterns[j] = pats

    pattern_index = pyo.Set(initialize=range(max(len(v) for v in patterns.values())))
    model.PAT = pattern_index

    # Variable: number of times pattern p of stock type j is used (integer roll count)
    def var_init(mdl):
        for j in range(n_stock):
            for p_idx in range(len(patterns[j])):
                yield (j, p_idx)

    model.KEYS = pyo.Set(initialize=list(var_init(model)), dimen=2)
    model.y = pyo.Var(model.KEYS, domain=pyo.NonNegativeIntegers)

    # Total stock length used per order: sum_j sum_{p in pats[j]} y[j,p] * a[i,p] >= L_i
    def demand_rule(mdl, i):
        return sum(
            mdl.y[j, p] * patterns[j][p][i]
            for j in range(n_stock)
            for p in range(len(patterns[j]))
        ) >= order_lengths[i]

    model.demand = pyo.Constraint(model.ORDERS, rule=demand_rule)

    # Objective: minimize total stock area
    def obj_rule(mdl):
        total_stock_area = 0
        for j in range(n_stock):
            for p in range(len(patterns[j])):
                total_stock_area += mdl.y[j, p] * stock_widths[j]
        return total_stock_area

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "failed: " + str(exc)}