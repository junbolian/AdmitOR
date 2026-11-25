# IR: {"sets":{"G":[0,1],"T":[0,1,2,3,4]},"params":{"fixed_cost[g]":["fixed_cost_type0","fixed_cost_type1"],"var_cost[g]":["var_cost_type0","var_cost_type1"],"start_cost[g]":["start_cost_type0","start_cost_type1"],"demand[t]":"demand","min_output[g]":["min_output_type0","min_output_type1"],"max_output[g]":["max_output_type0","max_output_type1"],"capac_req[t]":"capac_req","max_operational[g]":["max_operational_type0","max_operational_type1"],"max_initial_start[g]":["max_start_period0_type0","max_start_period0_type1"]},"variables":{"operational[g,t]":"NonNegativeIntegers","power[g,t]":"NonNegativeIntegers","started[g,t]":"NonNegativeIntegers"},"constraints":["sum_g power[g,t] >= demand[t] for each t","power[g,t] >= min_output[g]*operational[g,t] for each g,t","power[g,t] <= max_output[g]*operational[g,t] for each g,t","sum_g max_output[g]*operational[g,t] >= capac_req[t] for each t","operational[g,t] <= max_operational[g] for each g,t","started[g,0] <= max_initial_start[g] for each g","operational[g,0] <= started[g,0] for each g","started[g,t] <= operational[g,t-1] for each g,t>0","operational[g,t] <= operational[g,t-1]+started[g,t] for each g,t>0"],"objective":"minimize sum_g,t (fixed_cost[g]*operational[g,t]+var_cost[g]*power[g,t]+start_cost[g]*started[g,t])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = {
        0: params["fixed_cost_type0"],
        1: params["fixed_cost_type1"],
    }
    var_cost = {
        0: params["var_cost_type0"],
        1: params["var_cost_type1"],
    }
    start_cost = {
        0: params["start_cost_type0"],
        1: params["start_cost_type1"],
    }
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    max_operational = {
        0: params["max_operational_type0"],
        1: params["max_operational_type1"],
    }
    max_initial_start = {
        0: params["max_start_period0_type0"],
        1: params["max_start_period0_type1"],
    }
    demand = params["demand"]
    capac_req = params["capac_req"]

    model = pyo.ConcreteModel()
    model.G = pyo.Set(initialize=[0, 1], ordered=True)
    model.T = pyo.Set(initialize=range(5), ordered=True)
    model.later_periods = pyo.Set(initialize=range(1, 5), ordered=True)

    model.operational = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )
    model.power = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )
    model.started = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: sum(mdl.power[g, t] for g in mdl.G) >= demand[t],
    )
    model.minimum_generation = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.power[g, t] >= min_output[g] * mdl.operational[g, t]
        ),
    )
    model.maximum_generation = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.power[g, t] <= max_output[g] * mdl.operational[g, t]
        ),
    )
    model.capacity_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(max_output[g] * mdl.operational[g, t] for g in mdl.G)
            >= capac_req[t]
        ),
    )
    model.operational_limit = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.operational[g, t] <= max_operational[g]
        ),
    )
    model.initial_start_limit = pyo.Constraint(
        model.G,
        rule=lambda mdl, g: mdl.started[g, 0] <= max_initial_start[g],
    )
    model.initial_operational_balance = pyo.Constraint(
        model.G,
        rule=lambda mdl, g: mdl.operational[g, 0] <= mdl.started[g, 0],
    )
    model.subsequent_start_limit = pyo.Constraint(
        model.G,
        model.later_periods,
        rule=lambda mdl, g, t: (
            mdl.started[g, t] <= mdl.operational[g, t - 1]
        ),
    )
    model.subsequent_operational_balance = pyo.Constraint(
        model.G,
        model.later_periods,
        rule=lambda mdl, g, t: (
            mdl.operational[g, t]
            <= mdl.operational[g, t - 1] + mdl.started[g, t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            fixed_cost[g] * model.operational[g, t]
            + var_cost[g] * model.power[g, t]
            + start_cost[g] * model.started[g, t]
            for g in model.G
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}