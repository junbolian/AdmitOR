import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fac = 4
    n_cus = 10

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    # shipping_cost may be missing or partially specified; default to 0 for unknown entries
    shipping_cost = params.get("shipping_cost", None)

    def _ship_cost(i, j):
        if shipping_cost is None:
            return 0
        try:
            row = shipping_cost[i]
        except (KeyError, IndexError, TypeError):
            return 0
        try:
            val = row[j]
        except (KeyError, IndexError, TypeError):
            return 0
        if val is None:
            return 0
        return val

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUS = pyo.RangeSet(0, n_cus - 1)

    model.is_open = pyo.Var(model.FAC, domain=pyo.Binary)
    model.ship = pyo.Var(model.FAC, model.CUS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.is_open[i] for i in m.FAC) + \
               sum(_ship_cost(i, j) * m.ship[i, j] for i in m.FAC for j in m.CUS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.FAC) == demand[j]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.CUS) <= capacity[i] * m.is_open[i]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}