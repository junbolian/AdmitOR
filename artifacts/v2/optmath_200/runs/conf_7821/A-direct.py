import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    P = 4
    # generator type data
    types = [0, 1]
    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    min_out = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_out = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    var_cost = params["var_cost"]
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]
    max_op = {
        0: params["max_operating_type0"],
        1: params["max_operating_type1"],
    }
    type1_init_slack = params["type1_initial_slack"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, P - 1)
    model.G = pyo.Set(initialize=types)

    # variables
    model.gen_on = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers,
                           bounds=lambda m, t, p: (0, max_op[t]))
    model.prod = pyo.Var(model.G, model.T, domain=pyo.NonNegativeReals)
    model.startup = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)

    # production bounds linked to operating generators
    def prod_min_rule(m, t, p):
        return m.prod[t, p] >= min_out[t] * m.gen_on[t, p]

    def prod_max_rule(m, t, p):
        return m.prod[t, p] <= max_out[t] * m.gen_on[t, p]

    model.prod_min = pyo.Constraint(model.G, model.T, rule=prod_min_rule)
    model.prod_max = pyo.Constraint(model.G, model.T, rule=prod_max_rule)

    # demand satisfaction
    def demand_rule(m, p):
        return m.prod[0, p] + m.prod[1, p] >= demand[p]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    # reserve margin
    def reserve_rule(m, p):
        return (max_out[0] * m.gen_on[0, p] + max_out[1] * m.gen_on[1, p]
                >= (1.0 + reserve_margin) * demand[p])

    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    # startup logic for Type 0
    def startup0_p0_rule(m):
        return m.gen_on[0, 0] <= m.startup[0, 0]

    def startup0_rule(m, p):
        return m.gen_on[0, p] <= m.gen_on[0, p - 1] + m.startup[0, p]

    model.startup0_p0 = pyo.Constraint(rule=startup0_p0_rule)
    model.startup0 = pyo.Constraint(pyo.RangeSet(1, P - 1), rule=startup0_rule)

    # Type 1 special constraint: gen_on - startup <= slack
    def startup1_rule(m, p):
        return m.gen_on[1, p] - m.startup[1, p] <= type1_init_slack

    model.startup1 = pyo.Constraint(model.T, rule=startup1_rule)

    # objective
    def obj_rule(m):
        total = 0
        for t in types:
            for p in m.T:
                total += base_cost[t] * m.gen_on[t, p]
                total += var_cost * m.prod[t, p]
                total += startup_cost[t] * m.startup[t, p]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}