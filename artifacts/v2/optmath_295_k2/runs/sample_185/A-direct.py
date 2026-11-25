import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_cities = params["num_cities"]
    cities = list(range(num_cities))
    cities_set = pyo.Set(initialize=cities)
    
    # Distance matrix
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"distance_{i}_{j}"]
    
    model = pyo.ConcreteModel()
    
    # Arcs
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])
    
    # Decision variables: x[i,j] = 1 if travel from i to j
    model.x = pyo.Var(model.arcs, within=pyo.Binary, initialize=0)
    
    # Position variables: u[i] = position of city i in tour
    lower = params["position_lower_bound"]
    upper = params["position_upper_bound"]
    model.u = pyo.Var(cities_set, bounds=(lower, upper), initialize=lower)
    # Fix city 0 at the first position to break symmetry
    model.u[0].fix(lower)
    
    # Objective
    model.obj = pyo.Objective(
        expr=sum(dist[i, j] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize
    )
    
    # Each city left exactly once
    def leave_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1
    model.leave_con = pyo.Constraint(cities_set, rule=leave_rule)
    
    # Each city entered exactly once
    def enter_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1
    model.enter_con = pyo.Constraint(cities_set, rule=enter_rule)
    
    # MTZ subtour elimination: for i,j != 0 with i != j:
    # u[j] >= u[i] + 1 - M*(1 - x[i,j])
    n = num_cities
    bigM = upper - lower + n
    
    def subtour_rule(mdl, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return mdl.u[j] >= mdl.u[i] + 1 - bigM * (1 - mdl.x[i, j])
    model.subtour_con = pyo.Constraint(model.arcs, rule=subtour_rule)
    
    solver = Highs()
    solver.solve(model)
    
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}