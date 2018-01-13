## @ingroup Components-Energy-Networks
# Turbojet_Super.py
# 
# Created:  May 2015, T. MacDonald
# Modified: Aug 2017, E. Botero

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# suave imports
import SUAVE

from SUAVE.Core import Data, Units
from SUAVE.Components.Propulsors.Propulsor import Propulsor

# ----------------------------------------------------------------------
#  Turbojet Network
# ----------------------------------------------------------------------

## @ingroup Components-Energy-Networks
class Turbojet_Super(Propulsor):
    """ This is a turbojet for supersonic flight.

        Assumptions:
        None

        Source:
        Most of the componentes come from this book:
        https://web.stanford.edu/~cantwell/AA283_Course_Material/AA283_Course_Notes/
    """      

    def __defaults__(self):
        """ This sets the default values for the network to function.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        N/A
        """    	

        #setting the default values
        self.tag = 'Turbojet'
        self.number_of_engines = 1.0
        self.nacelle_diameter  = 1.0
        self.engine_length     = 1.0

    _component_root_map = None


    def evaluate_thrust(self,state):
        """ Calculate thrust given the current state of the vehicle

        	Assumptions:
        	None

        	Source:
        	N/A

        	Inputs:
        	state [state()]

        	Outputs:
        	results.thrust_force_vector [newtons]
        	results.vehicle_mass_rate   [kg/s]
        	conditions.propulsion.acoustic_outputs:
        	    core:
        		exit_static_temperature      
        		exit_static_pressure       
        		exit_stagnation_temperature 
        		exit_stagnation_pressure
        		exit_velocity 
        	    fan:
        		exit_static_temperature      
        		exit_static_pressure       
        		exit_stagnation_temperature 
        		exit_stagnation_pressure
        		exit_velocity 

        	Properties Used:
        	Defaulted values
            """  	

        #Unpack
        conditions = state.conditions

        ram                       = self.ram
        inlet_nozzle              = self.inlet_nozzle
        low_pressure_compressor   = self.low_pressure_compressor
        high_pressure_compressor  = self.high_pressure_compressor
        combustor                 = self.combustor
        high_pressure_turbine     = self.high_pressure_turbine
        low_pressure_turbine      = self.low_pressure_turbine
        core_nozzle               = self.core_nozzle
        thrust                    = self.thrust
        number_of_engines         = self.number_of_engines        

        #Creating the network by manually linking the different components

        #set the working fluid to determine the fluid properties
        ram.inputs.working_fluid                               = self.working_fluid

        #Flow through the ram , this computes the necessary flow quantities and stores it into conditions
        ram(conditions)

        #link inlet nozzle to ram 
        inlet_nozzle.inputs.stagnation_temperature             = ram.outputs.stagnation_temperature 
        inlet_nozzle.inputs.stagnation_pressure                = ram.outputs.stagnation_pressure

        #Flow through the inlet nozzle
        inlet_nozzle(conditions)

        #--link low pressure compressor to the inlet nozzle
        low_pressure_compressor.inputs.stagnation_temperature  = inlet_nozzle.outputs.stagnation_temperature
        low_pressure_compressor.inputs.stagnation_pressure     = inlet_nozzle.outputs.stagnation_pressure

        #Flow through the low pressure compressor
        low_pressure_compressor(conditions)

        #link the high pressure compressor to the low pressure compressor
        high_pressure_compressor.inputs.stagnation_temperature = low_pressure_compressor.outputs.stagnation_temperature
        high_pressure_compressor.inputs.stagnation_pressure    = low_pressure_compressor.outputs.stagnation_pressure

        #Flow through the high pressure compressor
        high_pressure_compressor(conditions)

        #link the combustor to the high pressure compressor
        combustor.inputs.stagnation_temperature                = high_pressure_compressor.outputs.stagnation_temperature
        combustor.inputs.stagnation_pressure                   = high_pressure_compressor.outputs.stagnation_pressure

        #flow through the high pressor comprresor
        combustor(conditions)

        #link the high pressure turbine to the combustor
        high_pressure_turbine.inputs.stagnation_temperature    = combustor.outputs.stagnation_temperature
        high_pressure_turbine.inputs.stagnation_pressure       = combustor.outputs.stagnation_pressure
        high_pressure_turbine.inputs.fuel_to_air_ratio         = combustor.outputs.fuel_to_air_ratio

        #link the high pressuer turbine to the high pressure compressor
        high_pressure_turbine.inputs.compressor                = high_pressure_compressor.outputs

        #flow through the high pressure turbine
        high_pressure_turbine(conditions)

        #link the low pressure turbine to the high pressure turbine
        low_pressure_turbine.inputs.stagnation_temperature     = high_pressure_turbine.outputs.stagnation_temperature
        low_pressure_turbine.inputs.stagnation_pressure        = high_pressure_turbine.outputs.stagnation_pressure

        #link the low pressure turbine to the low_pressure_compresor
        low_pressure_turbine.inputs.compressor                 = low_pressure_compressor.outputs

        #link the low pressure turbine to the combustor
        low_pressure_turbine.inputs.fuel_to_air_ratio          = combustor.outputs.fuel_to_air_ratio

        #get the bypass ratio from the thrust component
        low_pressure_turbine.inputs.bypass_ratio               = 0.0

        #flow through the low pressure turbine
        low_pressure_turbine(conditions)

        #link the core nozzle to the low pressure turbine
        core_nozzle.inputs.stagnation_temperature              = low_pressure_turbine.outputs.stagnation_temperature
        core_nozzle.inputs.stagnation_pressure                 = low_pressure_turbine.outputs.stagnation_pressure

        #flow through the core nozzle
        core_nozzle(conditions)

        # compute the thrust using the thrust component
        #link the thrust component to the core nozzle
        thrust.inputs.core_exit_velocity                       = core_nozzle.outputs.velocity
        thrust.inputs.core_area_ratio                          = core_nozzle.outputs.area_ratio
        thrust.inputs.core_nozzle                              = core_nozzle.outputs

        #link the thrust component to the combustor
        thrust.inputs.fuel_to_air_ratio                        = combustor.outputs.fuel_to_air_ratio

        #link the thrust component to the low pressure compressor 
        thrust.inputs.total_temperature_reference              = low_pressure_compressor.outputs.stagnation_temperature
        thrust.inputs.total_pressure_reference                 = low_pressure_compressor.outputs.stagnation_pressure
        thrust.inputs.number_of_engines                        = number_of_engines
        thrust.inputs.flow_through_core                        =  1.0 #scaled constant to turn on core thrust computation
        thrust.inputs.flow_through_fan                         =  0.0 #scaled constant to turn on fan thrust computation        

        #compute the thrust
        thrust(conditions)

        #getting the network outputs from the thrust outputs
        F            = thrust.outputs.thrust*[1,0,0]
        mdot         = thrust.outputs.fuel_flow_rate
        Isp          = thrust.outputs.specific_impulse
        output_power = thrust.outputs.power
        F_vec        = conditions.ones_row(3) * 0.0
        F_vec[:,0]   = F[:,0]
        F            = F_vec

        results = Data()
        results.thrust_force_vector = F
        results.vehicle_mass_rate   = mdot

        return results

    def size(self,state):  

        """ Size the turbofan

		Assumptions:
		None

		Source:
		N/A

		Inputs:
		State [state()]

		Outputs:
		None

		Properties Used:
		N/A
	    """             

        #Unpack components
        conditions = state.conditions
        thrust     = self.thrust
        thrust.size(conditions)

    __call__ = evaluate_thrust