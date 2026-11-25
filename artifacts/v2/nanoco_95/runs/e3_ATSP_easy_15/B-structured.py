# IR: {"sets":{"N":"{0,...,8}","V":"N\\{0}","A":"{(i,j) in N*N: i!=j}","B":"{(i,j) in V*V: i!=j}"},"params":{"transition_cost_matrix":"real[N,N], from params","coordinates_x":"real[N], from params; descriptive metadata","coordinates_y":"real[N], from params; descriptive metadata"},"variables":{"x":"binary[A]","u":"continuous[V], 1<=u[i]<=8"},"constraints":["outgoing[i]: sum(x[i,j] for j in N if j!=i)=1 for i in N","incoming[j]: sum(x[i,j] for i in N if i!=j)=1 for j in N","subtour[i,j]: u[i]-u[j]+8*x[i,j]<=7 for (i,j) in B"],"objective":"minimize sum(transition_cost_matrix[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    transition_cost_matrix = params["transition_cost_matrix"]
    coordinates_x = params["coordinates_x"]
    coordinates_y = params["coordinates_y"]

    model = pyo.ConcreteModel()

    model.N = pyo.RangeSet(0, 8)
    model.V = pyo.RangeSet(1, 8)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(9)
            for j in range(9)
            if i != j
        ],
    )
    model.B = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 9)
            for j in range(1, 9)
            if i != j
        ],
    )

    model.transition_cost_matrix = pyo.Param(
        model.N,
        model.N,
        initialize={
            (i, j): transition_cost_matrix[i][j]
            for i in range(9)
            for j in range(9)
        },
        within=pyo.Reals,
    )
    model.coordinates_x = pyo.Param(
        model.N,
        initialize={i: coordinates_x[i] for i in range(9)},
        within=pyo.Reals,
    )
    model.coordinates_y = pyo.Param(
        model.N,
        initialize={i: coordinates_y[i] for i in range(9)},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.V, domain=pyo.Reals, bounds=(1, 8))

    def outgoing_rule(patrol_model, i):
        return sum(
            patrol_model.x[i, j]
            for j in patrol_model.N
            if j != i
        ) == 1

    def incoming_rule(patrol_model, j):
        return sum(
            patrol_model.x[i, j]
            for i in patrol_model.N
            if i != j
        ) == 1

    def subtour_rule(patrol_model, i, j):
        return (
            patrol_model.u[i]
            - patrol_model.u[j]
            + 8 * patrol_model.x[i, j]
            <= 7
        )

    model.outgoing = pyo.Constraint(model.N, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.N, rule=incoming_rule)
    model.subtour = pyo.Constraint(model.B, rule=subtour_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transition_cost_matrix[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi HiGHS raises this when no feasible solution can be loaded.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}