# IR: {"sets":{"V":[0,1,2,3,4],"W":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","B":"{(i,j) in W x W: i != j}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A","u_lower":"params['u_lower']","u_upper":"params['u_upper']"},"variables":{"x[i,j]":{"index":"A","type":"Binary"},"u[i]":{"index":"V","type":"Real","bounds":"unbounded; position constraints apply only to W"}},"constraints":["sum(x[i,j] for j in V if j != i) == 1 for i in V","sum(x[i,j] for i in V if i != j) == 1 for j in V","u[i] >= u_lower for i in W","u[i] <= u_upper for i in W","u[i] - u[j] + 5*x[i,j] <= 4 for (i,j) in B"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(5), ordered=True)
    model.W = pyo.Set(initialize=range(1, 5), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(5) for j in range(5) if i != j],
    )
    model.B = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in range(1, 5) for j in range(1, 5) if i != j
        ],
    )

    model.cost = pyo.Param(
        model.A,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i in range(5)
            for j in range(5)
            if i != j
        },
        within=pyo.Reals,
    )
    model.u_lower = pyo.Param(
        initialize=params["u_lower"], within=pyo.Reals
    )
    model.u_upper = pyo.Param(
        initialize=params["u_upper"], within=pyo.Reals
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.V, domain=pyo.Reals)

    def departure_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.V if j != i) == 1

    def arrival_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.V if i != j) == 1

    def position_lower_rule(instance, i):
        return instance.u[i] >= instance.u_lower

    def position_upper_rule(instance, i):
        return instance.u[i] <= instance.u_upper

    def subtour_rule(instance, i, j):
        return instance.u[i] - instance.u[j] + 5 * instance.x[i, j] <= 4

    model.departure_constraints = pyo.Constraint(
        model.V, rule=departure_rule
    )
    model.arrival_constraints = pyo.Constraint(
        model.V, rule=arrival_rule
    )
    model.position_lower_constraints = pyo.Constraint(
        model.W, rule=position_lower_rule
    )
    model.position_upper_constraints = pyo.Constraint(
        model.W, rule=position_upper_rule
    )
    model.subtour_constraints = pyo.Constraint(
        model.B, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i, j] * model.x[i, j] for i, j in model.A),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}