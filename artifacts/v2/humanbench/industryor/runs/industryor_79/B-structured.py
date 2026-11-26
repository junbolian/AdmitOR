# IR: {"sets":{"C":["steel","engines","electronics","plastics"],"E":[["engines","steel"],["plastics","steel"],["steel","engines"],["electronics","engines"],["plastics","engines"],["steel","electronics"],["engines","electronics"],["plastics","electronics"],["engines","plastics"],["steel","plastics"],["electronics","plastics"]]},"params":{"price":["steel_price","engines_price","electronics_price","plastics_price"],"a_input_output":["a_steel_engines","a_steel_plastics","a_engines_steel","a_engines_electronics","a_engines_plastics","a_electronics_steel","a_electronics_engines","a_electronics_plastics","a_plastics_engines","a_plastics_steel","a_plastics_electronics"],"other_import_cost":["import_cost_steel","import_cost_engines","import_cost_electronics","import_cost_plastics"],"labor_years":{"steel":"labor_steel/12","engines":"labor_engines","electronics":"labor_electronics/12","plastics":"labor_plastics"},"capacity":["engine_capacity","plastics_capacity"],"labor_capacity":"labor_capacity"},"variables":{"production[c]":"nonnegative continuous","exports[c]":"nonnegative continuous","imports[c]":"nonnegative continuous"},"constraints":["For each c: production[c]+imports[c]=exports[c]+sum(a[c,j]*production[j] for (c,j) in E).","production[engines]<=engine_capacity.","production[plastics]<=plastics_capacity.","sum(labor_years[c]*production[c] for c in C)<=labor_capacity."],"objective":"maximize sum(price[c]*(exports[c]-imports[c])-other_import_cost[c]*production[c] for c in C)","assumptions":["Annual steady state; commodity imports and exports are allowed at the given world prices; 12 months equal one year."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize annual net export value, including other imported inputs."""
    commodities = ("steel", "engines", "electronics", "plastics")

    price_data = {
        "steel": params["steel_price"],
        "engines": params["engines_price"],
        "electronics": params["electronics_price"],
        "plastics": params["plastics_price"],
    }

    # Keys are (input commodity, output commodity).
    input_data = {
        ("engines", "steel"): params["a_steel_engines"],
        ("plastics", "steel"): params["a_steel_plastics"],
        ("steel", "engines"): params["a_engines_steel"],
        ("electronics", "engines"): params["a_engines_electronics"],
        ("plastics", "engines"): params["a_engines_plastics"],
        ("steel", "electronics"): params["a_electronics_steel"],
        ("engines", "electronics"): params["a_electronics_engines"],
        ("plastics", "electronics"): params["a_electronics_plastics"],
        ("engines", "plastics"): params["a_plastics_engines"],
        ("steel", "plastics"): params["a_plastics_steel"],
        ("electronics", "plastics"): params["a_plastics_electronics"],
    }

    other_import_cost_data = {
        "steel": params["import_cost_steel"],
        "engines": params["import_cost_engines"],
        "electronics": params["import_cost_electronics"],
        "plastics": params["import_cost_plastics"],
    }

    # Twelve is a unit-conversion constant, not a problem-data value.
    labor_years_data = {
        "steel": params["labor_steel"] / 12,
        "engines": params["labor_engines"],
        "electronics": params["labor_electronics"] / 12,
        "plastics": params["labor_plastics"],
    }

    model = pyo.ConcreteModel()

    model.commodities = pyo.Set(initialize=commodities, ordered=True)
    model.input_edges = pyo.Set(
        dimen=2, initialize=tuple(input_data), ordered=True
    )

    model.world_price = pyo.Param(
        model.commodities,
        initialize=price_data,
        within=pyo.NonNegativeReals,
    )
    model.input_requirement = pyo.Param(
        model.input_edges,
        initialize=input_data,
        within=pyo.NonNegativeReals,
    )
    model.other_import_cost = pyo.Param(
        model.commodities,
        initialize=other_import_cost_data,
        within=pyo.NonNegativeReals,
    )
    model.labor_years = pyo.Param(
        model.commodities,
        initialize=labor_years_data,
        within=pyo.NonNegativeReals,
    )
    model.engine_capacity = pyo.Param(
        initialize=params["engine_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.plastics_capacity = pyo.Param(
        initialize=params["plastics_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.labor_capacity = pyo.Param(
        initialize=params["labor_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )
    model.exports = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )
    model.imports = pyo.Var(
        model.commodities, domain=pyo.NonNegativeReals
    )

    def commodity_balance_rule(block, commodity):
        intermediate_demand = sum(
            block.input_requirement[input_commodity, output_commodity]
            * block.production[output_commodity]
            for input_commodity, output_commodity in block.input_edges
            if input_commodity == commodity
        )
        return (
            block.production[commodity] + block.imports[commodity]
            == block.exports[commodity] + intermediate_demand
        )

    model.commodity_balance = pyo.Constraint(
        model.commodities, rule=commodity_balance_rule
    )
    model.engine_limit = pyo.Constraint(
        expr=model.production["engines"] <= model.engine_capacity
    )
    model.plastics_limit = pyo.Constraint(
        expr=model.production["plastics"] <= model.plastics_capacity
    )
    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor_years[commodity] * model.production[commodity]
            for commodity in model.commodities
        )
        <= model.labor_capacity
    )

    model.gdp = pyo.Objective(
        expr=sum(
            model.world_price[commodity]
            * (model.exports[commodity] - model.imports[commodity])
            - model.other_import_cost[commodity]
            * model.production[commodity]
            for commodity in model.commodities
        ),
        sense=pyo.maximize,
    )

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines the returned success status.
    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.gdp))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}