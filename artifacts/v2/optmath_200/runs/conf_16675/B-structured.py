# IR: {"sets":{"I":[0,1,2],"T":[0,1,2,3,4],"Tplus":[1,2,3,4]},"params":{"production_cost":"params['production_cost']","startup_cost":"params['startup_cost']","startup_scaling_factor":"params['startup_scaling_factor']","machine_capacity":"params['machine_capacity']","holding_cost":"params['holding_cost'][i]","backlog_cost":"params['backlog_cost'][i]","demand_period0":"params['demand_period0'][i]"},"assumptions":["Unspecified demand in periods 1-4 is zero.","Initial inventory, backlog, and production state are zero.","Terminal backlog is permitted."],"variables":{"produce[i,t]":"binary","startup[i,t]":"binary","quantity[i,t]":"nonnegative continuous","inventory[i,t]":"nonnegative continuous","backlog[i,t]":"nonnegative continuous"},"constraints":["For each t: sum_i produce[i,t] <= 1.","For each i,t: quantity[i,t] <= machine_capacity*produce[i,t].","For each t: sum_i (quantity[i,t]+startup_scaling_factor*startup[i,t]) <= machine_capacity.","For each i: startup[i,0] = produce[i,0].","For each i,t>0: startup[i,t] >= produce[i,t]-produce[i,t-1].","For each i,t>0: startup[i,t] <= produce[i,t].","For each i,t>0: startup[i,t] <= 1-produce[i,t-1].","For each i,t: previous_inventory-previous_backlog+quantity[i,t] = demand[i,t]+inventory[i,t]-backlog[i,t], with zero initial inventory/backlog and demand[i,t]=demand_period0[i] if t=0 else zero."],"objective":"Minimize sum_i,t (production_cost*produce[i,t]+startup_cost*startup[i,t]+holding_cost[i]*inventory[i,t]+backlog_cost[i]*backlog[i,t])."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 4)
    model.Tplus = pyo.RangeSet(1, 4)

    model.production_cost = pyo.Param(initialize=params["production_cost"])
    model.startup_cost = pyo.Param(initialize=params["startup_cost"])
    model.startup_scaling_factor = pyo.Param(
        initialize=params["startup_scaling_factor"]
    )
    model.machine_capacity = pyo.Param(initialize=params["machine_capacity"])
    model.holding_cost = pyo.Param(
        model.I,
        initialize={i: params["holding_cost"][i] for i in model.I},
    )
    model.backlog_cost = pyo.Param(
        model.I,
        initialize={i: params["backlog_cost"][i] for i in model.I},
    )
    model.demand_period0 = pyo.Param(
        model.I,
        initialize={i: params["demand_period0"][i] for i in model.I},
    )

    model.produce = pyo.Var(model.I, model.T, domain=pyo.Binary)
    model.startup = pyo.Var(model.I, model.T, domain=pyo.Binary)
    model.quantity = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)

    def single_item_rule(instance, t):
        return sum(instance.produce[i, t] for i in instance.I) <= 1

    model.single_item_limit = pyo.Constraint(model.T, rule=single_item_rule)

    def production_link_rule(instance, i, t):
        return (
            instance.quantity[i, t]
            <= instance.machine_capacity * instance.produce[i, t]
        )

    model.production_link = pyo.Constraint(
        model.I, model.T, rule=production_link_rule
    )

    def capacity_rule(instance, t):
        return (
            sum(
                instance.quantity[i, t]
                + instance.startup_scaling_factor * instance.startup[i, t]
                for i in instance.I
            )
            <= instance.machine_capacity
        )

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    def initial_startup_rule(instance, i):
        return instance.startup[i, 0] == instance.produce[i, 0]

    model.initial_startup = pyo.Constraint(model.I, rule=initial_startup_rule)

    def startup_lower_rule(instance, i, t):
        return (
            instance.startup[i, t]
            >= instance.produce[i, t] - instance.produce[i, t - 1]
        )

    model.startup_lower = pyo.Constraint(
        model.I, model.Tplus, rule=startup_lower_rule
    )

    def startup_current_rule(instance, i, t):
        return instance.startup[i, t] <= instance.produce[i, t]

    model.startup_current_limit = pyo.Constraint(
        model.I, model.Tplus, rule=startup_current_rule
    )

    def startup_previous_rule(instance, i, t):
        return instance.startup[i, t] <= 1 - instance.produce[i, t - 1]

    model.startup_previous_limit = pyo.Constraint(
        model.I, model.Tplus, rule=startup_previous_rule
    )

    def balance_rule(instance, i, t):
        previous_net_inventory = (
            0
            if t == 0
            else instance.inventory[i, t - 1] - instance.backlog[i, t - 1]
        )
        demand = instance.demand_period0[i] if t == 0 else 0
        return (
            previous_net_inventory + instance.quantity[i, t]
            == demand + instance.inventory[i, t] - instance.backlog[i, t]
        )

    model.demand_balance = pyo.Constraint(model.I, model.T, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost * model.produce[i, t]
            + model.startup_cost * model.startup[i, t]
            + model.holding_cost[i] * model.inventory[i, t]
            + model.backlog_cost[i] * model.backlog[i, t]
            for i in model.I
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    # Determine success solely by whether the objective can be evaluated.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}