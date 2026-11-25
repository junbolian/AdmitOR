# IR: {"sets":{"N":"0..8","C":"1..8","A":"(i,j) in N*N, i!=j","AC":"(i,j) in C*C, i!=j"},"params":{"travel_time":"input matrix","time_window_start":"input node vector","time_window_end":"input node vector","planning_horizon":"input scalar","service_time":"input scalar or node vector","M[i,j]":"max(0,end[i]+service[i]+travel[i,j]-start[j])"},"variables":{"x[A]":"binary","t[N]":"continuous, start[i]<=t[i]<=end[i]; service starts after any waiting","return_time":"continuous, start[0]<=return_time<=end[0]","order[C]":"continuous, 1<=order[i]<=8"},"constraints":["sum(j!=i)x[i,j]=1 for i in N","sum(i!=j)x[i,j]=1 for j in N","order[i]-order[j]+8*x[i,j]<=7 for (i,j) in AC","t[j]>=t[i]+service[i]+travel[i,j]-M[i,j]*(1-x[i,j]) for (i,j) in A with j in C","return_time>=t[i]+service[i]+travel[i,0]-M[i,0]*(1-x[i,0]) for i in C","return_time-t[0]<=planning_horizon"],"objective":"minimize sum((i,j) in A) travel[i,j]*x[i,j]"}
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    travel_input = params["travel_time"]
    start_input = params["time_window_start"]
    end_input = params["time_window_end"]
    horizon_input = params["planning_horizon"]
    service_input = params["service_time"]

    nodes = range(9)
    customers = range(1, 9)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    customer_arcs = [
        (i, j) for i in customers for j in customers if i != j
    ]

    travel = {
        (i, j): float(travel_input[i][j])
        for i, j in arcs
    }
    window_start = {i: float(start_input[i]) for i in nodes}
    window_end = {i: float(end_input[i]) for i in nodes}
    horizon = float(horizon_input)

    if isinstance(service_input, Number):
        service = {i: float(service_input) for i in nodes}
    else:
        service = {i: float(service_input[i]) for i in nodes}

    if any(window_start[i] > window_end[i] for i in nodes):
        return {"objective": None, "status": "infeasible"}

    big_m = {
        (i, j): max(
            0.0,
            window_end[i] + service[i] + travel[i, j] - window_start[j],
        )
        for i, j in arcs
    }

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.customer_arcs = pyo.Set(dimen=2, initialize=customer_arcs)

    model.travel = pyo.Param(model.arcs, initialize=travel)
    model.window_start = pyo.Param(model.nodes, initialize=window_start)
    model.window_end = pyo.Param(model.nodes, initialize=window_end)
    model.service = pyo.Param(model.nodes, initialize=service)
    model.horizon = pyo.Param(initialize=horizon)
    model.big_m = pyo.Param(model.arcs, initialize=big_m)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def time_bounds(problem, i):
        return (
            pyo.value(problem.window_start[i]),
            pyo.value(problem.window_end[i]),
        )

    model.t = pyo.Var(
        model.nodes,
        domain=pyo.Reals,
        bounds=time_bounds,
    )
    model.return_time = pyo.Var(
        domain=pyo.Reals,
        bounds=(window_start[0], window_end[0]),
    )
    model.order = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, 8),
    )

    def outgoing_rule(problem, i):
        return sum(
            problem.x[i, j] for j in problem.nodes if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.nodes, rule=outgoing_rule)

    def incoming_rule(problem, j):
        return sum(
            problem.x[i, j] for i in problem.nodes if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.nodes, rule=incoming_rule)

    # Explicit subtour elimination remains valid with zero travel/service times.
    def subtour_rule(problem, i, j):
        return (
            problem.order[i] - problem.order[j] + 8 * problem.x[i, j]
            <= 7
        )

    model.subtour_elimination = pyo.Constraint(
        model.customer_arcs,
        rule=subtour_rule,
    )

    # t denotes service-start time, including waiting until a window opens.
    # The initial depot visit and final depot return have separate times.
    def timing_rule(problem, i, j):
        if j == 0:
            return pyo.Constraint.Skip
        return problem.t[j] >= (
            problem.t[i]
            + problem.service[i]
            + problem.travel[i, j]
            - problem.big_m[i, j] * (1 - problem.x[i, j])
        )

    model.visit_timing = pyo.Constraint(model.arcs, rule=timing_rule)

    def return_rule(problem, i):
        return problem.return_time >= (
            problem.t[i]
            + problem.service[i]
            + problem.travel[i, 0]
            - problem.big_m[i, 0] * (1 - problem.x[i, 0])
        )

    model.return_timing = pyo.Constraint(
        model.customers,
        rule=return_rule,
    )

    model.route_duration = pyo.Constraint(
        expr=model.return_time - model.t[0] <= model.horizon
    )

    model.total_travel = pyo.Objective(
        expr=sum(
            model.travel[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_travel))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}