import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = range(5)
    G = range(3)

    base_cost = params["base_cost"]
    marginal_cost = params["marginal_cost"]
    startup_cost = params["startup_cost"]
    demand = params["demand"]
    min_output = params["min_output"]
    max_output = params["max_output"]
    max_generators = params["max_generators"]
    reserve_requirement = params["reserve_requirement"]
    initial_startup_bound = params["initial_startup_bound"]

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=list(T))
    model.G = pyo.Set(initialize=list(G))

    model.gen = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)
    model.startup = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)
    model.output = pyo.Var(model.G, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            base_cost[g] * m.gen[g, t]
            + marginal_cost[g] * m.output[g, t]
            + startup_cost[g] * m.startup[g, t]
            for g in m.G
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, t):
        return sum(m.output[g, t] for g in m.G) >= demand[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    def output_min_rule(m, g, t):
        return m.output[g, t] >= min_output[g] * m.gen[g, t]

    model.output_min_con = pyo.Constraint(model.G, model.T, rule=output_min_rule)

    def output_max_rule(m, g, t):
        return m.output[g, t] <= max_output[g] * m.gen[g, t]

    model.output_max_con = pyo.Constraint(model.G, model.T, rule=output_max_rule)

    def cardinality_rule(m, g, t):
        return m.gen[g, t] <= max_generators[g]

    model.cardinality_con = pyo.Constraint(model.G, model.T, rule=cardinality_rule)

    def reserve_rule(m, t):
        return sum(max_output[g] * m.gen[g, t] for g in m.G) >= reserve_requirement[t]

    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    def startup_initial_rule(m, g):
        return m.gen[g, 0] <= m.startup[g, 0] + initial_startup_bound[g]

    model.startup_initial_con = pyo.Constraint(model.G, rule=startup_initial_rule)

    def startup_recursive_rule(m, g, t):
        if t >= 1:
            return m.gen[g, t] <= m.gen[g, t - 1] + m.startup[g, t]
        return pyo.Constraint.Skip

    model.startup_recursive_con = pyo.Constraint(model.G, model.T, rule=startup_recursive_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}