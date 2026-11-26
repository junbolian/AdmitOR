import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
    }
    price = {
        1: params["price_1month"],
        2: params["price_2month"],
        3: params["price_3month"],
        4: params["price_4month"],
    }

    durations = [1, 2, 3, 4]
    months = [1, 2, 3, 4]
    # Valid contracts: (start, duration) with start + duration - 1 <= 4
    contracts = [(t, k) for t in months for k in durations if t + k - 1 <= 4]

    model = pyo.ConcreteModel()
    model.contracts = pyo.Set(initialize=contracts, dimen=2)

    # area[t,k] = m^2 rented under a contract starting at month t lasting k months
    model.area = pyo.Var(model.contracts, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(
            price[k] * k * m.area[t, k] for (t, k) in contracts
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cover_rule(m, month):
        return sum(
            m.area[t, k]
            for (t, k) in contracts
            if t <= month <= t + k - 1
        ) >= demand[month]

    model.cover = pyo.Constraint(months, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}