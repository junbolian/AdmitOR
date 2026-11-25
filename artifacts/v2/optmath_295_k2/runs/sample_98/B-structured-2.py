# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"demand":"nonnegative[P,T]","production_cost":"real[P,T]","setup_cost":"real[P,T]","holding_cost":"real[P]","capacity":"nonnegative[T]","capacity_consumption":"positive[P]"},"variables":{"production":"nonnegative continuous[P,T]","inventory":"nonnegative continuous[P,T]","setup":"binary[P,T]"},"constraints":["balance[p,t]: sum(production[p,k], k<=t) = sum(demand[p,k], k<=t) + inventory[p,t]","capacity[t]: sum(capacity_consumption[p]*production[p,t], p in P) <= capacity[t]","setup_link[p,t]: production[p,t] <= sum(demand[p,k], k>=t)*setup[p,t]"],"objective":"min sum(production_cost[p,t]*production[p,t] + setup_cost[p,t]*setup[p,t] + holding_cost[p]*inventory[p,t], p in P, t in T)","boundary_convention":"No separate initial inventory variable; cumulative balances account for production and demand within the horizon. No explicit initial or final inventory equality."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.months = pyo.RangeSet(0, 5)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize=lambda _, product, month: demand[product][month],
        within=pyo.NonNegativeReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda _, product, month: production_cost[product][month],
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.products,
        model.months,
        initialize=lambda _, product, month: setup_cost[product][month],
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        model.products,
        initialize=lambda _, product: holding_cost[product],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.months,
        initialize=lambda _, month: capacity[month],
        within=pyo.NonNegativeReals,
    )
    model.capacity_consumption = pyo.Param(
        model.products,
        initialize=lambda _, product: capacity_consumption[product],
        within=pyo.PositiveReals,
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.setup = pyo.Var(
        model.products, model.months, domain=pyo.Binary
    )

    def inventory_balance_rule(instance, product, month):
        return (
            sum(
                instance.production[product, earlier]
                for earlier in instance.months
                if earlier <= month
            )
            == sum(
                instance.demand[product, earlier]
                for earlier in instance.months
                if earlier <= month
            )
            + instance.inventory[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def resource_capacity_rule(instance, month):
        return (
            sum(
                instance.capacity_consumption[product]
                * instance.production[product, month]
                for product in instance.products
            )
            <= instance.capacity[month]
        )

    model.resource_capacity = pyo.Constraint(
        model.months, rule=resource_capacity_rule
    )

    def setup_link_rule(instance, product, month):
        return (
            instance.production[product, month]
            <= sum(
                instance.demand[product, later]
                for later in instance.months
                if later >= month
            )
            * instance.setup[product, month]
        )

    model.setup_link = pyo.Constraint(
        model.products, model.months, rule=setup_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[product, month]
            * model.production[product, month]
            + model.setup_cost[product, month] * model.setup[product, month]
            + model.holding_cost[product] * model.inventory[product, month]
            for product in model.products
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        # Appsi HiGHS raises this when it cannot load a feasible solution.
        if "feasible solution" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}