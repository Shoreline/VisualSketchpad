import numpy as np

def find_perpendicular_intersection(A, B, C):
    """Calculate point E on BC where AE is perpendicular to BC"""
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    
    # Calculate direction vector of BC
    BC = C - B
    
    # Handle vertical lines separately
    if BC[0] == 0:
        return [B[0], A[1]]
    
    # Calculate slope of BC
    slope_BC = BC[1] / BC[0]
    # Perpendicular slope is negative reciprocal
    slope_perpendicular = -1 / slope_BC
    
    # Convert to standard form Ax + By + C = 0 for both lines
    # Line AE: y - y_A = slope_perpendicular * (x - x_A)
    A_coeff = -slope_perpendicular
    B_coeff = 1
    C_coeff = -A_coeff * A[0] - B_coeff * A[1]
    
    # Line BC: y - y_B = slope_BC * (x - x_B)
    A_BC = -slope_BC
    B_BC = 1
    C_BC = -A_BC * B[0] - B_BC * B[1]
    
    # Solve system of equations
    matrix = np.array([[A_coeff, B_coeff], [A_BC, B_BC]])
    constants = np.array([-C_coeff, -C_BC])
    intersection = np.linalg.solve(matrix, constants)
    return intersection.tolist()

def find_parallel_intersection(A, B, C):
    """Calculate point E on BC where AE is parallel to BC"""
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    
    # Calculate direction vector of BC
    direction_BC = C - B
    length_BC = np.linalg.norm(direction_BC)
    
    # Normalize and extend from A
    direction_AE = direction_BC / np.linalg.norm(direction_BC)
    E = A + direction_AE * length_BC
    
    return E.tolist()
