import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['E', 'F', 'G', 'H']
    cost = {
        ('E', 'F'): params["cost_E_F"],
        ('E', 'G'): params["cost_E_G"],
        ('E', 'H'): params["cost_E_H"],
        ('F', 'E'): params["cost_F_E"],
        ('F', 'G'): params["cost_F_G"],
        ('F', 'H'): params["cost_F_H"],
        ('G', 'E'): params["cost_G_E"],
        ('G', 'F'): params["cost_G_F"],
        ('G', 'H'): params["cost_G_H"],
        ('H', 'E'): params["cost_H_E"],
        ('H', 'F'): params["cost_H_F"],
        ('H', 'G'): params["cost_H_G"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    model.out_flow = pyo.Constraint(
        model.cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )
    model.in_flow = pyo.Constraint(
        model.cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (MTZ) over the 4 cities
    nodes = ['F', 'G', 'H']
    model.u = pyo.Var(nodes, bounds=(0, len(cities) - 1))
    model.subtour = pyo.ConstraintList()
    for i in nodes:
        for j in nodes:
            if i != j:
                model.subtour.add(
                    model.u[i] - model.u[j] + (len(cities) - 1) * model.x[(i, j)]
                    <= len(cities) - 2
                )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}