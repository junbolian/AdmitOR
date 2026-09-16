# sample_281

certified: 0.35509999999999997
vault label: 1.520688496320867
relative gap: 0.7664873503948217
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 6

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

The problem involves assigning 5 spectral peaks (labeled Peak 0 to Peak 4) to 6 amino acids (labeled Amino Acid 0 to Amino Acid 5) in a molecular analysis scenario. The goal is to minimize the total cost of these assignments while adhering to specific constraints. Each assignment of a peak to an amino acid has an associated cost, ranging from 0.3509 to 0.6976 units. The objective is to select the combination of assignments that results in the lowest possible total cost.

Each amino acid can be assigned to at most one peak, and each peak can be assigned to at most one amino acid. Exactly 4 assignments must be made in total. Additionally, certain pairs of assignments are restricted based on NOE (Nuclear Overhauser Effect) constraints, which ensure that assignments do not violate the spatial relationships inferred from the protein's 3D structure. For example, if Peak 0 is assigned to Amino Acid 0, then Peak 4 cannot be assigned to Amino Acid 1, 3, or 4. Similarly, if Peak 1 is assigned to Amino Acid 0, then Peak 2 cannot be assigned to Amino Acid 1, 3, or 4. These constraints are explicitly defined in the LP data, such as `NOE_0_4_0_1: x[0,0] + x[4,1] <= 1`, which ensures that Peak 0 cannot be assigned to Amino Acid 0 and Peak 4 to Amino Acid 1 simultaneously.

The decision variables are binary, meaning each assignment is either selected (1) or not (0). The problem is formulated as a linear programming problem, with the objective of minimizing the total cost while satisfying all constraints, including the NOE constraints, the uniqueness of assignments, and the requirement for exactly 4 assignments.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    costs = params["costs"]  # 5x6 matrix
    required_assignments = params["required_assignments"]
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    model.P = pyo.RangeSet(0, 4)  # peaks
    model.A = pyo.RangeSet(0, 5)  # amino acids
    
    # Variables
    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)
    
    # Objective
    def obj_rule(m):
        return sum(costs[i][j] * m.x[i, j] for i in m.P for j in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    # Exactly required_assignments assignments
    def total_assignments_rule(m):
        return sum(m.x[i, j] for i in m.P for j in m.A) == required_assignments
    model.total_assignments = pyo.Constraint(rule=total_assignments_rule)
    
    # Each peak assigned to at most one amino acid
    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.A) <= 1
    model.peak_constraint = pyo.Constraint(model.P, rule=peak_rule)
    
    # Each amino acid assigned to at most one peak
    def amino_acid_rule(m, j):
        return sum(m.x[i, j] for i in m.P) <= 1
    model.amino_acid_constraint = pyo.Constraint(model.A, rule=amino_acid_rule)
    
    # NOE constraints (from problem description)
    # NOE_0_4_0_1: x[0,0] + x[4,1] <= 1
    model.noe_0_4_0_1 = pyo.Constraint(expr=model.x[0,0] + model.x[4,1] <= 1)
    # NOE_0_4_0_3: x[0,0] + x[4,3] <= 1
    model.noe_0_4_0_3 = pyo.Constraint(expr=model.x[0,0] + model.x[4,3] <= 1)
    # NOE_0_4_0_4: x[0,0] + x[4,4] <= 1
    model.noe_0_4_0_4 = pyo.Constraint(expr=model.x[0,0] + model.x[4,4] <= 1)
    # NOE_1_2_0_1: x[1,0] + x[2,1] <= 1
    model.noe_1_2_0_1 = pyo.Constraint(expr=model.x[1,0] + model.x[2,1] <= 1)
    # NOE_1_2_0_3: x[1,0] + x[2,3] <= 1
    model.noe_1_2_0_3 = pyo.Constraint(expr=model.x[1,0] + model.x[2,3] <= 1)
    # NOE_1_2_0_4: x[1,0] + x[2,4] <= 1
    model.noe_1_2_0_4 = pyo.Constraint(expr=model.x[1,0] + model.x[2,4] <= 1)
    
    # Solve
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError):
        # If objective value cannot be retrieved, assume infeasible
        return {'objective': None, 'status': 'infeasible'}
```

## Clique member B-structured

```python
# IR: {"sets":{"P":"{0,1,2,3,4}","A":"{0,1,2,3,4,5}","NOE":"specified forbidden assignment pairs"},"params":{"costs":"dict/list mapping (i,j)->cost or nested costs[i][j]","required_assignments":"exact total assignments"},"vars":{"x[i,j]":"Binary assignment of peak i to amino acid j"},"constraints":["peak_match[i]: sum_j x[i,j] <= 1 for all i in P","amino_match[j]: sum_i x[i,j] <= 1 for all j in A","total_required: sum_{i,j} x[i,j] == required_assignments","noe[k]: x[i1,j1] + x[i2,j2] <= 1 for each forbidden pair k in NOE"],"objective":"minimize sum_{i,j} costs[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    peaks = list(range(5))
    amino_acids = list(range(6))

    raw_costs = params["costs"]
    required_assignments = params["required_assignments"]

    def get_cost(i_idx, j_idx):
        try:
            return float(raw_costs[i_idx][j_idx])
        except (TypeError, KeyError, IndexError):
            pass
        try:
            return float(raw_costs[(i_idx, j_idx)])
        except (TypeError, KeyError):
            pass
        try:
            return float(raw_costs[str((i_idx, j_idx))])
        except (TypeError, KeyError):
            pass
        return float(raw_costs[str(i_idx)][str(j_idx)])

    # Explicit NOE forbidden assignment pairs derived from the problem statement.
    noe_pairs = [
        ((0, 0), (4, 1)),
        ((0, 0), (4, 3)),
        ((0, 0), (4, 4)),
        ((1, 0), (2, 1)),
        ((1, 0), (2, 3)),
        ((1, 0), (2, 4)),
    ]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=peaks)
    model.A = pyo.Set(initialize=amino_acids)
    model.X_INDEX = pyo.Set(initialize=[(i_idx, j_idx) for i_idx in peaks for j_idx in amino_acids], dimen=2)
    model.NOE_INDEX = pyo.Set(initialize=list(range(len(noe_pairs))))

    model.x = pyo.Var(model.X_INDEX, domain=pyo.Binary)

    model.peak_match = pyo.Constraint(
        model.P,
        rule=lambda model, i_idx: sum(model.x[i_idx, j_idx] for j_idx in model.A) <= 1,
    )

    model.amino_match = pyo.Constraint(
        model.A,
        rule=lambda model, j_idx: sum(model.x[i_idx, j_idx] for i_idx in model.P) <= 1,
    )

    model.total_required = pyo.Constraint(
        expr=sum(model.x[i_idx, j_idx] for i_idx in model.P for j_idx in model.A) == required_assignments
    )

    def noe_rule(model, pair_idx):
        (i1, j1), (i2, j2) = noe_pairs[pair_idx]
        return model.x[i1, j1] + model.x[i2, j2] <= 1

    model.noe = pyo.Constraint(model.NOE_INDEX, rule=noe_rule)

    model.objective = pyo.Objective(
        expr=sum(get_cost(i_idx, j_idx) * model.x[i_idx, j_idx] for i_idx in model.P for j_idx in model.A),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.objective))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    required_assignments = params["required_assignments"]
    
    num_peaks = 5
    num_amino_acids = 6
    
    try:
        model = gp.Model("PeakAssignment")
        model.setParam('OutputFlag', 0)
        
        # Decision variables: x[i,j] = 1 if peak i assigned to amino acid j
        x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")
        
        # Objective: minimize total assignment cost
        obj = gp.quicksum(costs[i][j] * x[i, j] 
                         for i in range(num_peaks) 
                         for j in range(num_amino_acids))
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Constraint: each peak assigned to at most one amino acid
        for i in range(num_peaks):
            model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
                           name=f"peak_{i}_max_one")
        
        # Constraint: each amino acid assigned to at most one peak
        for j in range(num_amino_acids):
            model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
                           name=f"amino_{j}_max_one")
        
        # Constraint: exactly required_assignments assignments must be made
        model.addConstr(gp.quicksum(x[i, j] 
                                   for i in range(num_peaks) 
                                   for j in range(num_amino_acids)) == required_assignments,
                       name="exact_assignments")
        
        # NOE constraints based on problem description
        # If Peak 0 -> AA 0, then Peak 4 cannot -> AA 1, 3, or 4
        model.addConstr(x[0, 0] + x[4, 1] <= 1, name="NOE_0_4_0_1")
        model.addConstr(x[0, 0] + x[4, 3] <= 1, name="NOE_0_4_0_3")
        model.addConstr(x[0, 0] + x[4, 4] <= 1, name="NOE_0_4_0_4")
        
        # If Peak 1 -> AA 0, then Peak 2 cannot -> AA 1, 3, or 4
        model.addConstr(x[1, 0] + x[2, 1] <= 1, name="NOE_1_2_0_1")
        model.addConstr(x[1, 0] + x[2, 3] <= 1, name="NOE_1_2_0_3")
        model.addConstr(x[1, 0] + x[2, 4] <= 1, name="NOE_1_2_0_4")
        
        # Solve
        model.optimize()
        
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
```
