# IR: {"sets":{"V":"{0,...,num_cities-1}","W":"V\\{0}","A":"{(i,j) in V x V: i!=j}"},"params":{"distance[i,j]":"params['distance_i_j'] for (i,j) in A","num_cities":"params['num_cities']","u0_fixed":"params['u0_fixed']","u_lower_bound":"params['u_lower_bound']","u_upper_bound":"params['u_upper_bound']"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous, i in V; bounds [u_lower_bound,u_upper_bound] for i in W"},"constraints":["For each i in V: sum(x[i,j] for j in V if j!=i)=1","For each j in V: sum(x[i,j] for i in V if i!=j)=1","u[0]=u0_fixed","For distinct i,j in W: u[i]-u[j]+num_cities*x[i,j]<=num_cities-1"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    city_count = int(num_cities)
    if city_count != num_cities or city_count < 2:
        raise ValueError("num_cities must be an integer of at least two.")

    cities = list(range(city_count))
    arcs = [(i, j) for i in cities for j in cities if i != j]
    distances = {
        (i, j): params[f"distance_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=cities, ordered=True)
    model.W = pyo.Set(initialize=cities[1:], ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.city_count = pyo.Param(initialize=num_cities)
    model.distance = pyo.Param(model.A, initialize=distances)
    model.root_order = pyo.Param(initialize=params["u0_fixed"])
    model.order_lower = pyo.Param(initialize=params["u_lower_bound"])
    model.order_upper = pyo.Param(initialize=params["u_upper_bound"])

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def order_bounds(block, i):
        if i == 0:
            return None, None
        return block.order_lower, block.order_upper

    model.u = pyo.Var(model.V, domain=pyo.Reals, bounds=order_bounds)

    def outgoing_rule(block, i):
        return sum(block.x[i, j] for j in block.V if j != i) == 1

    def incoming_rule(block, j):
        return sum(block.x[i, j] for i in block.V if i != j) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)
    model.root_order_constraint = pyo.Constraint(
        expr=model.u[0] == model.root_order
    )

    def subtour_rule(block, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            block.u[i] - block.u[j] + block.city_count * block.x[i, j]
            <= block.city_count - 1
        )

    model.subtour = pyo.Constraint(model.W, model.W, rule=subtour_rule)
    model.total_distance = pyo.Objective(
        expr=sum(model.distance[i, j] * model.x[i, j] for i, j in model.A),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}