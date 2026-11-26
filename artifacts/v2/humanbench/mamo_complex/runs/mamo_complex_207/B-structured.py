# IR: {"sets":{"R":[1,2,3,4],"P":["regular","premium"]},"params":{"octane":["octane_raw_1","octane_raw_2","octane_raw_3","octane_raw_4"],"availability":["availability_raw_1","availability_raw_2","availability_raw_3","availability_raw_4"],"cost":["cost_raw_1","cost_raw_2","cost_raw_3","cost_raw_4"],"octane_min":["octane_min_regular","octane_min_premium"],"price":["price_regular","price_premium"],"demand_max":["demand_max_regular","demand_max_premium"]},"variables":{"blend[r,p]":"continuous nonnegative barrels"},"constraints":["For each r: sum_p blend[r,p] <= availability[r]","For each p: sum_r blend[r,p] <= demand_max[p]","For each p: sum_r (octane[r]-octane_min[p])*blend[r,p] >= 0"],"objective":"maximize sum_{r,p} (price[p]-cost[r])*blend[r,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.raw_types = pyo.Set(initialize=[1, 2, 3, 4], ordered=True)
    model.products = pyo.Set(
        initialize=["regular", "premium"], ordered=True
    )

    model.raw_octane = pyo.Param(
        model.raw_types,
        initialize={
            1: params["octane_raw_1"],
            2: params["octane_raw_2"],
            3: params["octane_raw_3"],
            4: params["octane_raw_4"],
        },
        within=pyo.Reals,
    )
    model.raw_availability = pyo.Param(
        model.raw_types,
        initialize={
            1: params["availability_raw_1"],
            2: params["availability_raw_2"],
            3: params["availability_raw_3"],
            4: params["availability_raw_4"],
        },
        within=pyo.NonNegativeReals,
    )
    model.raw_cost = pyo.Param(
        model.raw_types,
        initialize={
            1: params["cost_raw_1"],
            2: params["cost_raw_2"],
            3: params["cost_raw_3"],
            4: params["cost_raw_4"],
        },
        within=pyo.Reals,
    )
    model.minimum_octane = pyo.Param(
        model.products,
        initialize={
            "regular": params["octane_min_regular"],
            "premium": params["octane_min_premium"],
        },
        within=pyo.Reals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize={
            "regular": params["price_regular"],
            "premium": params["price_premium"],
        },
        within=pyo.Reals,
    )
    model.maximum_demand = pyo.Param(
        model.products,
        initialize={
            "regular": params["demand_max_regular"],
            "premium": params["demand_max_premium"],
        },
        within=pyo.NonNegativeReals,
    )

    model.blend = pyo.Var(
        model.raw_types,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(instance, raw):
        return (
            sum(instance.blend[raw, product] for product in instance.products)
            <= instance.raw_availability[raw]
        )

    model.availability_limits = pyo.Constraint(
        model.raw_types, rule=availability_rule
    )

    def demand_rule(instance, product):
        return (
            sum(instance.blend[raw, product] for raw in instance.raw_types)
            <= instance.maximum_demand[product]
        )

    model.demand_limits = pyo.Constraint(
        model.products, rule=demand_rule
    )

    def quality_rule(instance, product):
        return (
            sum(
                (
                    instance.raw_octane[raw]
                    - instance.minimum_octane[product]
                )
                * instance.blend[raw, product]
                for raw in instance.raw_types
            )
            >= 0
        )

    model.octane_requirements = pyo.Constraint(
        model.products, rule=quality_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (model.selling_price[product] - model.raw_cost[raw])
            * model.blend[raw, product]
            for raw in model.raw_types
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}