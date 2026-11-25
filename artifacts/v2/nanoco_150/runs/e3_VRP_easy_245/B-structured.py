# IR: {"sets":{"K":"0..num_trucks-1","N":"0..num_sites","S":"1..num_sites","A":"{(i,j) in N x N: i != j}"},"params":{"num_trucks":"positive integer","num_sites":"positive integer","travel_cost":"matrix indexed [i][j] for i,j in N"},"variables":{"x[k,i,j]":"binary, k in K, (i,j) in A","u[i]":"continuous in [1,num_sites], i in S"},"constraints":["For each i in S: sum(k in K, j in N excluding i) x[k,i,j] = 1.","For each k in K and i in S: sum(j in N excluding i) x[k,i,j] = sum(j in N excluding i) x[k,j,i].","For each k in K: sum(j in S) x[k,0,j] = 1.","For each k in K: sum(i in S) x[k,i,0] = 1.","For distinct i,j in S: u[i] - u[j] + num_sites * sum(k in K) x[k,i,j] <= num_sites - 1."],"objective":"Minimize sum(k in K, (i,j) in A) travel_cost[i][j] * x[k,i,j]."}
import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_trucks = operator.index(params["num_trucks"])
    num_sites = operator.index(params["num_sites"])
    travel_cost = params["travel_cost"]

    if num_trucks <= 0 or num_sites <= 0:
        return {"objective": None, "status": "invalid_dimensions"}

    # Each truck must serve at least one site on its depot-to-depot circuit.
    if num_trucks > num_sites:
        return {"objective": None, "status": "infeasible"}

    model = pyo.ConcreteModel()

    model.K = pyo.Set(initialize=range(num_trucks), ordered=True)
    model.N = pyo.Set(initialize=range(num_sites + 1), ordered=True)
    model.S = pyo.Set(initialize=range(1, num_sites + 1), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(num_sites + 1)
            for j in range(num_sites + 1)
            if i != j
        ],
        ordered=True,
    )

    model.site_count = pyo.Param(
        initialize=num_sites, within=pyo.PositiveIntegers
    )
    model.arc_cost = pyo.Param(
        model.A,
        initialize=lambda mdl, i, j: travel_cost[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.K, model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.S,
        domain=pyo.Reals,
        bounds=(1, num_sites),
    )

    def unique_service_rule(mdl, i):
        return sum(
            mdl.x[k, i, j]
            for k in mdl.K
            for j in mdl.N
            if j != i
        ) == 1

    model.unique_service = pyo.Constraint(
        model.S, rule=unique_service_rule
    )

    def flow_balance_rule(mdl, k, i):
        return (
            sum(mdl.x[k, i, j] for j in mdl.N if j != i)
            == sum(mdl.x[k, j, i] for j in mdl.N if j != i)
        )

    model.flow_balance = pyo.Constraint(
        model.K, model.S, rule=flow_balance_rule
    )

    def depot_departure_rule(mdl, k):
        return sum(mdl.x[k, 0, j] for j in mdl.S) == 1

    model.depot_departure = pyo.Constraint(
        model.K, rule=depot_departure_rule
    )

    def depot_return_rule(mdl, k):
        return sum(mdl.x[k, i, 0] for i in mdl.S) == 1

    model.depot_return = pyo.Constraint(
        model.K, rule=depot_return_rule
    )

    def subtour_elimination_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i]
            - mdl.u[j]
            + mdl.site_count * sum(mdl.x[k, i, j] for k in mdl.K)
            <= mdl.site_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.S, model.S, rule=subtour_elimination_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.x[k, i, j]
            for k in model.K
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}