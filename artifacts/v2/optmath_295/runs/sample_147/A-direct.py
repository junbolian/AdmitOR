import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = params["num_periods"]

    base0 = params["base_cost_type0"]
    base1 = params["base_cost_type1"]
    var0 = params["var_cost_type0"]
    var1 = params["var_cost_type1"]
    start0 = params["startup_cost_type0"]
    start1 = params["startup_cost_type1"]

    max0 = params["max_units_type0"]
    max1 = params["max_units_type1"]

    demand = params["demand"]
    minout0 = params["min_output_type0"]
    maxout0 = params["max_output_type0"]
    minout1 = params["min_output_type1"]
    maxout1 = params["max_output_type1"]

    reserve = params["reserve_margin"]

    mstart0 = params["max_startup_type0_period0"]
    mstart1 = params["max_startup_type1_period0"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)

    model.n0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds=(0, max0))
    model.n1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds=(0, max1))
    model.g0 = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.g1 = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.s0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.s1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, t):
        return m.g0[t] + m.g1[t] >= demand[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    def reserve_rule(m, t):
        return maxout0 * m.n0[t] + maxout1 * m.n1[t] >= (1.0 + reserve) * demand[t]

    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    def gen0_lo(m, t):
        return m.g0[t] >= minout0 * m.n0[t]

    def gen0_hi(m, t):
        return m.g0[t] <= maxout0 * m.n0[t]

    def gen1_lo(m, t):
        return m.g1[t] >= minout1 * m.n1[t]

    def gen1_hi(m, t):
        return m.g1[t] <= maxout1 * m.n1[t]

    model.gen0_lo_con = pyo.Constraint(model.T, rule=gen0_lo)
    model.gen0_hi_con = pyo.Constraint(model.T, rule=gen0_hi)
    model.gen1_lo_con = pyo.Constraint(model.T, rule=gen1_lo)
    model.gen1_hi_con = pyo.Constraint(model.T, rule=gen1_hi)

    model.s0[0].setlb(0)
    model.s0[0].setub(mstart0)
    model.s1[0].setlb(0)
    model.s1[0].setub(mstart1)

    def startup0_rule(m, t):
        return m.s0[t] <= m.n0[t - 1]

    def startup1_rule(m, t):
        return m.s1[t] <= m.n1[t - 1]

    model.startup0_con = pyo.Constraint(pyo.RangeSet(1, T - 1), rule=startup0_rule)
    model.startup1_con = pyo.Constraint(pyo.RangeSet(1, T - 1), rule=startup1_rule)

    def cost_rule(m):
        total = 0
        for t in m.T:
            total += base0 * m.n0[t] + base1 * m.n1[t]
            total += var0 * m.g0[t] + var1 * m.g1[t]
            total += start0 * m.s0[t] + start1 * m.s1[t]
        return total

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}