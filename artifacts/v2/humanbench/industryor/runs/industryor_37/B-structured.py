# IR: {"sets":{"I":"1..params[num_factories] (3 factories)","J":"1..params[num_customers] (4 customers)","R":[1,2,3]},"params":{"supply":"factory capacities","demand":"positive customer demands","unit_cost":"transportation costs","full_satisfaction_target_customer4":"customer 4 shipment target","balance_satisfaction_target_customers1and3":"target signed satisfaction difference s[1]-s[3]; zero means equal satisfaction","remaining_customers_min_satisfaction_rate":"minimum satisfaction target for R","factory3_to_customer1_min":"route (3,1) shipment target","factory2_to_customer4_penalty_weight":"nonnegative route (2,4) penalty weight","num_factories":"frozen factory count","num_customers":"frozen customer count"},"variables":{"x[i,j]":"nonnegative continuous shipments","short4":"nonnegative continuous customer 4 shortfall","rate_short[j]":"nonnegative continuous satisfaction shortfall, j in R","route_short":"nonnegative continuous route (3,1) shortfall","balance_under":"nonnegative continuous balance deviation","balance_over":"nonnegative continuous balance deviation"},"expressions":{"s[j]":"sum_i x[i,j]/demand[j]"},"constraints":["sum_j x[i,j] <= supply[i], each i","sum_i x[i,j] <= demand[j], each j","sum_i x[i,4] + short4 >= full_satisfaction_target_customer4","s[j] + rate_short[j] >= remaining_customers_min_satisfaction_rate, each j in R","x[3,1] + route_short >= factory3_to_customer1_min","s[1]-s[3]+balance_under-balance_over = balance_satisfaction_target_customers1and3","after each priority except the last, its expression <= its attained optimum"],"objective":{"sense":"lexicographic minimization","priorities":["short4","sum_j_in_R rate_short[j]","route_short","factory2_to_customer4_penalty_weight*x[2,4]","balance_under+balance_over","sum_i_j unit_cost[i,j]*x[i,j]"]}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six priorities lexicographically.

    Array inputs use ordinary zero-based Python indexing. The balance target
    is the signed satisfaction difference between customers 1 and 3;
    a target of zero requests equal satisfaction.
    """
    num_factories = params["num_factories"]
    num_customers = params["num_customers"]

    if num_factories != 3 or num_customers != 4:
        raise ValueError("This problem requires 3 factories and 4 customers.")

    model = pyo.ConcreteModel()
    model.factories = pyo.RangeSet(1, num_factories)
    model.customers = pyo.RangeSet(1, num_customers)
    model.remaining_customers = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.capacity = pyo.Param(
        model.factories,
        initialize={
            factory: params["supply"][factory - 1]
            for factory in model.factories
        },
        within=pyo.NonNegativeReals,
    )
    model.order_quantity = pyo.Param(
        model.customers,
        initialize={
            customer: params["demand"][customer - 1]
            for customer in model.customers
        },
        within=pyo.PositiveReals,
    )
    model.transport_cost = pyo.Param(
        model.factories,
        model.customers,
        initialize={
            (factory, customer): params["unit_cost"][factory - 1][customer - 1]
            for factory in model.factories
            for customer in model.customers
        },
        within=pyo.Reals,
    )
    model.customer4_target = pyo.Param(
        initialize=params["full_satisfaction_target_customer4"],
        within=pyo.NonNegativeReals,
    )
    model.balance_target = pyo.Param(
        initialize=params["balance_satisfaction_target_customers1and3"],
        within=pyo.Reals,
    )
    model.minimum_rate = pyo.Param(
        initialize=params["remaining_customers_min_satisfaction_rate"],
        within=pyo.NonNegativeReals,
    )
    model.route31_target = pyo.Param(
        initialize=params["factory3_to_customer1_min"],
        within=pyo.NonNegativeReals,
    )
    model.route24_weight = pyo.Param(
        initialize=params["factory2_to_customer4_penalty_weight"],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.factories, model.customers, domain=pyo.NonNegativeReals
    )
    model.short4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.rate_short = pyo.Var(
        model.remaining_customers, domain=pyo.NonNegativeReals
    )
    model.route_short = pyo.Var(domain=pyo.NonNegativeReals)
    model.balance_under = pyo.Var(domain=pyo.NonNegativeReals)
    model.balance_over = pyo.Var(domain=pyo.NonNegativeReals)

    model.satisfaction = pyo.Expression(
        model.customers,
        rule=lambda mod, customer: (
            sum(mod.x[factory, customer] for factory in mod.factories)
            / mod.order_quantity[customer]
        ),
    )

    model.capacity_limits = pyo.Constraint(
        model.factories,
        rule=lambda mod, factory: (
            sum(mod.x[factory, customer] for customer in mod.customers)
            <= mod.capacity[factory]
        ),
    )
    model.order_limits = pyo.Constraint(
        model.customers,
        rule=lambda mod, customer: (
            sum(mod.x[factory, customer] for factory in mod.factories)
            <= mod.order_quantity[customer]
        ),
    )
    model.customer4_goal = pyo.Constraint(
        expr=(
            sum(model.x[factory, 4] for factory in model.factories)
            + model.short4
            >= model.customer4_target
        )
    )
    model.minimum_satisfaction_goals = pyo.Constraint(
        model.remaining_customers,
        rule=lambda mod, customer: (
            mod.satisfaction[customer] + mod.rate_short[customer]
            >= mod.minimum_rate
        ),
    )
    model.route31_goal = pyo.Constraint(
        expr=model.x[3, 1] + model.route_short >= model.route31_target
    )
    model.balance_goal = pyo.Constraint(
        expr=(
            model.satisfaction[1]
            - model.satisfaction[3]
            + model.balance_under
            - model.balance_over
            == model.balance_target
        )
    )

    model.total_transport_cost = pyo.Expression(
        expr=sum(
            model.transport_cost[factory, customer]
            * model.x[factory, customer]
            for factory in model.factories
            for customer in model.customers
        )
    )

    priorities = [
        model.short4,
        sum(
            model.rate_short[customer]
            for customer in model.remaining_customers
        ),
        model.route_short,
        model.route24_weight * model.x[2, 4],
        model.balance_under + model.balance_over,
        model.total_transport_cost,
    ]

    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priorities[0], sense=pyo.minimize
    )

    for priority_position, priority_expression in enumerate(priorities):
        model.goal_objective.set_value(priority_expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solve_failed"}

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_position < len(priorities) - 1:
            model.priority_locks.add(priority_expression <= obj_val)

    return {"objective": obj_val, "status": "optimal"}