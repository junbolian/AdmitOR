# IR: {"sets":{"G":["steel","engines","electronics","plastic"],"C":["engines","plastic"],"A":[["engines","steel"],["plastic","steel"],["steel","engines"],["electronics","engines"],["plastic","engines"],["steel","electronics"],["engines","electronics"],["plastic","electronics"],["engines","plastic"],["steel","plastic"],["electronics","plastic"]]},"params":{"price":["price_steel","price_engines","price_electronics","price_plastic"],"requirements":["steel_req_engines","steel_req_plastic","engines_req_steel","engines_req_electronics","engines_req_plastic","electronics_req_steel","electronics_req_engines","electronics_req_plastic","plastic_req_engines","plastic_req_steel","plastic_req_electronics"],"other_import_cost":["steel_import_cost","engines_import_cost","electronics_import_cost","plastic_import_cost"],"labor":["steel_labor","engines_labor","electronics_labor","plastic_labor"],"capacity":["cap_engines","cap_plastic"],"labor_available":"labor_available"},"variables":{"production[g]":"continuous nonnegative","exports[g]":"continuous nonnegative","imports[g]":"continuous nonnegative"},"constraints":["For each g in G: production[g] + imports[g] = exports[g] + sum(requirement[g,j] * production[j] for (g,j) in A).","sum(labor[g] * production[g] for g in G) <= labor_available; all labor coefficients are supplied in person-months.","For each g in C: production[g] <= capacity[g]."],"objective":"Maximize GDP = sum(price[g] * (exports[g] - imports[g]) - other_import_cost[g] * production[g] for g in G).","assumptions":["The four commodities may be imported or exported at the supplied world prices.","All production remaining after intermediate use is exported; other imported goods are additional production costs."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.goods = pyo.Set(
        initialize=["steel", "engines", "electronics", "plastic"],
        ordered=True,
    )
    model.capacity_goods = pyo.Set(
        initialize=["engines", "plastic"],
        within=model.goods,
    )

    # Each pair is (input commodity, producing industry).
    requirement_data = {
        ("engines", "steel"): params["steel_req_engines"],
        ("plastic", "steel"): params["steel_req_plastic"],
        ("steel", "engines"): params["engines_req_steel"],
        ("electronics", "engines"): params["engines_req_electronics"],
        ("plastic", "engines"): params["engines_req_plastic"],
        ("steel", "electronics"): params["electronics_req_steel"],
        ("engines", "electronics"): params["electronics_req_engines"],
        ("plastic", "electronics"): params["electronics_req_plastic"],
        ("engines", "plastic"): params["plastic_req_engines"],
        ("steel", "plastic"): params["plastic_req_steel"],
        ("electronics", "plastic"): params["plastic_req_electronics"],
    }

    model.input_arcs = pyo.Set(
        dimen=2,
        initialize=list(requirement_data),
        within=model.goods * model.goods,
    )
    model.requirement = pyo.Param(
        model.input_arcs,
        initialize=requirement_data,
        within=pyo.NonNegativeReals,
    )

    model.price = pyo.Param(
        model.goods,
        initialize={
            "steel": params["price_steel"],
            "engines": params["price_engines"],
            "electronics": params["price_electronics"],
            "plastic": params["price_plastic"],
        },
        within=pyo.NonNegativeReals,
    )
    model.other_import_cost = pyo.Param(
        model.goods,
        initialize={
            "steel": params["steel_import_cost"],
            "engines": params["engines_import_cost"],
            "electronics": params["electronics_import_cost"],
            "plastic": params["plastic_import_cost"],
        },
        within=pyo.NonNegativeReals,
    )
    model.labor = pyo.Param(
        model.goods,
        initialize={
            "steel": params["steel_labor"],
            "engines": params["engines_labor"],
            "electronics": params["electronics_labor"],
            "plastic": params["plastic_labor"],
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.capacity_goods,
        initialize={
            "engines": params["cap_engines"],
            "plastic": params["cap_plastic"],
        },
        within=pyo.NonNegativeReals,
    )
    model.labor_available = pyo.Param(
        initialize=params["labor_available"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(model.goods, domain=pyo.NonNegativeReals)
    model.exports = pyo.Var(model.goods, domain=pyo.NonNegativeReals)
    model.imports = pyo.Var(model.goods, domain=pyo.NonNegativeReals)

    def commodity_balance_rule(instance, good):
        intermediate_use = sum(
            instance.requirement[input_good, industry]
            * instance.production[industry]
            for input_good, industry in instance.input_arcs
            if input_good == good
        )
        return (
            instance.production[good] + instance.imports[good]
            == instance.exports[good] + intermediate_use
        )

    model.commodity_balance = pyo.Constraint(
        model.goods,
        rule=commodity_balance_rule,
    )
    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor[good] * model.production[good]
            for good in model.goods
        )
        <= model.labor_available
    )
    model.production_capacity = pyo.Constraint(
        model.capacity_goods,
        rule=lambda instance, good: (
            instance.production[good] <= instance.capacity[good]
        ),
    )

    model.gdp = pyo.Objective(
        expr=sum(
            model.price[good] * (model.exports[good] - model.imports[good])
            - model.other_import_cost[good] * model.production[good]
            for good in model.goods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.gdp))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}