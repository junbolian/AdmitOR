# IR: {"sets":{"K":[0,1],"T":[0,1,2,3,4]},"params":["fixed_cost_type0","fixed_cost_type1","var_cost_type0","var_cost_type1","start_cost_type0","start_cost_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","capac_req","max_operational_type0","max_operational_type1","max_start_period0_type0","max_start_period0_type1"],"variables":{"operational[k,t]":"nonnegative integer","power[k,t]":"nonnegative integer","started[k,t]":"nonnegative integer"},"constraints":["sum_k power[k,t] >= demand[t] for all t","min_output[k]*operational[k,t] <= power[k,t] for all k,t","power[k,t] <= max_output[k]*operational[k,t] for all k,t","sum_k max_output[k]*operational[k,t] >= capac_req[t] for all t","operational[k,t] <= max_operational[k] for all k,t","started[k,0] <= max_start_period0[k] for all k","operational[k,0] <= started[k,0] for all k","started[k,t] <= operational[k,t-1] for all k,t>0","operational[k,t] <= operational[k,t-1]+started[k,t] for all k,t>0"],"objective":"minimize sum_{k,t}(fixed_cost[k]*operational[k,t]+var_cost[k]*power[k,t]+start_cost[k]*started[k,t])"}
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
    demand = params["demand"]
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    capac_req = params["capac_req"]
    max_operational = {
        0: params["max_operational_type0"],
        1: params["max_operational_type1"],
    }
    max_start_period0 = {
        0: params["max_start_period0_type0"],
        1: params["max_start_period0_type1"],
    }

    model = pyo.ConcreteModel()
    model.K = pyo.Set(initialize=[0, 1])
    model.T = pyo.RangeSet(0, 4)
    model.later_periods = pyo.RangeSet(1, 4)

    model.operational = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)
    model.power = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)
    model.started = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: sum(mdl.power[k, t] for k in mdl.K) >= demand[t],
    )
    model.minimum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, k, t:
        mdl.power[k, t] >= min_output[k] * mdl.operational[k, t],
    )
    model.maximum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, k, t:
        mdl.power[k, t] <= max_output[k] * mdl.operational[k, t],
    )
    model.capacity_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t:
        sum(max_output[k] * mdl.operational[k, t] for k in mdl.K)
        >= capac_req[t],
    )
    model.operational_limit = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, k, t: mdl.operational[k, t] <= max_operational[k],
    )
    model.initial_start_limit = pyo.Constraint(
        model.K,
        rule=lambda mdl, k: mdl.started[k, 0] <= max_start_period0[k],
    )
    model.initial_operation = pyo.Constraint(
        model.K,
        rule=lambda mdl, k: mdl.operational[k, 0] <= mdl.started[k, 0],
    )
    model.subsequent_start_limit = pyo.Constraint(
        model.K,
        model.later_periods,
        rule=lambda mdl, k, t: mdl.started[k, t] <= mdl.operational[k, t - 1],
    )
    model.operation_transition = pyo.Constraint(
        model.K,
        model.later_periods,
        rule=lambda mdl, k, t:
        mdl.operational[k, t]
        <= mdl.operational[k, t - 1] + mdl.started[k, t],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            fixed_cost[k] * model.operational[k, t]
            + var_cost[k] * model.power[k, t]
            + start_cost[k] * model.started[k, t]
            for k in model.K
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