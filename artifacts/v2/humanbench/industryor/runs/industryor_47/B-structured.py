# IR: {"sets":{"P":["I","II"],"T":[1,2,3,4,5,6,7,8,9,10,11,12]},"params":{"demand_I":"12 monthly values","demand_II":"12 monthly values","cost_I":"12 monthly values","cost_II":"12 monthly values","production_capacity":"scalar","warehouse_capacity":"scalar","space_I":"scalar","space_II":"scalar","own_storage_cost":"scalar","external_storage_cost":"scalar additional external-space charge"},"variables":{"production[p,t]":"nonnegative continuous units","inventory[p,t]":"nonnegative continuous end-of-month units","own_space[t]":"nonnegative continuous cubic meters","external_space[t]":"nonnegative continuous cubic meters"},"constraints":["production[p,t]+(inventory[p,t-1] if t>1 else 0)=demand[p,t]+inventory[p,t]","sum_p production[p,t]<=production_capacity","own_space[t]+external_space[t]=sum_p space[p]*inventory[p,t]","own_space[t]<=warehouse_capacity"],"objective":"min sum_t(sum_p cost[p,t]*production[p,t]+own_storage_cost*(own_space[t]+external_space[t])+external_storage_cost*external_space[t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using monthly sequences ordered January through December.

    Initial inventory is zero. Storage charges apply to end-of-month
    inventory. External space incurs the base storage charge plus the
    additional external storage charge.
    """
    demand_by_product = {
        "I": params["demand_I"],
        "II": params["demand_II"],
    }
    cost_by_product = {
        "I": params["cost_I"],
        "II": params["cost_II"],
    }
    space_by_product = {
        "I": params["space_I"],
        "II": params["space_II"],
    }

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["I", "II"], ordered=True)
    model.months = pyo.RangeSet(1, 12)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: (
            demand_by_product[product][month - 1]
        ),
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda mdl, product, month: (
            cost_by_product[product][month - 1]
        ),
        within=pyo.NonNegativeReals,
    )
    model.unit_space = pyo.Param(
        model.products,
        initialize=space_by_product,
        within=pyo.NonNegativeReals,
    )
    model.production_capacity = pyo.Param(
        initialize=params["production_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.warehouse_capacity = pyo.Param(
        initialize=params["warehouse_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.own_storage_cost = pyo.Param(
        initialize=params["own_storage_cost"],
        within=pyo.NonNegativeReals,
    )
    model.external_storage_cost = pyo.Param(
        initialize=params["external_storage_cost"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.own_space = pyo.Var(
        model.months, domain=pyo.NonNegativeReals
    )
    model.external_space = pyo.Var(
        model.months, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(mdl, product, month):
        previous_inventory = (
            0 if month == 1 else mdl.inventory[product, month - 1]
        )
        return (
            mdl.production[product, month] + previous_inventory
            == mdl.demand[product, month] + mdl.inventory[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def production_limit_rule(mdl, month):
        return (
            sum(mdl.production[product, month] for product in mdl.products)
            <= mdl.production_capacity
        )

    model.production_limit = pyo.Constraint(
        model.months, rule=production_limit_rule
    )

    def storage_balance_rule(mdl, month):
        return (
            mdl.own_space[month] + mdl.external_space[month]
            == sum(
                mdl.unit_space[product] * mdl.inventory[product, month]
                for product in mdl.products
            )
        )

    model.storage_balance = pyo.Constraint(
        model.months, rule=storage_balance_rule
    )

    model.own_storage_limit = pyo.Constraint(
        model.months,
        rule=lambda mdl, month: (
            mdl.own_space[month] <= mdl.warehouse_capacity
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            sum(
                model.unit_cost[product, month]
                * model.production[product, month]
                for product in model.products
            )
            + model.own_storage_cost
            * (model.own_space[month] + model.external_space[month])
            + model.external_storage_cost * model.external_space[month]
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}