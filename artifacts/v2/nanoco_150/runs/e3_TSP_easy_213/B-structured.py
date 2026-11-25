# IR: {"sets":{"V":"0..7","C":"1..7","A":"{(i,j) in V x V: i != j}"},"params":{"travel_time_matrix":"params['travel_time_matrix'], indexed by V x V"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,7] for i in C"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1.","For each j in V: sum(x[i,j] for i in V if i != j) = 1.","For each distinct i,j in C: u[i] - u[j] + 7*x[i,j] <= 6."],"objective":"Minimize sum(travel_time_matrix[i][j]*x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    travel_time_matrix = params["travel_time_matrix"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.sites = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.travel_time = pyo.Param(
        model.arcs,
        initialize={
            (i, j): travel_time_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.sites,
        domain=pyo.Reals,
        bounds=(1, len(model.sites)),
    )

    def departure_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.nodes if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.nodes, rule=departure_rule
    )

    def arrival_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.nodes if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.nodes, rule=arrival_rule
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        site_count = len(mdl.sites)
        return (
            mdl.u[i] - mdl.u[j] + site_count * mdl.x[i, j]
            <= site_count - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.sites, model.sites, rule=subtour_rule
    )

    model.total_travel_time = pyo.Objective(
        expr=sum(
            model.travel_time[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_travel_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}