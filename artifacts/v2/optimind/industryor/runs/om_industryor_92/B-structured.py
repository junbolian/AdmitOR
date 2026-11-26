# IR: {"sets":{"C":["A","B"],"G":["I","II"],"T":[1,2,3],"K":[2,3]},"params":["price_gas_I","price_gas_II","min_prop_A_I","min_prop_A_II","inventory_A","inventory_B","max_purchase_A","price_tier1","tier1_limit","price_tier2","tier2_limit","price_tier3"],"interpretation":{"tier2_limit":"cumulative purchase threshold ending tranche 2","initial_inventory_cost":"sunk"},"variables":{"x[c,g]":"nonnegative continuous tonnes of crude c allocated to gasoline g","q[t]":"nonnegative continuous tonnes purchased in tranche t","z[k]":"binary indicator enabling tranche k"},"constraints":["sum_g x[A,g] <= inventory_A + sum_t q[t]","sum_g x[B,g] <= inventory_B","x[A,g] >= min_prop_A_g*(x[A,g]+x[B,g]) for g in G","sum_t q[t] <= max_purchase_A","q[1] <= tier1_limit","q[1] >= tier1_limit*z[2]","q[2] <= (tier2_limit-tier1_limit)*z[2]","q[2] >= (tier2_limit-tier1_limit)*z[3]","q[3] <= max_purchase_A*z[3]","z[3] <= z[2]"],"objective":"maximize sum_g price_gas_g*(x[A,g]+x[B,g]) - price_tier1*q[1] - price_tier2*q[2] - price_tier3*q[3]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    selling_price = {
        "I": params["price_gas_I"],
        "II": params["price_gas_II"],
    }
    minimum_a = {
        "I": params["min_prop_A_I"],
        "II": params["min_prop_A_II"],
    }
    inventory_a = params["inventory_A"]
    inventory_b = params["inventory_B"]
    purchase_limit = params["max_purchase_A"]
    purchase_price = {
        1: params["price_tier1"],
        2: params["price_tier2"],
        3: params["price_tier3"],
    }
    first_threshold = params["tier1_limit"]
    second_threshold = params["tier2_limit"]
    second_capacity = second_threshold - first_threshold

    model = pyo.ConcreteModel()
    model.crudes = pyo.Set(initialize=["A", "B"])
    model.products = pyo.Set(initialize=["I", "II"])
    model.tranches = pyo.Set(initialize=[1, 2, 3])
    model.activation_tranches = pyo.Set(initialize=[2, 3])

    model.x = pyo.Var(
        model.crudes, model.products, domain=pyo.NonNegativeReals
    )
    model.q = pyo.Var(model.tranches, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(model.activation_tranches, domain=pyo.Binary)

    model.crude_a_balance = pyo.Constraint(
        expr=sum(model.x["A", grade] for grade in model.products)
        <= inventory_a + sum(model.q[tier] for tier in model.tranches)
    )
    model.crude_b_balance = pyo.Constraint(
        expr=sum(model.x["B", grade] for grade in model.products)
        <= inventory_b
    )

    def blend_requirement_rule(block, grade):
        return block.x["A", grade] >= minimum_a[grade] * (
            block.x["A", grade] + block.x["B", grade]
        )

    model.blend_requirement = pyo.Constraint(
        model.products, rule=blend_requirement_rule
    )

    model.total_purchase_limit = pyo.Constraint(
        expr=sum(model.q[tier] for tier in model.tranches)
        <= purchase_limit
    )
    model.first_tranche_limit = pyo.Constraint(
        expr=model.q[1] <= first_threshold
    )
    model.fill_first_before_second = pyo.Constraint(
        expr=model.q[1] >= first_threshold * model.z[2]
    )
    model.second_tranche_limit = pyo.Constraint(
        expr=model.q[2] <= second_capacity * model.z[2]
    )
    model.fill_second_before_third = pyo.Constraint(
        expr=model.q[2] >= second_capacity * model.z[3]
    )
    model.third_tranche_activation = pyo.Constraint(
        expr=model.q[3] <= purchase_limit * model.z[3]
    )
    model.tranche_activation_order = pyo.Constraint(
        expr=model.z[3] <= model.z[2]
    )

    model.profit = pyo.Objective(
        expr=(
            sum(
                selling_price[grade]
                * (model.x["A", grade] + model.x["B", grade])
                for grade in model.products
            )
            - sum(
                purchase_price[tier] * model.q[tier]
                for tier in model.tranches
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}