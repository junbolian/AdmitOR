# IR (JSON):
# {
#   "sets": {"G": [0, 1], "T": [0, 1, 2]},
#   "params": {
#     "base": "base_cost_per_generator_per_period",
#     "power_cost": "power_cost_per_mw",
#     "startup[0]": "startup_cost_type0",
#     "startup[1]": "startup_cost_type1",
#     "demand[t]": "demand_per_period[t]",
#     "capacity_required[t]": "capacity_margin_demand[t]",
#     "minimum[0]": "min_output_type0",
#     "maximum[0]": "max_output_type0",
#     "minimum[1]": "min_output_type1",
#     "maximum[1]": "max_output_type1",
#     "operating_limit": "max_generators_per_type_per_period",
#     "initial[0]": "type0_period0_operating_limit_offset",
#     "initial[1]": "type1_period0_operating_limit_offset"
#   },
#   "variables": {
#     "operating[g,t]": "nonnegative integer",
#     "power[g,t]": "nonnegative continuous; aggregate MW for type g",
#     "started[g,t]": "nonnegative integer"
#   },
#   "constraints": [
#     "operating[g,t] <= operating_limit for all g,t",
#     "power[g,t] >= minimum[g]*operating[g,t] for all g,t",
#     "power[g,t] <= maximum[g]*operating[g,t] for all g,t",
#     "sum_g power[g,t] >= demand[t] for all t",
#     "sum_g maximum[g]*operating[g,t] >= capacity_required[t] for all t",
#     "operating[g,0] <= initial[g] + started[g,0] for all g",
#     "operating[g,t] <= operating[g,t-1] + started[g,t] for all g,t>0"
#   ],
#   "objective": "minimize sum_{g,t}(base*operating[g,t] + power_cost*power[g,t] + startup[g]*started[g,t])"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Period-indexed inputs must support integer keys or indices 0, 1, 2."""
    base = params["base_cost_per_generator_per_period"]
    power_cost = params["power_cost_per_mw"]
    startup = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    demand = params["demand_per_period"]
    capacity_required = params["capacity_margin_demand"]
    minimum = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    maximum = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    operating_limit = params["max_generators_per_type_per_period"]
    initial = {
        0: params["type0_period0_operating_limit_offset"],
        1: params["type1_period0_operating_limit_offset"],
    }

    model = pyo.ConcreteModel()
    model.G = pyo.Set(initialize=[0, 1], ordered=True)
    model.T = pyo.Set(initialize=[0, 1, 2], ordered=True)

    model.operating = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )
    model.power = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeReals
    )
    model.started = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )

    def operating_limit_rule(block, generator_type, period):
        return block.operating[generator_type, period] <= operating_limit

    model.operating_limit_constraint = pyo.Constraint(
        model.G, model.T, rule=operating_limit_rule
    )

    def minimum_power_rule(block, generator_type, period):
        return (
            block.power[generator_type, period]
            >= minimum[generator_type]
            * block.operating[generator_type, period]
        )

    model.minimum_power_constraint = pyo.Constraint(
        model.G, model.T, rule=minimum_power_rule
    )

    def maximum_power_rule(block, generator_type, period):
        return (
            block.power[generator_type, period]
            <= maximum[generator_type]
            * block.operating[generator_type, period]
        )

    model.maximum_power_constraint = pyo.Constraint(
        model.G, model.T, rule=maximum_power_rule
    )

    def demand_rule(block, period):
        return (
            sum(block.power[generator_type, period]
                for generator_type in block.G)
            >= demand[period]
        )

    model.demand_constraint = pyo.Constraint(model.T, rule=demand_rule)

    def capacity_rule(block, period):
        return (
            sum(
                maximum[generator_type]
                * block.operating[generator_type, period]
                for generator_type in block.G
            )
            >= capacity_required[period]
        )

    model.capacity_constraint = pyo.Constraint(model.T, rule=capacity_rule)

    def initial_startup_rule(block, generator_type):
        return (
            block.operating[generator_type, 0]
            <= initial[generator_type] + block.started[generator_type, 0]
        )

    model.initial_startup_constraint = pyo.Constraint(
        model.G, rule=initial_startup_rule
    )

    def subsequent_startup_rule(block, generator_type, period):
        return (
            block.operating[generator_type, period]
            <= block.operating[generator_type, period - 1]
            + block.started[generator_type, period]
        )

    model.subsequent_startup_constraint = pyo.Constraint(
        model.G, [1, 2], rule=subsequent_startup_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            base * model.operating[generator_type, period]
            + power_cost * model.power[generator_type, period]
            + startup[generator_type] * model.started[generator_type, period]
            for generator_type in model.G
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}