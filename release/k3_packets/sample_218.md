# sample_218

certified: 2877.0
vault label: 2939.0
relative gap: 0.02109561075195645
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 4

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

Project Assignment in a Consulting Firm

Imagine you are managing a consulting firm with seven consultants and six ongoing projects. Each consultant has a specific number of hours they can dedicate to projects, and each project requires a certain number of hours to be completed. Your goal is to assign consultants to projects in a way that minimizes the total cost while ensuring all project requirements are met and no consultant exceeds their available hours.

#### Consultants and Their Availability:
- **Consultant 0**: Available for 0 hours (currently unavailable for assignments).
- **Consultant 1**: Available for 14 hours.
- **Consultant 2**: Available for 20 hours.
- **Consultant 3**: Available for 15 hours.
- **Consultant 4**: Available for 19 hours.
- **Consultant 5**: Available for 16 hours.
- **Consultant 6**: Available for 19 hours.

#### Projects and Their Hourly Requirements:
- **Project 0**: Requires 20 hours.
- **Project 1**: Requires 18 hours.
- **Project 2**: Requires 15 hours.
- **Project 3**: Requires 19 hours.
- **Project 4**: Requires 16 hours.
- **Project 5**: Requires 15 hours.

#### Assignment Costs:
The cost of assigning a consultant to a project varies based on their expertise and the project's complexity. The costs per hour are as follows:

- **Consultant 0**: 
  - Project 0: $33/hour, Project 1: $34/hour, Project 2: $25/hour, Project 3: $31/hour, Project 4: $34/hour, Project 5: $25/hour.
- **Consultant 1**: 
  - Project 0: $31/hour, Project 1: $30/hour, Project 2: $28/hour, Project 3: $29/hour, Project 4: $25/hour, Project 5: $33/hour.
- **Consultant 2**: 
  - Project 0: $35/hour, Project 1: $30/hour, Project 2: $30/hour, Project 3: $28/hour, Project 4: $30/hour, Project 5: $28/hour.
- **Consultant 3**: 
  - Project 0: $34/hour, Project 1: $35/hour, Project 2: $31/hour, Project 3: $32/hour, Project 4: $25/hour, Project 5: $25/hour.
- **Consultant 4**: 
  - Project 0: $28/hour, Project 1: $30/hour, Project 2: $32/hour, Project 3: $35/hour, Project 4: $27/hour, Project 5: $29/hour.
- **Consultant 5**: 
  - Project 0: $30/hour, Project 1: $29/hour, Project 2: $27/hour, Project 3: $35/hour, Project 4: $35/hour, Project 5: $26/hour.
- **Consultant 6**: 
  - Project 0: $35/hour, Project 1: $31/hour, Project 2: $33/hour, Project 3: $25/hour, Project 4: $30/hour, Project 5: $33/hour.

#### Constraints:
1. **Consultant Availability**: Each consultant can only be assigned up to their available hours. For example:
   - Consultant 1 can work up to 14 hours across all projects.
   - Consultant 2 can work up to 20 hours, and so on.

2. **Project Requirements**: Each project must receive exactly the required number of hours. For example:
   - Project 0 must receive exactly 20 hours from the assigned consultants.
   - Project 1 must receive exactly 18 hours, and so on.

3. **Assignment Limits**: There are limits on how many hours a consultant can work on a specific project. For example:
   - Consultant 0 can work up to 8 hours on Project 0, 8 hours on Project 1, 9 hours on Project 2, 10 hours on Project 3, 7 hours on Project 4, and 5 hours on Project 5.
   - Similar limits apply to all other consultants and projects.

#### Objective:
Your task is to assign consultants to projects in such a way that:
- All project requirements are met.
- No consultant exceeds their available hours.
- The total cost of all assignments is minimized.

This involves carefully balancing the assignments to ensure that the most cost-effective consultants are used for each project while respecting their availability and the project-specific limits. The goal is to achieve the lowest possible total cost while meeting all operational constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract data from params
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]
    
    # Determine dimensions
    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)
    
    # Validate dimensions
    if (len(assignment_costs) != num_consultants or 
        any(len(row) != num_projects for row in assignment_costs)):
        return {"objective": None, "status": "invalid assignment_costs dimensions"}
    if (len(assignment_limits) != num_consultants or 
        any(len(row) != num_projects for row in assignment_limits)):
        return {"objective": None, "status": "invalid assignment_limits dimensions"}
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    model.C = pyo.Set(initialize=range(num_consultants))
    model.P = pyo.Set(initialize=range(num_projects))
    
    # Variables: hours assigned from consultant i to project j
    model.x = pyo.Var(model.C, model.P, within=pyo.NonNegativeReals)
    
    # Objective: minimize total cost
    def obj_rule(m):
        return sum(assignment_costs[i][j] * m.x[i, j] 
                   for i in m.C for j in m.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    # Consultant availability constraints
    def availability_rule(m, i):
        return sum(m.x[i, j] for j in m.P) <= consultant_availability[i]
    model.availability_con = pyo.Constraint(model.C, rule=availability_rule)
    
    # Project requirements constraints
    def requirements_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == project_requirements[j]
    model.requirements_con = pyo.Constraint(model.P, rule=requirements_rule)
    
    # Assignment limits constraints
    def limits_rule(m, i, j):
        return m.x[i, j] <= assignment_limits[i][j]
    model.limits_con = pyo.Constraint(model.C, model.P, rule=limits_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution was found
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible or no solution found"}
```

## Clique member B-structured

```python
# {"sets":{"consultants":"range(7)","projects":"range(6)"},"params":{"consultant_availability":"hours available per consultant","project_requirements":"required hours per project","assignment_costs":"cost per hour for consultant-project pair","assignment_limits":"max hours for consultant-project pair"},"decision_variables":{"assign_hours":{"type":"NonNegativeReals","index":"consultants,projects"}},"constraints":["sum_j assign_hours[i,j] <= consultant_availability[i] for each consultant i","sum_i assign_hours[i,j] == project_requirements[j] for each project j","assign_hours[i,j] <= assignment_limits[i][j] for each consultant i, project j"],"objective":"minimize sum_{i,j} assignment_costs[i][j] * assign_hours[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultants = range(7)
    projects = range(6)

    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]

    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 6)
    model.projects = pyo.RangeSet(0, 5)

    model.assign_hours = pyo.Var(model.consultants, model.projects, domain=pyo.NonNegativeReals)

    def availability_rule(model, consultant):
        return sum(model.assign_hours[consultant, project] for project in projects) <= consultant_availability[consultant]

    model.availability_con = pyo.Constraint(model.consultants, rule=availability_rule)

    def requirement_rule(model, project):
        return sum(model.assign_hours[consultant, project] for consultant in consultants) == project_requirements[project]

    model.requirement_con = pyo.Constraint(model.projects, rule=requirement_rule)

    def assignment_limit_rule(model, consultant, project):
        return model.assign_hours[consultant, project] <= assignment_limits[consultant][project]

    model.assignment_limit_con = pyo.Constraint(model.consultants, model.projects, rule=assignment_limit_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            assignment_costs[consultant][project] * model.assign_hours[consultant, project]
            for consultant in consultants
            for project in projects
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read parameters
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]
    
    # Determine problem dimensions
    num_consultants = len(consultant_availability)
    num_projects = len(project_requirements)
    
    try:
        # Create model
        model = gp.Model("ConsultingAssignment")
        model.setParam('OutputFlag', 0)
        
        # Decision variables: hours assigned from consultant i to project j
        x = {}
        for i in range(num_consultants):
            for j in range(num_projects):
                x[i, j] = model.addVar(
                    lb=0,
                    ub=assignment_limits[i][j],
                    vtype=GRB.CONTINUOUS,
                    name=f"x_{i}_{j}"
                )
        
        # Objective: minimize total cost
        obj_expr = gp.quicksum(
            assignment_costs[i][j] * x[i, j]
            for i in range(num_consultants)
            for j in range(num_projects)
        )
        model.setObjective(obj_expr, GRB.MINIMIZE)
        
        # Constraint 1: Consultant availability
        for i in range(num_consultants):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(num_projects)) <= consultant_availability[i],
                name=f"availability_{i}"
            )
        
        # Constraint 2: Project requirements
        for j in range(num_projects):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(num_consultants)) == project_requirements[j],
                name=f"requirement_{j}"
            )
        
        # Solve the model
        model.optimize()
        
        # Check status and return results
        if model.status == GRB.OPTIMAL:
            return {
                "objective": model.objVal,
                "status": "optimal"
            }
        elif model.status == GRB.INFEASIBLE:
            return {
                "objective": None,
                "status": "infeasible"
            }
        elif model.status == GRB.UNBOUNDED:
            return {
                "objective": None,
                "status": "unbounded"
            }
        else:
            return {
                "objective": None,
                "status": f"status_{model.status}"
            }
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }
    except Exception as e:
        raise
```
