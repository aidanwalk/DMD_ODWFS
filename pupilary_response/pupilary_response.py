"""
The purpose of this script is to 

1. Model the pupilary response curve shown in TI:
    DLP230NP and DLP230NPSE .23 1080p Digital Micromirror Devices
    Figure 6-2 (page 27)
    
2. Plot the response curve (i.e replicate Figure 6-2)

3. Reverse the response curve to find the input that would produce a desired output.

"""

import numpy as np
import matplotlib.pyplot as plt


def perception_correction(input_level, A=1, gamma=2.2):
    """
    Convert intensity to response using the model from TI.
    This is the correction TI uses to determine the micromirror duty cycle
    from an input intensity.
    
    Parameters:
    -----------
    intensity : float or np.ndarray
        Input intensity value(s) in the range [0, 1].
    
    Returns:
    --------
    response : float or np.ndarray
        Corresponding response value(s) in the range [0, 1].
    """
    output_level = A * input_level**gamma
    return output_level



def reverse_perception_correction(output_level, A=1, gamma=2.2):
    """
    Convert response to intensity using the inverse of the model from TI.
    
    Parameters:
    -----------
    output_level : float or np.ndarray
        Output response value(s) in the range [0, 1].
    
    Returns:
    --------
    intensity : float or np.ndarray
        Corresponding input intensity value(s) in the range [0, 1].
    """
    input_level = (output_level / A)**(1/gamma)
    return input_level



if __name__ == "__main__":
    # This is the conversion the DMD does to determine micromirror duty cycle 
    # from an input intensity.
    input_levels = np.linspace(0, 1, 100)
    output_levels = perception_correction(input_levels)
    
    # Plot the response curve
    plt.figure(figsize=(8, 6))
    plt.plot(input_levels, output_levels, label='gamma=2.2', color='black')
    plt.title('Pupilary Response Curve')
    plt.xlabel('Input Level')
    plt.ylabel('Output Level')
    plt.grid()
    plt.legend()
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.savefig('pupilary_response_curve.png')
    
    
    # Now, model what happens when we input intensit levels into the DMD 
    # that are pupilary response corrected. 
    
    input_levels = np.linspace(0, 1, 100)
    
    # First, reverse the response curve 
    input_levels_corrected = reverse_perception_correction(input_levels)
    
    # The output levels should be a straight line -- %This is the 
    # correction applied by the projector 
    output_levels_corrected = perception_correction(input_levels_corrected)
    
    # Plot the corrected response curve
    plt.figure(figsize=(8, 6))
    plt.plot(input_levels, output_levels_corrected, label='corrected output', color='black')
    plt.plot(input_levels, input_levels_corrected, label='inversed input', color='black', alpha=0.5)
    plt.title('Corrected Pupilary Response Curve')
    plt.xlabel('Input Level')
    plt.ylabel('Output Level')
    plt.grid()
    plt.legend()
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.savefig('corrected_pupilary_response_curve.png')
    
    
    