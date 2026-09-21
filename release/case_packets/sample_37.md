# sample_37

certified: 1.546
vault label: 1.545455400270471
relative gap: 0.0003523878653720557
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 5

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

In a biochemical research facility, scientists are working on assigning spectral peaks from nuclear magnetic resonance (NMR) experiments to specific amino acids in a protein sequence. The goal is to minimize the overall assignment cost while adhering to specific constraints to ensure accurate and feasible assignments. There are 4 spectral peaks (labeled Peak 0 to Peak 3) and 5 amino acids (labeled Amino Acid 0 to Amino Acid 4) in the protein sequence. Each peak must be assigned to at most one amino acid, and each amino acid can be assigned to at most one peak. A total of exactly 3 assignments must be made between peaks and amino acids. The cost of assigning a specific peak to a specific amino acid varies, as shown in the cost matrix. Assigning Peak 0 to Amino Acid 0 costs 0.537, to Amino Acid 1 costs 0.669, to Amino Acid 2 costs 0.619, to Amino Acid 3 costs 0.527, and to Amino Acid 4 costs 0.656. Assigning Peak 1 to Amino Acid 0 costs 0.675, to Amino Acid 1 costs 0.501, to Amino Acid 2 costs 0.601, to Amino Acid 3 costs 0.598, and to Amino Acid 4 costs 0.603. Assigning Peak 2 to Amino Acid 0 costs 0.539, to Amino Acid 1 costs 0.599, to Amino Acid 2 costs 0.612, to Amino Acid 3 costs 0.576, and to Amino Acid 4 costs 0.623. Assigning Peak 3 to Amino Acid 0 costs 0.587, to Amino Acid 1 costs 0.670, to Amino Acid 2 costs 0.530, to Amino Acid 3 costs 0.670, and to Amino Acid 4 costs 0.518. Each amino acid can be assigned to at most one peak. For example, Amino Acid 0 can only be assigned to one of Peak 0, Peak 1, Peak 2, or Peak 3. Similarly, each peak can be assigned to at most one amino acid. For example, Peak 0 can only be assigned to one of Amino Acid 0, Amino Acid 1, Amino Acid 2, Amino Acid 3, or Amino Acid 4. Exactly 3 assignments must be made between peaks and amino acids. Certain pairs of assignments are restricted based on the distance between amino acids. For example, if Peak 0 is assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4. If Peak 1 is assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4. These constraints ensure that assignments respect the spatial relationships between amino acids in the protein structure. The goal is to minimize the total cost of assigning peaks to amino acids while satisfying all the constraints mentioned above. The total cost is the sum of the individual costs of the selected assignments. The decision variables are binary, meaning each assignment is either made (1) or not made (0).

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    cost_matrix = params["cost_matrix"]  # list of lists, shape (4, 5)
    required_assignments = params["required_assignments"]  # integer

    # Create model
    model = pyo.ConcreteModel()

    # Sets
    model.P = pyo.RangeSet(0, 3)  # peaks
    model.A = pyo.RangeSet(0, 4)  # amino acids

    # Decision variables
    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    # Objective: minimize total assignment cost
    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for i in model.P for j in model.A),
        sense=pyo.minimize
    )

    # Constraints
    # Each peak assigned to at most one amino acid
    def peak_limit_rule(model, i):
        return sum(model.x[i, j] for j in model.A) <= 1
    model.peak_limit = pyo.Constraint(model.P, rule=peak_limit_rule)

    # Each amino acid assigned to at most one peak
    def amino_acid_limit_rule(model, j):
        return sum(model.x[i, j] for i in model.P) <= 1
    model.amino_acid_limit = pyo.Constraint(model.A, rule=amino_acid_limit_rule)

    # Exactly required_assignments assignments must be made
    def total_assignments_rule(model):
        return sum(model.x[i, j] for i in model.P for j in model.A) == required_assignments
    model.total_assignments = pyo.Constraint(rule=total_assignments_rule)

    # Conflict constraints (hardcoded as per problem description)
    # If Peak 0 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    def conflict1_rule(model):
        return model.x[0, 1] + model.x[2, 4] <= 1
    model.conflict1 = pyo.Constraint(rule=conflict1_rule)

    # If Peak 1 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    def conflict2_rule(model):
        return model.x[1, 1] + model.x[2, 4] <= 1
    model.conflict2 = pyo.Constraint(rule=conflict2_rule)

    # Solve
    solver = Highs()
    result = solver.solve(model)

    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except ValueError:
        return {'objective': None, 'status': 'infeasible or no solution found'}
```

## Clique member B-structured

```python
# {"sets":{"P":["0","1","2","3"],"A":["0","1","2","3","4"]},"params":{"cost_matrix":"4x5 numeric matrix from params['cost_matrix']","required_assignments":"scalar from params['required_assignments']"},"vars":{"x[p,a]":"binary"},"constraints":["sum_a x[p,a] <= 1 for all p","sum_p x[p,a] <= 1 for all a","sum_p,sum_a x[p,a] == required_assignments","x[0,1] + x[2,4] <= 1","x[1,1] + x[2,4] <= 1"],"objective":"min sum_p,sum_a cost_matrix[p][a] * x[p,a]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.A = pyo.RangeSet(0, 4)

    cost_matrix = params["cost_matrix"]
    required_assignments = params["required_assignments"]

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost_matrix[p][a] * model.x[p, a] for p in model.P for a in model.A)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_limit_rule(model, p):
        return sum(model.x[p, a] for a in model.A) <= 1
    model.peak_limit = pyo.Constraint(model.P, rule=peak_limit_rule)

    def amino_limit_rule(model, a):
        return sum(model.x[p, a] for p in model.P) <= 1
    model.amino_limit = pyo.Constraint(model.A, rule=amino_limit_rule)

    model.total_assignments = pyo.Constraint(
        expr=sum(model.x[p, a] for p in model.P for a in model.A) == required_assignments
    )

    model.restrict_01_24 = pyo.Constraint(expr=model.x[0, 1] + model.x[2, 4] <= 1)
    model.restrict_11_24 = pyo.Constraint(expr=model.x[1, 1] + model.x[2, 4] <= 1)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.objective))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    required_assignments = params["required_assignments"]
    
    # Infer dimensions from cost_matrix
    num_peaks = len(cost_matrix)
    num_amino_acids = len(cost_matrix[0]) if num_peaks > 0 else 0
    
    # Create model
    model = gp.Model("NMR_Assignment")
    model.setParam('OutputFlag', 0)
    
    # Decision variables: x[i][j] = 1 if peak i is assigned to amino acid j
    x = {}
    for i in range(num_peaks):
        for j in range(num_amino_acids):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # Objective: minimize total assignment cost
    obj = gp.quicksum(cost_matrix[i][j] * x[i, j] 
                      for i in range(num_peaks) 
                      for j in range(num_amino_acids))
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraint: each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
                       name=f"peak_{i}_at_most_one")
    
    # Constraint: each amino acid assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
                       name=f"amino_acid_{j}_at_most_one")
    
    # Constraint: exactly required_assignments assignments must be made
    model.addConstr(gp.quicksum(x[i, j] 
                                for i in range(num_peaks) 
                                for j in range(num_amino_acids)) == required_assignments,
                   name="total_assignments")
    
    # Distance-based restrictions from problem description:
    # If Peak 0 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[0, 1] + x[2, 4] <= 1, name="restriction_peak0_aa1_peak2_aa4")
    
    # If Peak 1 assigned to Amino Acid 1, then Peak 2 cannot be assigned to Amino Acid 4
    model.addConstr(x[1, 1] + x[2, 4] <= 1, name="restriction_peak1_aa1_peak2_aa4")
    
    # Solve
    model.optimize()
    
    # Return results
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
```
