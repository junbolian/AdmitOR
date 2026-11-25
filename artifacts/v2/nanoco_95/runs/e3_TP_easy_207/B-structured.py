# IR: {"sets":{"H":[0,1,2],"A":[3,4,5,6],"E":"H x A"},"params":{"supply":"params['supply'][h]","demand":"params['demand'][a-3] (positive)","capacity":"params['capacity_0'], params['capacity_1'], params['capacity_2'], indexed by a-3","cost":"params['cost_0'], params['cost_1'], params['cost_2'], indexed by a-3"},"variables":{"flow[h,a]":"continuous nonnegative"},"constraints":["sum(flow[h,a] for a in A) = supply[h] for h in H","sum(flow[h,a] for h in H) = demand[a] for a in A","flow[h,a] <= capacity[h,a] for (h,a) in E"],"objective":"minimize sum(cost[h,a]*flow[h,a] for (h,a) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_rows = (
        params["capacity_0"],
        params["capacity_1"],
        params["capacity_2"],
    )
    cost_rows = (
        params["cost_0"],
        params["cost_1"],
        params["cost_2"],
    )

    model = pyo.ConcreteModel()
    model.H = pyo.Set(initialize=range(3), ordered=True)
    model.A = pyo.Set(initialize=range(3, 7), ordered=True)
    model.E = pyo.Set(
        dimen=2,
        initialize=((h, a) for h in range(3) for a in range(3, 7)),
    )

    model.supply = pyo.Param(
        model.H,
        initialize={h: supply[h] for h in range(3)},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.A,
        initialize={a: demand[a - 3] for a in range(3, 7)},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.E,
        initialize={
            (h, a): capacity_rows[h][a - 3]
            for h in range(3)
            for a in range(3, 7)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.E,
        initialize={
            (h, a): cost_rows[h][a - 3]
            for h in range(3)
            for a in range(3, 7)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.E, domain=pyo.NonNegativeReals)

    def supply_balance_rule(problem, h):
        return (
            sum(problem.flow[h, a] for a in problem.A)
            == problem.supply[h]
        )

    def demand_balance_rule(problem, a):
        return (
            sum(problem.flow[h, a] for h in problem.H)
            == problem.demand[a]
        )

    def corridor_capacity_rule(problem, h, a):
        return problem.flow[h, a] <= problem.capacity[h, a]

    model.supply_balance = pyo.Constraint(
        model.H, rule=supply_balance_rule
    )
    model.demand_balance = pyo.Constraint(
        model.A, rule=demand_balance_rule
    )
    model.corridor_capacity = pyo.Constraint(
        model.E, rule=corridor_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[h, a] * model.flow[h, a]
            for h, a in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}