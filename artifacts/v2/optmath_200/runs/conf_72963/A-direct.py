import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost = params["base_cost_per_generator_per_period"]
    power_cost = params["power_cost_per_mw"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    demand_per_period = params["demand_per_period"]
    capacity_margin_demand = params["capacity_margin_demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    max_generators_per_type_per_period = params["max_generators_per_type_per_period"]
    t0_offset = params["type0_period0_operating_limit_offset"]
    t1_offset = params["type1_period0_operating_limit_offset"]

    periods = [0, 1, 2]
    types = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.T = pyo.Set(initialize=types)

    # Number of generators operating
    model.n_operating = pyo.Var(model.T, model.P, domain=pyo.NonNegativeIntegers)
    # Power output per generator
    model.power = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)
    # Number of generators started
    model.n_started = pyo.Var(model.T, model.P, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        total = 0
        for t in m.T:
            for p in m.P:
                total += base_cost * m.n_operating[t, p]
                total += power_cost * m.power[t, p]
                if t == 0:
                    total += startup_cost_type0 * m.n_started[t, p]
                else:
                    total += startup_cost_type1 * m.n_started[t, p]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand constraint: total power >= demand
    def demand_rule(m, p):
        return m.power[0, p] + m.power[1, p] >= demand_per_period[p]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    # Capacity margin constraint: max output capacity >= 115% demand
    def capacity_rule(m, p):
        return (max_output_type0 * m.n_operating[0, p]
                + max_output_type1 * m.n_operating[1, p]) >= capacity_margin_demand[p]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    # Power output bounds (only relevant when operating; if n_operating=0, power=0)
    def power_upper_type0(m, p):
        return m.power[0, p] <= max_output_type0 * m.n_operating[0, p]

    def power_lower_type0(m, p):
        return m.power[0, p] >= min_output_type0 * m.n_operating[0, p]

    def power_upper_type1(m, p):
        return m.power[1, p] <= max_output_type1 * m.n_operating[1, p]

    def power_lower_type1(m, p):
        return m.power[1, p] >= min_output_type1 * m.n_operating[1, p]

    model.power_upper_t0 = pyo.Constraint(model.P, rule=power_upper_type0)
    model.power_lower_t0 = pyo.Constraint(model.P, rule=power_lower_type0)
    model.power_upper_t1 = pyo.Constraint(model.P, rule=power_upper_type1)
    model.power_lower_t1 = pyo.Constraint(model.P, rule=power_lower_type1)

    # Max generators operating per type per period
    def max_gen_rule(m, t, p):
        return m.n_operating[t, p] <= max_generators_per_type_per_period

    model.max_gen_con = pyo.Constraint(model.T, model.P, rule=max_gen_rule)

    # Period 0 operating limit offsets
    def t0_period0_rule(m):
        return m.n_operating[0, 0] <= t0_offset + m.n_started[0, 0]

    def t1_period0_rule(m):
        return m.n_operating[1, 0] <= t1_offset + m.n_started[1, 0]

    model.t0_period0_con = pyo.Constraint(rule=t0_period0_rule)
    model.t1_period0_con = pyo.Constraint(rule=t1_period0_rule)

    # Subsequent periods: operating <= previous operating + started
    def t0_subsequent_rule(m, p):
        return m.n_operating[0, p] <= m.n_operating[0, p - 1] + m.n_started[0, p]

    def t1_subsequent_rule(m, p):
        return m.n_operating[1, p] <= m.n_operating[1, p - 1] + m.n_started[1, p]

    model.t0_subsequent_con = pyo.Constraint([1, 2], rule=t0_subsequent_rule)
    model.t1_subsequent_con = pyo.Constraint([1, 2], rule=t1_subsequent_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}