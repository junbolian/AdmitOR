import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    labor_A = params["labor_A"]
    assembly_B = params["assembly_B"]
    labor_A_heater = params["labor_A_heater"]
    assembly_B_heater = params["assembly_B_heater"]
    inspect_cost_mw = params["inspect_cost_mw"]
    inspect_cost_wh = params["inspect_cost_wh"]
    cap_A = params["cap_A"]
    cap_B = params["cap_B"]
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    demand_mw = params["demand_mw"]
    demand_wh = params["demand_wh"]
    inspect_budget = params["inspect_budget"]
    target_mw = params["target_mw"]
    target_wh = params["target_wh"]
    overtime_A_cap = params["overtime_A_cap"]

    model = pyo.ConcreteModel()

    # Decision variables
    model.mw = pyo.Var(domain=pyo.NonNegativeReals)
    model.wh = pyo.Var(domain=pyo.NonNegativeReals)
    model.over_A = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, overtime_A_cap))

    # Workshop A regular usage
    def reg_A_rule(m):
        return labor_A * m.mw + labor_A_heater * m.wh
    model.reg_A = pyo.Expression(rule=reg_A_rule)

    def use_B_rule(m):
        return assembly_B * m.mw + assembly_B_heater * m.wh
    model.use_B = pyo.Expression(rule=use_B_rule)

    # Deviation variables (only over-achievement / under-achievement as needed)
    # P1: inspection cost over budget
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)
    # P2: microwave sales below target
    model.d2_minus = pyo.Var(domain=pyo.NonNegativeReals)
    # P3: idle hours of A and B
    model.d3_A = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3_B = pyo.Var(domain=pyo.NonNegativeReals)
    # P4: overtime over cap
    model.d4_plus = pyo.Var(domain=pyo.NonNegativeReals)
    # P5: water heater sales below target
    model.d5_minus = pyo.Var(domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_A_rule(m):
        return m.reg_A <= cap_A + m.over_A
    model.cap_A_con = pyo.Constraint(rule=cap_A_rule)

    def cap_B_rule(m):
        return m.use_B <= cap_B
    model.cap_B_con = pyo.Constraint(rule=cap_B_rule)

    # Sales ceilings
    def demand_mw_rule(m):
        return m.mw <= demand_mw
    model.demand_mw_con = pyo.Constraint(rule=demand_mw_rule)

    def demand_wh_rule(m):
        return m.wh <= demand_wh
    model.demand_wh_con = pyo.Constraint(rule=demand_wh_rule)

    # P1: inspection cost + d1_plus >= budget  (over-budget penalized)
    def p1_rule(m):
        return inspect_cost_mw * m.mw + inspect_cost_wh * m.wh <= inspect_budget + m.d1_plus
    model.p1_con = pyo.Constraint(rule=p1_rule)

    # P2: mw + d2_minus >= target_mw
    def p2_rule(m):
        return m.mw + m.d2_minus >= target_mw
    model.p2_con = pyo.Constraint(rule=p2_rule)

    # P3: idle hours (full utilization target)
    def p3_A_rule(m):
        return m.d3_A >= (cap_A + m.over_A) - m.reg_A
    model.p3_A_con = pyo.Constraint(rule=p3_A_rule)

    def p3_B_rule(m):
        return m.d3_B >= cap_B - m.use_B
    model.p3_B_con = pyo.Constraint(rule=p3_B_rule)

    # P4: over_A <= overtime_A_cap + d4_plus
    def p4_rule(m):
        return m.over_A <= overtime_A_cap + m.d4_plus
    model.p4_con = pyo.Constraint(rule=p4_rule)

    # P5: wh + d5_minus >= target_wh
    def p5_rule(m):
        return m.wh + m.d5_minus >= target_wh
    model.p5_con = pyo.Constraint(rule=p5_rule)

    # Lexicographic objective via large weights
    BIG = 1e5
    w1 = BIG ** 5
    w2 = BIG ** 4
    w3_A = BIG ** 3 * cost_A
    w3_B = BIG ** 3 * cost_B
    w4 = BIG ** 2
    w5 = BIG ** 1

    def obj_rule(m):
        return (w1 * m.d1_plus
                + w2 * m.d2_minus
                + w3_A * m.d3_A + w3_B * m.d3_B
                + w4 * m.d4_plus
                + w5 * m.d5_minus)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}