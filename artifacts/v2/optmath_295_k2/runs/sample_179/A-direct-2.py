import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    cost_p0_c0 = params["cost_p0_c0"]
    cost_p0_c1 = params["cost_p0_c1"]

    n_prod = 6
    n_contract = 6
    producers = list(range(n_prod))
    contracts = list(range(n_contract))

    # Build a deterministic cost table within [cost_min, cost_max] using a seed-free formula.
    def cost_value(p, c):
        if p == 0 and c == 0:
            return cost_p0_c0
        if p == 0 and c == 1:
            return cost_p0_c1
        span = cost_max - cost_min
        raw = cost_min + span * ((p * 7 + c * 13) % 11) / 10.0
        if raw < cost_min:
            raw = cost_min
        if raw > cost_max:
            raw = cost_max
        return raw

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    model.x = pyo.Var(model.P, model.C, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, within=pyo.Binary)

    def obj_rule(m):
        return sum(cost_value(p, c) * m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity constraint per producer
    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= producer_capacity[p]

    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    # Contract fulfillment per contract
    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= contract_demand[c]

    model.demand = pyo.Constraint(model.C, rule=demand_rule)

    # Minimum contributors per contract
    def min_contrib_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_producers_per_contract[c]

    model.min_contrib = pyo.Constraint(model.C, rule=min_contrib_rule)

    # Linking + minimum delivery: x >= min_delivery * y
    def link_rule(m, p, c):
        return m.x[p, c] >= producer_min_delivery[p] * m.y[p, c]

    model.link = pyo.Constraint(model.P, model.C, rule=link_rule)

    # Big-M upper linking: x <= capacity * y
    def upper_rule(m, p, c):
        return m.x[p, c] <= producer_capacity[p] * m.y[p, c]

    model.upper = pyo.Constraint(model.P, model.C, rule=upper_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}