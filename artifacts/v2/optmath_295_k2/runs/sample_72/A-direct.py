import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Read parameters
    assignment_cost = params["assignment_cost"]
    employee_total_capacity = params["employee_total_capacity"]
    employee_project_limit = params["employee_project_limit"]
    project_demand = params["project_demand"]
    
    # Define sets
    employees = range(5)
    projects = range(5)
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Decision variables: x[i,j] = units assigned from employee i to project j
    model.x = pyo.Var(employees, projects, domain=pyo.NonNegativeReals)
    
    # Objective: minimize total assignment cost
    model.obj = pyo.Objective(
        expr=sum(assignment_cost[i][j] * model.x[i, j] for i in employees for j in projects),
        sense=pyo.minimize
    )
    
    # Constraint: each employee's total contribution exactly equals their capacity
    def employee_capacity_rule(model, i):
        return sum(model.x[i, j] for j in projects) == employee_total_capacity[i]
    model.employee_capacity_con = pyo.Constraint(employees, rule=employee_capacity_rule)
    
    # Constraint: each project's demand is exactly met
    def project_demand_rule(model, j):
        return sum(model.x[i, j] for i in employees) == project_demand[j]
    model.project_demand_con = pyo.Constraint(projects, rule=project_demand_rule)
    
    # Constraint: each employee's contribution to each project cannot exceed the limit
    def project_limit_rule(model, i, j):
        return model.x[i, j] <= employee_project_limit[i][j]
    model.project_limit_con = pyo.Constraint(employees, projects, rule=project_limit_rule)
    
    # Solve
    solver = Highs()
    solver.solve(model)
    
    # Get objective value
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible'}