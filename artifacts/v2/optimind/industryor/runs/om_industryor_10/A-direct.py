import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price_A = params["price_A"]
    price_B = params["price_B"]

    hours_manuf_A = params["hours_manuf_A"]
    hours_asm_A = params["hours_asm_A"]
    hours_insp_A = params["hours_insp_A"]
    hours_manuf_B = params["hours_manuf_B"]
    hours_asm_B = params["hours_asm_B"]
    hours_insp_B = params["hours_insp_B"]

    cap_manuf = params["cap_manuf"]
    cap_asm = params["cap_asm"]
    cap_insp = params["cap_insp"]

    cost_manuf = params["cost_manuf"]
    cost_asm = params["cost_asm"]
    cost_insp = params["cost_insp"]

    profit_target = params["profit_target"]
    min_A_target = params["min_A_target"]

    model = pyo.ConcreteModel()

    # Decision variables: production quantities
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    # Goal deviation variables (under/over achievements)
    # p1: profit >= profit_target -> minimize under-achievement d1_minus
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)
    # p2: xA >= min_A_target -> minimize under-achievement d2_minus
    model.d2_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # Idle time slack variables for each process (idle = capacity - used)
    model.idle_manuf = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle_asm = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle_insp = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective weights: lexicographic via large weights for p1, p2, then idle costs
    W1 = 1e6
    W2 = 1e5
    W3 = 1.0

    def obj_rule(m):
        return (
            W1 * m.d1_minus
            + W2 * m.d2_minus
            + W3 * (cost_manuf * m.idle_manuf + cost_asm * m.idle_asm + cost_insp * m.idle_insp)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Profit goal constraint: profit + d1_minus - d1_plus = profit_target
    # Profit = revenue - cost = price_A*xA + price_B*xB - (cost per hour * hours used)
    def profit_rule(m):
        revenue = price_A * m.xA + price_B * m.xB
        cost = (
            cost_manuf * (hours_manuf_A * m.xA + hours_manuf_B * m.xB)
            + cost_asm * (hours_asm_A * m.xA + hours_asm_B * m.xB)
            + cost_insp * (hours_insp_A * m.xA + hours_insp_B * m.xB)
        )
        return revenue - cost + m.d1_minus - m.d1_plus == profit_target

    model.profit_goal = pyo.Constraint(rule=profit_rule)

    # Min A production goal: xA + d2_minus - d2_plus = min_A_target
    def min_A_rule(m):
        return m.xA + m.d2_minus - m.d2_plus == min_A_target

    model.min_A_goal = pyo.Constraint(rule=min_A_rule)

    # Capacity (no overtime) constraints with idle time
    def manuf_cap_rule(m):
        return hours_manuf_A * m.xA + hours_manuf_B * m.xB + m.idle_manuf == cap_manuf

    model.manuf_cap = pyo.Constraint(rule=manuf_cap_rule)

    def asm_cap_rule(m):
        return hours_asm_A * m.xA + hours_asm_B * m.xB + m.idle_asm == cap_asm

    model.asm_cap = pyo.Constraint(rule=asm_cap_rule)

    def insp_cap_rule(m):
        return hours_insp_A * m.xA + hours_insp_B * m.xB + m.idle_insp == cap_insp

    model.insp_cap = pyo.Constraint(rule=insp_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}