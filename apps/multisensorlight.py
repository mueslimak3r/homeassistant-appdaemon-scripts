import hassapi as hass


"""
    Set the state of a set of lights from the state of multiple sensors.
    When the first sensor's state is 'on', the lights are set to the target brightness, and their prior state is saved for later
    When all of the sensors' states are 'off', the lights' prior state is restored. If no state has been stored, the lights are turned off.

    Args:
        sensors:
            - sensor.entity.id.1
            - sensor.entity.id.2
        lights:
            - light.entity.id.1
            - light.entity.id.2
        light_off_timeout: 30
        light_brightness: 100
    
    Release Notes
    Version 1.0:
        Initial Version
"""


class MultiSensorLightControl(hass.Hass):
    def initialize(self):
        self.set_namespace('hass')
        self.sensors = []
        self.lights = []
        self.states = {}
        self.log('initializing Multi Sensor Light Control')

        self.light_off_timeout = self.args['light_off_timeout'] if 'light_off_timeout' in self.args else 1
        self.target_brightness = self.args['light_brightness'] if 'light_brightness' in self.args else 100

        self.log("target brightness: {} sensor off trigger duration: {}".format(self.target_brightness, self.light_off_timeout))

        for sensor in self.args['sensors']:
            self.sensors.append(sensor)
            self.states[sensor] = self.get_state(sensor)
            self.log("listening to sensor: {} which has current state: {}".format(sensor, self.states[sensor]))

            self.listen_state(self.state_change, sensor, new='on')
            self.listen_state(self.state_change, sensor, new='off', duration=self.light_off_timeout)

        for light in self.args['lights']:
            self.lights.append(light)
        self.log("affected lights: {}".format(self.lights))

    def state_change(self, entity, attribute, old, new, kwargs):
        self.log("entity: {} new state: {} old state: {}".format(entity, new, old))       
        self.states[entity] = new
        
        all_off = False
        if new == 'off':
            all_off = True
            for sensor in self.sensors:
                if self.states[sensor] == 'on':
                    all_off = False
                    self.log("sensor: {} is still activated, lights will keep current state".format(sensor))

        if all_off == True:
            for light in self.lights:
                if light in self.states and self.states[light]['brightness'] is not None:
                    self.turn_on(light, brightness=self.states[light]['brightness'])
                else:
                    self.turn_off(light)

                if light in self.states:
                    del self.states[light]
            return
        elif new == 'on':
            for light in self.lights:
                if light not in self.states:
                    self.states[light] = {
                        'brightness': self.get_state(light, attribute="brightness")
                    }
                    self.log("saved state of light {}, brightness: {}".format(light, self.states[light]['brightness']))
                self.turn_on(light, brightness=self.target_brightness)