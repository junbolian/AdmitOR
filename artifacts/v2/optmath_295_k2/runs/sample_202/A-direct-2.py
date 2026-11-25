import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Facilities and customers
    facilities = range(6)
    customers = range(9)
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Decision variables
    model.open_facility = pyo.Var(facilities, domain=pyo.Binary)
    model.ship = pyo.Var(facilities, customers, domain=pyo.NonNegativeReals)
    
    # Parameters
    fixed_cost = {i: params[f"fixed_cost_{i}"] for i in facilities}
    demand = {j: params[f"demand_{j}"] for j in customers}
    shipping_cost = {(i, j): params[f"shipping_cost_{i}_{j}"] for i in facilities for j in customers}
    capacity = {i: params[f"capacity_{i}"] for i in facilities}
    
    # Objective: minimize total cost
    model.total_cost = pyo.Objective(
        expr=sum(fixed_cost[i] * model.open_facility[i] for i in facilities) +
             sum(shipping_cost[i, j] * model.ship[i, j] for i in facilities for j in customers),
        sense=pyo.minimize
    )
    
    # Constraints
    # Demand satisfaction
    model.demand_constraint = pyo.ConstraintList()
    for j in customers:
        model.demand_constraint.add(
            sum(model.ship[i, j] for i in facilities) == demand[j]
        )
    
    # Capacity constraints
    model.capacity_constraint = pyo.ConstraintList()
    for i in facilities:
        model.capacity_constraint.add(
            sum(model.ship[i, j] for j in customers) <= capacity[i] * model.open_facility[i]
        )
    
    # Solve
    solver = Highs()
    solver.solve(model)
    
    # Get objective value
    try:
        obj_val = float(pyo.value(model.total_cost))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible'}