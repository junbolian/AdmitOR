# {"sets":{"R":["A","B","C"],"T":[1,2,3]},"params":{"raw_cost":{"A":"raw_cost_A","B":"raw_cost_B","C":"raw_cost_C"},"limit":{"A":"limit_A","B":"limit_B","C":"limit_C"},"proc_fee":{"1":"proc_fee_1","2":"proc_fee_2","3":"proc_fee_3"},"price":{"1":"price_1","2":"price_2","3":"price_3"},"A_min_1":"content_A_min_1","B_min_2":"content_B_min_2","C_max":{"1":"content_C_max_1","2":"content_C_max_2","3":"content_C_max_3"}},"variables":{"x[r,t]":"continuous nonnegative; kg of raw material r in candy type t"},"expressions":{"production[t]":"sum(x[r,t] for r in R)"},"constraints":["sum(x[r,t] for t in T) <= limit[r] for each r in R","x[A,1] >= A_min_1 * production[1]","x[B,2] >= B_min_2 * production[2]","x[C,t] <= C_max[t] * production[t] for each t in T"],"objective":{"sense":"maximize","expression":"sum((price[t]-proc_fee[t])*production[t] for t in T) - sum(raw_cost[r]*x[r,t] for r in R for t in T)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_cost = {
        "A": params["raw_cost_A"],
        "B": params["raw_cost_B"],
        "C": params["raw_cost_C"],
    }
    limits = {
        "A": params["limit_A"],
        "B": params["limit_B"],
        "C": params["limit_C"],
    }
    processing_fees = {
        1: params["proc_fee_1"],
        2: params["proc_fee_2"],
        3: params["proc_fee_3"],
    }
    selling_prices = {
        1: params["price_1"],
        2: params["price_2"],
        3: params["price_3"],
    }
    minimum_A_type_1 = params["content_A_min_1"]
    minimum_B_type_2 = params["content_B_min_2"]
    maximum_C = {
        1: params["content_C_max_1"],
        2: params["content_C_max_2"],
        3: params["content_C_max_3"],
    }

    model = pyo.ConcreteModel()
    model.R = pyo.Set(initialize=["A", "B", "C"], ordered=True)
    model.T = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.raw_cost = pyo.Param(model.R, initialize=raw_cost)
    model.raw_limit = pyo.Param(model.R, initialize=limits)
    model.processing_fee = pyo.Param(model.T, initialize=processing_fees)
    model.selling_price = pyo.Param(model.T, initialize=selling_prices)
    model.minimum_A_type_1 = pyo.Param(initialize=minimum_A_type_1)
    model.minimum_B_type_2 = pyo.Param(initialize=minimum_B_type_2)
    model.maximum_C = pyo.Param(model.T, initialize=maximum_C)

    model.x = pyo.Var(model.R, model.T, domain=pyo.NonNegativeReals)

    def production_rule(block, candy_type):
        return sum(block.x[raw, candy_type] for raw in block.R)

    model.production = pyo.Expression(model.T, rule=production_rule)

    def availability_rule(block, raw):
        return (
            sum(block.x[raw, candy_type] for candy_type in block.T)
            <= block.raw_limit[raw]
        )

    model.raw_availability = pyo.Constraint(
        model.R, rule=availability_rule
    )
    model.minimum_A_constraint = pyo.Constraint(
        expr=model.x["A", 1]
        >= model.minimum_A_type_1 * model.production[1]
    )
    model.minimum_B_constraint = pyo.Constraint(
        expr=model.x["B", 2]
        >= model.minimum_B_type_2 * model.production[2]
    )

    def maximum_C_rule(block, candy_type):
        return (
            block.x["C", candy_type]
            <= block.maximum_C[candy_type] * block.production[candy_type]
        )

    model.maximum_C_constraints = pyo.Constraint(
        model.T, rule=maximum_C_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (
                model.selling_price[candy_type]
                - model.processing_fee[candy_type]
            )
            * model.production[candy_type]
            for candy_type in model.T
        )
        - sum(
            model.raw_cost[raw] * model.x[raw, candy_type]
            for raw in model.R
            for candy_type in model.T
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}