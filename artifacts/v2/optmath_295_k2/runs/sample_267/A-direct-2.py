import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost_type0 = params["fixed_cost_type0"]
    fixed_cost_type1 = params["fixed_cost_type1"]
    var_cost_type0 = params["var_cost_type0"]
    var_cost_type1 = params["var_cost_type1"]
    start_cost_type0 = params["start_cost_type0"]
    start_cost_type1 = params["start_cost_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    capac_req = params["capac_req"]
    max_operational_type0 = params["max_operational_type0"]
    max_operational_type1 = params["max_operational_type1"]
    max_start_period0_type0 = params["max_start_period0_type0"]
    max_start_period0_type1 = params["max_start_period0_type1"]

    periods = list(range(5))
    types = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods, ordered=True)
    model.T = pyo.Set(initialize=types, ordered=True)

    model.n_oper = pyo.Var(model.T, model.P, domain=pyo.NonNegativeIntegers)
    model.n_start = pyo.Var(model.T, model.P, domain=pyo.NonNegativeIntegers)
    model.gen = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        total = 0
        for t in m.T:
            fc = fixed_cost_type0 if t == 0 else fixed_cost_type1
            vc = var_cost_type0 if t == 0 else var_cost_type1
            sc = start_cost_type0 if t == 0 else start_cost_type1
            for p in m.P:
                total += fc * m.n_oper[t, p]
                total += vc * m.gen[t, p]
                total += sc * m.n_start[t, p]
        return total

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def demand_rule(m, p):
        return m.gen[0, p] + m.gen[1, p] >= demand[p]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def gen_min_t0_rule(m, p):
        return m.gen[0, p] >= min_output_type0 * m.n_oper[0, p]

    def gen_max_t0_rule(m, p):
        return m.gen[0, p] <= max_output_type0 * m.n_oper[0, p]

    def gen_min_t1_rule(m, p):
        return m.gen[1, p] >= min_output_type1 * m.n_oper[1, p]

    def gen_max_t1_rule(m, p):
        return m.gen[1, p] <= max_output_type1 * m.n_oper[1, p]

    model.gen_min_t0 = pyo.Constraint(model.P, rule=gen_min_t0_rule)
    model.gen_max_t0 = pyo.Constraint(model.P, rule=gen_max_t0_rule)
    model.gen_min_t1 = pyo.Constraint(model.P, rule=gen_min_t1_rule)
    model.gen_max_t1 = pyo.Constraint(model.P, rule=gen_max_t1_rule)

    def capac_rule(m, p):
        return max_output_type0 * m.n_oper[0, p] + max_output_type1 * m.n_oper[1, p] >= capac_req[p]

    model.capac_con = pyo.Constraint(model.P, rule=capac_rule)

    def max_oper_t0_rule(m, p):
        return m.n_oper[0, p] <= max_operational_type0

    def max_oper_t1_rule(m, p):
        return m.n_oper[1, p] <= max_operational_type1

    model.max_oper_t0 = pyo.Constraint(model.P, rule=max_oper_t0_rule)
    model.max_oper_t1 = pyo.Constraint(model.P, rule=max_oper_t1_rule)

    def start0_period0_rule(m):
        return m.n_start[0, 0] <= max_start_period0_type0

    def start1_period0_rule(m):
        return m.n_start[1, 0] <= max_start_period0_type1

    model.start0_period0 = pyo.Constraint(rule=start0_period0_rule)
    model.start1_period0 = pyo.Constraint(rule=start1_period0_rule)

    def start_t0_later_rule(m, p):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_start[0, p] <= m.n_oper[0, p - 1]

    def start_t1_later_rule(m, p):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_start[1, p] <= m.n_oper[1, p - 1]

    model.start_t0_later = pyo.Constraint(model.P, rule=start_t0_later_rule)
    model.start_t1_later = pyo.Constraint(model.P, rule=start_t1_later_rule)

    def oper_t0_rule(m, p):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_oper[0, p] <= m.n_oper[0, p - 1] + m.n_start[0, p]

    def oper_t1_rule(m, p):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_oper[1, p] <= m.n_oper[1, p - 1] + m.n_start[1, p]

    model.oper_t0 = pyo.Constraint(model.P, rule=oper_t0_rule)
    model.oper_t1 = pyo.Constraint(model.P, rule=oper_t1_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}