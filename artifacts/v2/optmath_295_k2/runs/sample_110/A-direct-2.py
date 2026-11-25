import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    power_cost_type0 = params["power_cost_type0"]
    power_cost_type1 = params["power_cost_type1"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_active_per_type = params["max_active_per_type"]
    max_startups_first_type0 = params["max_startups_first_type0"]
    max_startups_first_type1 = params["max_startups_first_type1"]

    # Structural constants
    periods = range(5)
    types = range(2)

    # Create model
    model = pyo.ConcreteModel()

    # Decision variables
    # num_active[t, k] = number of active generators of type k in period t
    model.num_active = pyo.Var(periods, types, domain=pyo.NonNegativeIntegers)

    # output[t, k] = total power output from type k generators in period t
    model.output = pyo.Var(periods, types, domain=pyo.NonNegativeReals)

    # num_startup[t, k] = number of startups of type k in period t
    model.num_startup = pyo.Var(periods, types, domain=pyo.NonNegativeIntegers)

    # Objective function
    def objective_rule(m):
        base_cost = sum(base_cost_type0 * m.num_active[t, 0] +
                        base_cost_type1 * m.num_active[t, 1] for t in periods)
        power_cost = sum(power_cost_type0 * m.output[t, 0] +
                         power_cost_type1 * m.output[t, 1] for t in periods)
        startup_cost = sum(startup_cost_type0 * m.num_startup[t, 0] +
                           startup_cost_type1 * m.num_startup[t, 1] for t in periods)
        return base_cost + power_cost + startup_cost

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Constraints

    # 1. Demand satisfaction
    def demand_rule(m, t):
        return m.output[t, 0] + m.output[t, 1] >= demand[t]
    model.demand_constraint = pyo.Constraint(periods, rule=demand_rule)

    # 2. Output bounds for Type 0
    def output_type0_lower(m, t):
        return m.output[t, 0] >= min_output_type0 * m.num_active[t, 0]
    model.output_type0_lower = pyo.Constraint(periods, rule=output_type0_lower)

    def output_type0_upper(m, t):
        return m.output[t, 0] <= max_output_type0 * m.num_active[t, 0]
    model.output_type0_upper = pyo.Constraint(periods, rule=output_type0_upper)

    # 3. Output bounds for Type 1
    def output_type1_lower(m, t):
        return m.output[t, 1] >= min_output_type1 * m.num_active[t, 1]
    model.output_type1_lower = pyo.Constraint(periods, rule=output_type1_lower)

    def output_type1_upper(m, t):
        return m.output[t, 1] <= max_output_type1 * m.num_active[t, 1]
    model.output_type1_upper = pyo.Constraint(periods, rule=output_type1_upper)

    # 4. Reserve margin constraint
    def reserve_rule(m, t):
        total_capacity = max_output_type0 * m.num_active[t, 0] + max_output_type1 * m.num_active[t, 1]
        return total_capacity >= (1 + reserve_margin) * demand[t]
    model.reserve_constraint = pyo.Constraint(periods, rule=reserve_rule)

    # 5. Maximum active generators per type
    def max_active_type0(m, t):
        return m.num_active[t, 0] <= max_active_per_type
    model.max_active_type0 = pyo.Constraint(periods, rule=max_active_type0)

    def max_active_type1(m, t):
        return m.num_active[t, 1] <= max_active_per_type
    model.max_active_type1 = pyo.Constraint(periods, rule=max_active_type1)

    # 6. Active generator transition constraints
    # For period 0
    def initial_type0(m):
        return m.num_active[0, 0] <= m.num_startup[0, 0]
    model.initial_type0 = pyo.Constraint(rule=initial_type0)

    def initial_type1(m):
        return m.num_active[0, 1] <= m.num_startup[0, 1]
    model.initial_type1 = pyo.Constraint(rule=initial_type1)

    # For subsequent periods
    def transition_type0(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.num_active[t, 0] <= m.num_active[t - 1, 0] + m.num_startup[t, 0]
    model.transition_type0 = pyo.Constraint(periods, rule=transition_type0)

    def transition_type1(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.num_active[t, 1] <= m.num_active[t - 1, 1] + m.num_startup[t, 1]
    model.transition_type1 = pyo.Constraint(periods, rule=transition_type1)

    # 7. Startup constraints
    # First period startup limits
    def startup_limit_first_type0(m):
        return m.num_startup[0, 0] <= max_startups_first_type0
    model.startup_limit_first_type0 = pyo.Constraint(rule=startup_limit_first_type0)

    def startup_limit_first_type1(m):
        return m.num_startup[0, 1] <= max_startups_first_type1
    model.startup_limit_first_type1 = pyo.Constraint(rule=startup_limit_first_type1)

    # Subsequent period startup limits (cannot exceed increase in active)
    def startup_limit_type0(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.num_startup[t, 0] >= m.num_active[t, 0] - m.num_active[t - 1, 0]
    model.startup_limit_type0 = pyo.Constraint(periods, rule=startup_limit_type0)

    def startup_limit_type1(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.num_startup[t, 1] >= m.num_active[t, 1] - m.num_active[t - 1, 1]
    model.startup_limit_type1 = pyo.Constraint(periods, rule=startup_limit_type1)

    # Solve the problem
    Highs().solve(model)

    # Extract objective value
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}