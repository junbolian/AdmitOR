import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    T = [1, 2, 3, 4]
    P = ['I', 'II', 'III']

    hours_per_unit = {
        'I': params["hours_per_unit_I"],
        'II': params["hours_per_unit_II"],
        'III': params["hours_per_unit_III"],
    }
    orders = {
        'I': params["orders_I"],
        'II': params["orders_II"],
        'III': params["orders_III"],
    }
    comp_rate = {
        'I': params["compensation_per_unit_per_quarter_I_II"],
        'II': params["compensation_per_unit_per_quarter_I_II"],
        'III': params["compensation_per_unit_per_quarter_III"],
    }
    end_inv = params["ending_inventory_required"]
    storage = params["storage_fee_per_unit_per_quarter"]
    hours_avail = params["production_hours_per_quarter"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=T)
    model.P = pyo.Set(initialize=P)

    # production quantities
    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    # unmet/delivered-late amount: undelivered units carried (backlog)
    # Track inventory (finished goods) and backlog accumulated per period.
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.deficit = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    # product I cannot be produced in quarter 2
    model.prod['I', 2].fix(0)

    # Production time constraint per quarter
    model.prod_time = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(hours_per_unit[p] * m.prod[p, t] for p in m.P) <= hours_avail
    )

    # Product I cannot be produced in Q2
    # (handled via fix above)

    # Flow balance with backlog:
    # inv[p,t] - deficit[p,t] = inv[p,t-1] - deficit[p,t-1] + prod[p,t] - orders[p][t-1]
    def balance_rule(m, p, t):
        o = orders[p][t - 1]
        if t == 1:
            prev_inv = 0
            prev_def = 0
        else:
            prev_inv = m.inv[p, t - 1]
            prev_def = m.deficit[p, t - 1]
        return m.inv[p, t] - m.deficit[p, t] == prev_inv - prev_def + m.prod[p, t] - o
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Ending inventory requirement at end of Q4
    model.end_req = pyo.Constraint(model.P, rule=lambda m, p: m.inv[p, 4] >= end_inv)

    # Can't both have inventory and backlog at the final period meaningfully;
    # deficit in final period is not allowed to count toward ending inventory
    # (ending inventory handled above requires inv>=150, deficit>=0).

    # Objective: compensation for backlog carried in period t
    # (compensation is charged per quarter the product is late, i.e., deficit at end of each quarter)
    # storage fee on held inventory at end of each quarter.
    def obj_rule(m):
        comp = sum(comp_rate[p] * m.deficit[p, t] for p in m.P for t in m.T)
        hold = sum(storage * m.inv[p, t] for p in m.P for t in m.T)
        return comp + hold
    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {'objective': obj_val, 'status': 'optimal'}