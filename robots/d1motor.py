import socket
import time
from config.door_config import door_config 
from config.robots_config import robots_config
 

class D1Motor:
    def __init__(self, name, ip, port, id, status, shutdown, switchOn, enableOperation, stop, reset,  DInputs, role="generic", **kwargs):
        self.name = name
        self.ip = ip
        self.port = port
        self.robot_id = id.lower()
        self.id = id
        self.status = status
        self.status_array = bytearray(status)

        self.shutdown = shutdown
        self.shutdown_array = bytearray(shutdown)

        self.switchOn = switchOn
        self.switchOn_array = bytearray(switchOn)

        self.enableOperation = enableOperation
        self.enableOperation_array = bytearray(enableOperation)

        self.stop = stop
        self.stop_array = bytearray(stop)

        self.reset = reset
        self.reset_array = bytearray(reset)

        self.DInputs = DInputs
        
        self.DInputs_array = bytearray(DInputs)
        self.role = role
        self.current_position = None
        self.sock = None
        self.initialized = False


    # Variables start value
    start = 0
    ref_done = 0
    error = 0
    
    def connect(self):
        print(f"==============================")
        print(f"🛠️  Prepare motor: {self.robot_id.upper()}")
        print(f"==============================")
        print(f"🔌 Connecting to {self.ip}:{self.port}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.ip, self.port))
            print("♻️ Reiniciando motor, be sure that only this connection exists ")
            time.sleep(0.5)
            print("🔓 Activating control...")
            print("⚡ Enabling motor...")
            self.reference()
            print(f"✅ {self.robot_id.upper()}: Connected successfully")
        except ConnectionRefusedError as e:
            raise RuntimeError(f"❌ Failed to connect to {self.robot_id} ({self.ip}:{self.port}) → {e}")

    def reference(self):
        print(f"🌟 Referencing motor '{self.robot_id}'")
        self.homing()
        self.initialize()
        
    def initialize(self):
        if self.initialized:
            return
        self.set_mode(1)
        self.sendCommand(self.reset_array)
        self.set_shdn()
        self.set_swon()
        self.set_op_en()
            
        # self._send(self._cmd_set_mode(1))           
        # self._send(self._cmd_reset())
        # self._send(self._cmd_shutdown())
        # self._send(self._cmd_switch_on())
        # self._send(self._cmd_enable_op())
        self.initialized = True
        print(f"✅ Motor '{self.robot_id}' enabled")
    
    
    def homing(self):
        print(f"🌟 Starting homing for '{self.robot_id}'...")
        self.sendCommand(self.enableOperation_array)
        self.set_mode(6)
        self._send(self._cmd_feed_constant())
        self._send(self._cmd_set_revolution())
        self._send(self._cmd_speed())
        self._send(self._cmd_acceleration())
        self._send(self._cmd_start_homing())
        
        # self._send(self._cmd_enable_op())
        # self._send(self._cmd_set_mode(6))  # homing mode
        # self._send(self._cmd_start_homing())
        # self._send(self._cmd_feed_constant())
        # self._send(self._cmd_set_revolution())
        # self._send(self._cmd_speed())
        # self._send(self._cmd_acceleration())
        print("Estado: ")
        print(self._send(bytearray(self.status_array)))
        while (self._send(bytearray(self.status_array)) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
            and self._send(bytearray(self.status_array)) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
            and self._send(bytearray(self.status_array)) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
            and  self._send(bytearray(self.status_array)) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
                #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
                #If the StopButton is pushed the loop breaks
                if self._send(self.DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                    break
                time.sleep(0.1)
                print ("Homing")
        
        # ✔️ Update internal state and shared configuration
        self.current_position = 0.0
        door_config.DOOR_CLOSED_POS = 0.0
        print(f"✅ Homing completed → position set to {self.current_position}")
        print(f"🔁 door_config.DOOR_CLOSED_POS set to {door_config.DOOR_CLOSED_POS}")


    def move_to_open(self):
        # self._prepare_motion()
        self.set_mode(1)
        self.sendCommand(self.enableOperation_array)
        self._send_velocity_accel()
        self._send_target_positiona(250)  # mm
        self._start_motion()
        print("🚪 Motor moving to OPEN position")
        #Check Statusword for signal referenced and if an error in the D1 comes up
        while (self._send(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
            and self._send(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
                #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
                #If the StopButton is pushed the loop breaks
                if self._send(self.DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                    break
                time.sleep(0.1)
                print ("🚪 Motor moving to OPEN position")

    def move_to_closed(self):
        # self._prepare_motion()
        self.sendCommand(self.enableOperation_array)
        self._send_velocity_accel()
        self._send_target_positionb(250)
        self._start_motion()
        print("🚪 Motor moving to CLOSED position")
        # Check Statusword for signal referenced and if an error in the D1 comes up
        while (self._send(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
            and self._send(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
                #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
                #If the StopButton is pushed the loop breaks
                if self._send(self.DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                    break
                time.sleep(0.1)
                print ("Motor moving to CLOSED position")
        
    
    # def move_to(self, position):
    #     if self.sock is None:
    #         print(f"⚠️ D1Motor '{self.robot_id}' not connected, cannot move.")
    #         return
    #     self.current_position = position  
    #     try:
    #         self._send(self._cmd_set_mode(1))
    #         self._send(self._set_target_pos(position))
    #         self._send(self._start_motion())
    #         print(f"📍 Moving D1Motor '{self.robot_id}' to position {position}")
    #     except Exception as e:
    #         print(f"❌ Error moving motor {self.robot_id}: {e}")


    def _prepare_motion(self):
        self._send(self._cmd_enable_op())
        self._send(self._cmd_set_mode(1))  # Profile Position Mode

    def _send_velocity_accel(self):
        self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, 232, 3, 0, 0])) #speed
        self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 100, 0, 0, 0])) #acc
        print("⚙️ Velocidad y aceleración enviadas")

    def _send_target_positiona(self, pos_mm):
        val = int(pos_mm * 100)
        # bytes_ = [val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF, (val >> 24) & 0xFF]
        # self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4] + bytes_))
        print("Comando a pos a")
        self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 80, 70, 0, 0]))
    
    def _send_target_positionb(self, pos_mm):
        val = int(pos_mm * 100)
        # bytes_ = [val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF, (val >> 24) & 0xFF]
        # self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4] + bytes_))
        self._send(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 0, 0, 0, 0]))

    def _start_motion(self):
        self._send(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
        print("Go movement")
        time.sleep(1)

    def disable(self):
        print(f"⛔ Disable not implemented for D1Motor '{self.robot_id}'")

    def close(self):
        if self.sock:
            self.sock.close()
            print(f"🔐 Socket closed for motor '{self.robot_id}'")

    def _send(self, data):
        if not self.sock:
            raise Exception(f"❌ Motor '{self.robot_id}' is not connected.")
        self.sock.send(data)
        return list(self.sock.recv(24))
    
    def import_variables(self):
        # D1 motors do not import variables
        print(f"📥 D1Motor '{self.robot_id}': no variables to import (skipped)")

    def check_errors(self):
        # Puedes personalizar los telegramas de error si tienes un protocolo claro
        try:
            status = self._send(self._cmd_status())

            if status in [
                # Agrega todos los status que indican errores conocidos
                [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6],
                [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34],
            ]:
                print(f"❌ Motor '{self.robot_id}' reports error status: {status}")
                return True
        except Exception as e:
            print(f"⚠️ Could not check error for '{self.robot_id}': {e}")
        return False

    def rotate_full(self):
        """
        Rotates the motor 360 degrees from its current position.
        Resets to 0 if it exceeds 360.
        """
        print(f"🔄 Rotating motor '{self.robot_id}' one full turn (360°)...")
        
        # Estimamos que 360 grados corresponde a una posición de 360 mm (ajusta si necesitas otro valor)
        next_pos = (self.current_position or 0) + 360.0
        
        # Si pasa de 360, reseteamos a 0
        if next_pos >= 360:
            next_pos = 0.0
        
        self.move_to(next_pos)
        print(f"📍 New position for '{self.robot_id}': {next_pos} mm")

    
    # ======= Commands ========
    # def _cmd_reset(self):
    #     return bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1])

    # def _cmd_shutdown(self):
    #     return bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0])

    # def _cmd_switch_on(self):
    #     return bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0])

    # def _cmd_enable_op(self):
    #     return bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0])

    # def _cmd_set_mode(self, mode):
    #     return bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode])

    def _cmd_start_homing(self):
        return bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])
    
    def _cmd_feed_constant(self):
        return bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 160, 140, 0, 0])
    
    def _cmd_set_revolution(self):
        return bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0])
    
    def _cmd_speed(self):
        return bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 16, 39, 0, 0])
    
    def _cmd_acceleration(self):
        return bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, 16, 39, 0, 0])
    
    # def _cmd_status(self):
    #     return bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])
    
    def sendCommand(self, data):
        if not self.sock:
            raise Exception(f"❌ Motor '{self.robot_id}' is not connected.")
        self.sock.send(data)
        res = self.sock.recv(24)
        print(list(res))
        return list(res)

        
    #sending Shutdown Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
    def set_shdn(self):
        self.sendCommand(self.reset_array)
        self.sendCommand(self.shutdown_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 6]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 22]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 2]):
            print("wait for shdn")

            #1 Sekunde Verzoegerung
            #1 second delay
            time.sleep(1)

    #sending Switch on Disabled Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
    def set_swon(self):
        self.sendCommand(self.switchOn_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 6]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 22]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 2]):
            print("wait for sw on")

            time.sleep(1)
    #Operation Enable Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
    def set_op_en(self):
        self.sendCommand(self.enableOperation_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 6]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
            and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 2]):
            print("wait for op en")

            time.sleep(1)
    
    def set_mode(self, mode):
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
        print(f"🔄 Current mode before star moving: {mode}")
        while (self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) != 
            [0, 0, 0, 0, 0, 14, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1, mode]):
            print("wait for mode")
            time.sleep(0.1)
