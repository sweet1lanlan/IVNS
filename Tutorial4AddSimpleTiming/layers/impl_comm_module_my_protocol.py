from components.base.ecu.software.abst_comm_layers import AbstractCommModule
from tools.general import RefList, General as G
from io_processing.surveillance_handler import MonitorInput, MonitorTags
from components.base.ecu.software.impl_physical_layers import StdPhysicalLayer
from components.base.ecu.software.impl_datalink_layers import StdDatalinkLayer
from components.base.ecu.software.impl_transport_layers import FakeSegmentTransportLayer,\
    SegmentTransportLayer
from tools.general import General as G
import uuid
from io_processing.surveillance_handler import MonitorInput, MonitorTags

class MyProtocolCommModule(AbstractCommModule):
    
    def __init__(self, sim_env, ecu_id):
        ''' Constructor
            
            Input:  ecu_id         string                   id of the corresponding AbstractECU
                    sim_env        simpy.Environment        environment of this component
            Output:  -
        '''
        AbstractCommModule.__init__(self, sim_env)

        # local parameters
        self._ecu_id = ecu_id
        self._jitter_in = 1
        self.monitor_list = RefList()
        
        # initialize
        self._init_layers(self.sim_env, self.MessageClass)
        
        # add tags
        self._tags = ["AUTH_SEND_TIME_BEFORE_ENCRYPTION", "AUTH_SEND_TIME_AFTER_ENCRYPTION", "AUTH_RECEIVE_TIME_BEFORE_DECRYPTION", "AUTH_RECEIVE_TIME_AFTER_DECRYPTION"]        
    
    def receive_msg(self):
        
        while True:
                        
            # receive from lower layer
            [message_id, message_data] = yield self.sim_env.process(self.transp_lay.receive_msg())        
        
            # receiver information    
            print("\n\nRECEIVER\nTime: "+str(self.sim_env.now)+"--Communication Layer: \nI am ECU " + self._ecu_id + "\nReceived message:\n - ID: " + str(message_id) +"\n - Content: " + message_data.get())
        
            # Assume it takes 0.5 seconds to e.g. decrypt this message
            uid = uuid.uuid4()
            # BEFORE PROCESSING
            print("\nECU "+ str(self._ecu_id) +"Time before message received: "+ str(self.sim_env.now))
            G().mon(self.monitor_list, MonitorInput([], "AUTH_RECEIVE_TIME_BEFORE_DECRYPTION", self._ecu_id, self.sim_env.now, 123, message_id, message_data.get(), message_data.padded_size, 432, uid))
            
            yield self.sim_env.timeout(0.5)
            
            # AFTER PROCESSING
            print("\nECU "+ str(self._ecu_id) +"Time after message received: "+ str(self.sim_env.now))            
            G().mon(self.monitor_list, MonitorInput([], "AUTH_RECEIVE_TIME_AFTER_DECRYPTION", self._ecu_id, self.sim_env.now, 123, message_id, message_data.get(), message_data.padded_size, 432, uid))
            
        # push to higher layer
        return [message_id, message_data]

    def send_msg(self, sender_id, message_id, message):
        # Sender information
        print("\n\nSENDER - \nTime: "+str(self.sim_env.now)+"--Communication Layer: \nI am ECU " + sender_id + "\nSending message:\n - ID: " + str(message_id)+"\n - Content: " + message.get())
                
        # Message to be send 
        print("\nSize of the message we want to send: "+ str(message.padded_size))
        print("\nContent of the message: "+ str(message.get()))
        
        # Assume it takes 0.2 seconds to e.g. encrypt this message
        uid = uuid.uuid4()
        # BEFORE PROCESSING
        print("\nECU "+ str(self._ecu_id) +"Time before message sent: "+ str(self.sim_env.now))
        G().mon(self.monitor_list, MonitorInput([], "AUTH_SEND_TIME_BEFORE_ENCRYPTION", self._ecu_id, self.sim_env.now, 123, message_id, message.get(), message.padded_size, 432, uid))
        
        yield self.sim_env.timeout(0.2)
        
        # AFTER PROCESSING
        G().mon(self.monitor_list, MonitorInput([], "AUTH_SEND_TIME_AFTER_ENCRYPTION", self._ecu_id, self.sim_env.now, 123, message_id, message.get(), message.padded_size, 432, uid))
        print("\nECU "+ str(self._ecu_id) +"Time after message sent: "+ str(self.sim_env.now))

        # Send message - here send your message with your message_id
        yield  self.sim_env.process(self.transp_lay.send_msg(sender_id, message_id, message))

            
    def _init_layers(self, sim_env, MessageClass):
        ''' Initializes the software layers 
            
            Input:  sim_env                        simpy.Environment        environment of this component                      
                    MessageClass                   AbstractBusMessage       class of the messages  how they are sent on the CAN Bus
            Output: -                   
        '''
        
        # create layers
        self.physical_lay = StdPhysicalLayer(sim_env)         
        self.datalink_lay = StdDatalinkLayer(sim_env) 
        self.transp_lay = SegmentTransportLayer(sim_env, MessageClass)
   
        # interconnect layers             
        self.datalink_lay.physical_lay = self.physical_lay        
        self.transp_lay.datalink_lay = self.datalink_lay           
        
        
    @property
    def ecu_id(self):
        return self._ecu_id
               
    @ecu_id.setter    
    def ecu_id(self, value):
        self._ecu_id = value          

    def monitor_update(self):
        ''' updates the monitor connected to this ecu
            
            Input:    -
            Output:   monitor_list    RefList    list of MonitorInputs
        '''
        # register Monitoring tags to track
        #G().register_eventline_tags(self._tags)
        
        items_1 = len(self.transp_lay.datalink_lay.controller.receive_buffer.items)
        items_2 = self.transp_lay.datalink_lay.transmit_buffer_size
        
        G().mon(self.monitor_list, MonitorInput(items_1, MonitorTags.BT_ECU_RECEIVE_BUFFER, self._ecu_id, self.sim_env.now))
        G().mon(self.monitor_list, MonitorInput(items_2, MonitorTags.BT_ECU_TRANSMIT_BUFFER, self._ecu_id, self.sim_env.now))
        
        self.monitor_list.clear_on_access()  # on the next access the list will be cleared        
        return self.monitor_list.get()

